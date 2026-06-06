"""
pdf_extract.py

Extracts and pre-processes text from all PDF files in the documents/ folder.
Each PDF is a browser-saved page (Reddit threads, blog posts, review sites),
so noise patterns include:
  - Browser/nav chrome: "Skip to main content", "Log in", "Sign up", site headers
  - Bare URLs printed at top of every browser-saved page
  - Reddit sidebar widgets: Discord links, schedule-of-classes links, stat blocks
  - Apartment/product ads injected into blog sidebars (e.g. Tripalink listings)
  - Pagination artifacts: "Page 1 of N", standalone numbers
"""

import os
import re
import sys
import logging
from typing import Optional
import pdfplumber

# Suppress noisy pdfminer font/color warnings (e.g. "Cannot set gray stroke
# color because /'P220' is an invalid float value"). These are harmless
# rendering artifacts in browser-saved PDFs and don't affect text extraction.
logging.getLogger("pdfminer").setLevel(logging.ERROR)

# ---------------------------------------------------------------------------
# Noise-filter helpers
# ---------------------------------------------------------------------------

# Patterns that indicate a line is pure UI chrome or a sidebar artifact.
# Each pattern is matched against a stripped, lowercased version of the line.
_NOISE_PATTERNS = [    
    # Reddit nav / sidebar chrome
    r"^skip to (main )?content",
    r"^(log ?in|sign ?up|create|search in r/)",
    r"^r/\w+\s*(•|\|)",                                            # "r/UCI •1y ago"
    r"^joined$",
    r"^\d+\.?\d*k?\s+(anteaters|members|online)",                  # stat blocks
    r"^(public|private|restricted)\s*$",
    r"^user flair\s*$",
    r"^about\s*$",
    r"^created\s+\w+\s+\d+,\s+\d{4}",                             # "Created Sep 24, 2009"
    r"^discord:\s*https?://",
    r"^(schedule of classes|register for classes)\s*:?$",
    r"^uci covid-?19 dashboard",

    # Generic nav / blog chrome
    r"^(home|help|earn|about|faqs?|login|search|menu|navigation)\s*$",
    r"^share\s+table of contents\s*$",
    r"^(en|fr|es)\s+renter tools",                                  # Tripalink locale switcher
    r"^top choices in uci area\s*$",

    # Apartment ad blocks (Tripalink sidebar)
    r"^\$[\d,]+\+?/mo\s*$",                                        # price lines
    r"^\d+\s+beds?\s+\d+(\.\d+)?\s+baths?",                       # "4 Beds 3.5 Baths"
    r"^(parking|private bathroom|utilities included)\s*$",
    r"^view all listings\s*$",
    r"^tripalink is here",

    # Pagination / standalone page numbers
    r"^page \d+ of \d+\s*$",
    r"^\d+\s*$",                                                    # lone digit(s)

    # Prked.com nav
    r"^(home|help|earn|log in|sign up)\s*$",
    r"^z\s+zack\s+\w+",                                            # author byline artifact

    # society19 / blog share widgets
    r"^(facebook|twitter|pinterest|instagram|tiktok|copy link)\s*$",
    r"^(written by|by)\s+\w+",
    r"^\(https?://",                                               # markdown-style link noise

    # ratemydorm widget noise
    r"^(overall|location|safety|value|cleanliness|facilities)\s*[\d.]+\s*$",
    r"^🎓",                                                        # ratemydorm AI promo emoji line
    r"^new to college\?",
    r"^(copy and go|ratemy\w+)\s*$",
    r"^\d+%\s+off\s+with\s+code",

    # Reddit nav that survives the earlier patterns
    r"^r/uci\s*(search|joined|•|\|)",
    r"^(search in r/|create)\s*$",
    r"^uc irvine\s*$",                                             # subreddit description title
    r"^a place for uci anteaters",
    r"^\d+\s+(share|comment|award)",
    r"^sort by:\s*(best|top|new|controversial)\s*$",
    r"^join the conversation\s*$",
]

_NOISE_RE = re.compile(
    "|".join(_NOISE_PATTERNS),
    flags=re.IGNORECASE,
)


def _is_noise(line: str) -> bool:
    """Return True if the line should be discarded as noise."""
    stripped = line.strip()
    if not stripped:
        return True
    if len(stripped) < 3:                      # single chars / stray punctuation
        return True
    if _NOISE_RE.match(stripped.lower()):
        return True
    return False


def _clean_text(raw: str) -> str:
    """
    Apply line-level noise filtering and light normalization to raw extracted text.

    Steps:
      1. Split into lines.
      2. Drop lines that match noise patterns.
      3. Collapse runs of 3+ blank lines down to 2 (preserve paragraph breaks).
      4. Strip leading/trailing whitespace from each surviving line.
    """
    lines = raw.splitlines()
    cleaned = []
    blank_run = 0

    for line in lines:
        if _is_noise(line):
            blank_run += 1 if not line.strip() else 0
            continue

        if not line.strip():
            blank_run += 1
            if blank_run <= 2:          # allow up to two consecutive blank lines
                cleaned.append("")
        else:
            blank_run = 0
            cleaned.append(line.strip())

    # Remove leading/trailing blank lines from the whole document
    while cleaned and not cleaned[0]:
        cleaned.pop(0)
    while cleaned and not cleaned[-1]:
        cleaned.pop()

    return "\n".join(cleaned)


# ---------------------------------------------------------------------------
# Column detection
# ---------------------------------------------------------------------------

def _detect_left_column_width(page, bucket_size: int = 25) -> Optional[float]:
    """
    Detect the right edge of the left content column by locating the left
    edge of a right-side density spike (i.e. the sidebar column).

    Returns the x-coordinate to crop at, or None if no clear two-column
    layout is detected (single-column page → use full width).

    Strategy:
      1. Bin word x0 positions into small buckets (25 pt default).
      2. Restrict search to the 35%–72% horizontal band — too far left is just
         indentation; too far right means there is no real sidebar.
      3. Inside that band, find the valley (minimum density bucket).
      4. Check that a density spike follows the valley on the right
         (i.e. right-column words restart). If yes, crop at the valley start.
      5. If the left column itself is nearly empty (page is mostly sidebar),
         still crop at the valley so we don't include sidebar-only pages.
    """
    words = page.extract_words()
    if not words:
        return None

    page_width   = page.width
    num_buckets  = int(page_width // bucket_size) + 1

    counts = [0] * num_buckets
    for w in words:
        b = int(w["x0"] // bucket_size)
        if b < num_buckets:
            counts[b] += 1

    lo = int(num_buckets * 0.35)   # don't crop before 35% of page width
    hi = int(num_buckets * 0.72)   # don't crop after 72% of page width

    search = counts[lo:hi]
    if not search:
        return None

    # Find the valley index (lowest density bucket in the search window)
    valley_offset = search.index(min(search))
    valley_idx    = lo + valley_offset

    # Confirm a density recovery to the right of the valley
    right_window  = counts[valley_idx + 1 : valley_idx + 5]
    right_peak    = max(right_window) if right_window else 0

    left_window   = counts[max(0, valley_idx - 4) : valley_idx]
    left_peak     = max(left_window) if left_window else 0

    # Only crop if:
    #  1. The valley is not right at the start of the search window.
    #     valley_offset == 0 means the gap is at the left margin of the search
    #     zone, which just indicates a left-margin indent before article text
    #     (e.g. centred blog layouts like campusobscura), not a column boundary.
    #     Requiring offset >= 2 ensures there is real left-column content before
    #     the gap, not just a narrow left margin.
    #  2. The right side has a meaningful density spike (real sidebar column).
    valley_count = counts[valley_idx]
    if (
        valley_offset >= 2
        and right_peak >= 4
        and right_peak >= 2 * (valley_count + 1)
    ):
        return valley_idx * bucket_size

    return None  # no convincing two-column split found


# ---------------------------------------------------------------------------
# Core extraction function
# ---------------------------------------------------------------------------

def _is_sidebar_only_page(page, threshold: float = 0.55) -> bool:
    """
    Return True if the overwhelming majority of words on this page start in
    the right portion (x0 > threshold * page_width). These are pages that
    contain only sidebar/ad content and no left-column article text.
    """
    words = page.extract_words()
    if not words:
        return False
    cutoff = page.width * threshold
    right_count = sum(1 for w in words if w["x0"] > cutoff)
    return right_count / len(words) >= 0.80


def _extract_page_text(page) -> str:
    """
    Extract text from a single pdfplumber Page:
      - If the page is sidebar-only (no left-column content), skip it.
      - If a two-column layout is detected, crop to the left column first.
      - Otherwise extract the full page.
    """
    if _is_sidebar_only_page(page):
        return ""
    crop_x = _detect_left_column_width(page)
    if crop_x is not None:
        page = page.crop((0, 0, crop_x, page.height))
    return page.extract_text() or ""


def extract_text_from_pdf(pdf_path: str) -> str:
    """
    Extract and clean text from a single PDF file.
    pdf_path: Absolute or relative path to a .pdf file.
    Returns: A cleaned string containing the document's text content,
             or an empty string if no text could be extracted.
    """
    with pdfplumber.open(pdf_path) as pdf:
        raw_pages = []
        for page in pdf.pages:
            page_text = _extract_page_text(page)
            if page_text:
                raw_pages.append(page_text)

    if not raw_pages:
        return ""

    raw = "\n\n".join(raw_pages)
    return _clean_text(raw)


# ---------------------------------------------------------------------------
# Batch processing
# ---------------------------------------------------------------------------

def extract_all_pdfs(input_docs_dir: str, output_docs_dir: str) -> dict[str, str]:
    """
    Extract text from every PDF in input_docs_dir and save each result as a
    .txt file in output_docs_dir.

    input_docs_dir:  Folder containing source PDF files.
    output_docs_dir: Folder where cleaned .txt files will be written.
                     Created automatically if it does not exist.
    Returns: A dict mapping pdf filename → cleaned text.
    """
    os.makedirs(output_docs_dir, exist_ok=True)

    results = {}
    pdf_files = sorted(f for f in os.listdir(input_docs_dir) if f.lower().endswith(".pdf"))

    if not pdf_files:
        print(f"No PDF files found in '{input_docs_dir}/'.")
        return results

    for fname in pdf_files:
        input_path = os.path.join(input_docs_dir, fname)
        print(f"Extracting: {fname} ...", end=" ")
        try:
            text = extract_text_from_pdf(input_path)
            results[fname] = text
            word_count = len(text.split())

            # Save cleaned text to output folder with the same stem + .txt
            txt_fname = os.path.splitext(fname)[0] + ".txt"
            output_path = os.path.join(output_docs_dir, txt_fname)
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(text)

            print(f"({word_count} words)")
        except Exception as e:
            print(f"ERROR — {e}")
            results[fname] = ""

    return results

