import os
import re
from config import (
    EMBEDDING_MODEL,
    CHUNK_SIZE,
    CHUNK_OVERLAP_WORDS,
    MIN_CHUNK_SIZE,
    LONG_DOC_THRESHOLD,
)


# Month names, full or abbreviated (e.g. "December" or "Dec")
_MONTHS = (
    r"Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|"
    r"Jul(?:y)?|Aug(?:ust)?|Sep(?:t(?:ember)?)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?"
)
# Word-format date, e.g. "DECEMBER 5, 2024" or "Oct 16, 2024"
_WORD_DATE = rf"(?:{_MONTHS})\.?\s+\d{{1,2}},?\s+\d{{4}}"
# Number-format date, e.g. "6/6/26" or "10/16/2024", optionally with a time ("6/6/26, 2:33 PM")
_NUMERIC_DATE = r"\d{1,2}/\d{1,2}/\d{2,4}(?:,?\s*\d{1,2}:\d{2}\s*[AP]M)?"
# Try word dates first, then numeric; re.search returns the leftmost match in the text.
_DATE_PATTERN = re.compile(rf"{_WORD_DATE}|{_NUMERIC_DATE}", re.IGNORECASE)


def find_first_date(text):
    """Return the first date string found anywhere in the text, or None."""
    match = _DATE_PATTERN.search(text)
    return match.group(0).strip() if match else None


def load_documents(DOCS_PATH):
    """Load all .txt rule documents from the docs folder and augment them with metadata."""
    documents = []
    for filename in sorted(os.listdir(DOCS_PATH)):
        if filename.endswith(".txt"):
            filepath = os.path.join(DOCS_PATH, filename)
            with open(filepath, "r", encoding="utf-8") as f:
                text = f.read()
            # site_name is the first word of the filename, up to the first "_"
            site_name = filename.split("_")[0]
            
            # created_date is the first date found in the document text
            created_date = find_first_date(text)

            documents.append({
                "filename": filename,
                "site": site_name,
                "created_date": created_date,
                "text": text,
            })
    print(f"Loaded {len(documents)} rule document(s): {[d['site'] for d in documents]}")
    return documents


# Split on sentence-ending punctuation followed by whitespace, or on line breaks.
# Reddit comments often lack terminal punctuation, so newlines act as boundaries too.
_SENTENCE_RE = re.compile(r"(?<=[.!?])\s+|\n+")

# Lazily-built LangChain SemanticChunker (loading the embedding model is expensive,
# so we only build it the first time a long document needs semantic chunking).
_semantic_chunker = None


def _slugify(name):
    """Turn a filename stem into a safe, unique chunk-id prefix."""
    return re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")


def _get_semantic_chunker():
    """Build (once) and return a LangChain SemanticChunker backed by the embedding model."""
    global _semantic_chunker
    if _semantic_chunker is None:
        from langchain_huggingface import HuggingFaceEmbeddings
        from langchain_experimental.text_splitter import SemanticChunker

        embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)
        # Split at the 90th-percentile of consecutive-sentence embedding distance:
        # i.e. cut where the topic shifts most sharply.
        _semantic_chunker = SemanticChunker(
            embeddings,
            breakpoint_threshold_type="percentile",
            breakpoint_threshold_amount=90,
        )
    return _semantic_chunker


def _semantic_split(text):
    """Topic-aware chunking for long, multi-paragraph guides/threads."""
    return _get_semantic_chunker().split_text(text)


def _sentence_split(text):
    """
    Sentence chunking for short comment/review docs.

    Greedily packs whole sentences into a chunk up to CHUNK_SIZE characters, then
    starts the next chunk with the last CHUNK_OVERLAP_WORDS words of the previous
    one so a fact spanning a boundary stays retrievable. Keeping sentences intact
    avoids cutting a short opinion in half.
    """
    sentences = [s.strip() for s in _SENTENCE_RE.split(text) if s.strip()]
    chunks = []
    current = []
    current_len = 0

    for sent in sentences:
        # Flush the current chunk before it would overflow, then seed the next
        # chunk with a trailing-word overlap from what we just emitted.
        if current and current_len + len(sent) + 1 > CHUNK_SIZE:
            chunks.append(" ".join(current))
            overlap = " ".join(chunks[-1].split()[-CHUNK_OVERLAP_WORDS:])
            current = [overlap] if overlap else []
            current_len = len(overlap)

        current.append(sent)
        current_len += len(sent) + 1

    if current:
        chunks.append(" ".join(current))
    return chunks


def chunk_document(doc_item):
    """
    Split one loaded document (a dict from load_documents) into embedding-ready chunks.

    Strategy is chosen per document by length:
      - text >= LONG_DOC_THRESHOLD chars  -> semantic chunking (using LangChain SemanticChunker)
      - shorter docs                      -> sentence chunking with word overlap

    Returns a list of dicts, each with the chunk text, a unique chunk_id, and
    source metadata (site, created_date, filename) carried through for attribution.

    """
    text = doc_item["text"]
    prefix = _slugify(os.path.splitext(doc_item["filename"])[0])

    if len(text) >= LONG_DOC_THRESHOLD:
        pieces = _semantic_split(text)
    else:
        pieces = _sentence_split(text)

    chunks = []
    counter = 0
    for piece in pieces:
        piece = piece.strip()
        if len(piece) < MIN_CHUNK_SIZE:        # drop whitespace/noise fragments
            continue
        chunks.append({
            "text": piece,
            "chunk_id": f"{prefix}_{counter}",
            "site": doc_item["site"],
            "created_date": doc_item["created_date"] or "unknown",
            "filename": doc_item["filename"],
        })
        counter += 1
    return chunks
