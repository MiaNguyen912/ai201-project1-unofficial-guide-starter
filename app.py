import os
import sys
from config import DOCS_PATH_RAW, DOCS_PATH_CLEAN


# sys.path.insert(0, "/Users/nguye/Library/Python/3.9/lib/python/site-packages")
# sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "helpers"))

from helpers.pdf_extract import extract_all_pdfs

if __name__ == "__main__":
    extracted = extract_all_pdfs(DOCS_PATH_RAW, DOCS_PATH_CLEAN)


    print(f"\nDone. Extracted text from {len(extracted)} PDF(s).")
    print("=" * 0)