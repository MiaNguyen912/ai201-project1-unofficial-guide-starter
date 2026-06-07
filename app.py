import os
import sys
import time
from config import DOCS_PATH_RAW, DOCS_PATH_CLEAN
from helpers.embed_and_retrieve import embed_and_store
from helpers.ingest_and_chunk import load_documents, chunk_document
from helpers.pdf_extract import extract_all_pdfs
from helpers.embed_and_retrieve import embed_and_store, retrieve, get_collection, test_retrieve

test_queries = [
    "Which dorms are quieter or more social, and which suit freshmen vs upperclassmen?",
    "What hidden costs should I expect besides housing rates?",
    "Is the UCI housing lottery actually random, or are there patterns students report?",
    "how is the safety level at Middle Earth?",
    "how is the living cost for off‑campus complexes near UCI compared to on‑campus dorm options?",
]

if __name__ == "__main__":
    # ---- Check if the vector store is already populated to avoid redundant ingestion ----
    collection = get_collection()
    if collection.count() > 0:
        print(f"Vector store already populated ({collection.count()} chunks). Skipping ingestion.")
        print("To re-ingest, delete the ./chromadb_uci_housing_dataset folder and restart.")
        print("=" * 50)
    
    else:
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
        
        # ------ embed the chunks and store them in the vector database (ChromaDB) -------
        if all_chunks:
            embed_and_store(all_chunks)
            print(f"Ingestion complete. {len(all_chunks)} chunks stored.")
            print("=" * 50)
        else:
            print("No chunks to embed and store. Please check the previous steps for issues.")
            
            
            
    # ------ (Optional) Retrieve test -------
    print("\nTesting retrieval with sample queries:")
    test_retrieve(test_queries)
    print("\nFinished testing retrieval.")
    print("=" * 50)