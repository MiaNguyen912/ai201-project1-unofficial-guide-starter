import os
import sys
import time
from config import DOCS_PATH_RAW, DOCS_PATH_CLEAN
from helpers.ingest import load_documents, chunk_document


# sys.path.insert(0, "/Users/nguye/Library/Python/3.9/lib/python/site-packages")
# sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "helpers"))

from helpers.pdf_extract import extract_all_pdfs

if __name__ == "__main__":
    # ------- extract text from all PDFs in DOCS_PATH_RAW directory and save to DOCS_PATH_CLEAN -------
    # extracted = extract_all_pdfs(DOCS_PATH_RAW, DOCS_PATH_CLEAN)
    # print(f"\nDone. Extracted text from {len(extracted)} PDF(s).")
    # print("=" * 0)
    
    # ------- ingest the .txt files and augmented them with metadata (e.g., filename, date, etc.) --------
    documents = load_documents(DOCS_PATH_CLEAN)
    # for doc in documents:
    #     print(f"Document: {doc['filename']}")
    #     print(f"Site: {doc['site']}")
    #     print(f"Created Date: {doc['created_date']}")
    #     print(f"Text Preview: {doc['text'][:50]}...")
    #     print("-" * 50)
    print(f"\nDone. Loaded {len(documents)} document(s) with metadata.")
    print("=" * 50)
    
    # ------- chunk the documents into embedding-ready pieces with source metadata carried through -------
    all_chunks = []
    for doc in documents:
        start_time = time.time()
        chunks = chunk_document(doc)
        end_time = time.time()
        all_chunks.extend(chunks)
        print(f"Document '{doc['filename']}' chunked into {len(chunks)} pieces after {end_time - start_time:.2f} seconds.")
    # print(f"Sample chunks from the first document:")
    # for chunk in all_chunks[:5]:
    #     print(f"Chunk ID: {chunk['chunk_id']}")
    #     print(f"Site: {chunk['site']}")
    #     print(f"Created Date: {chunk['created_date']}")
    #     print(f"Filename: {chunk['filename']}")
    #     print(f"Text: {chunk['text']}...")
    #     print("-" * 50)
    print(f"\nDone. Created {len(all_chunks)} chunks from {len(documents)} document(s).")
    print("=" * 50)
    
    if all_chunks:
        # embed_and_store(all_chunks)
        print(f"Ingestion complete. {len(all_chunks)} chunks stored.")
    
    
    
    