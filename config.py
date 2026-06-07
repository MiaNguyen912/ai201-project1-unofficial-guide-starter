import os
from dotenv import load_dotenv

load_dotenv()

# --- Documents ---
DOCS_PATH_RAW = "./documents_raw_pdf"
DOCS_PATH_CLEAN = "./documents_clean_txt"

# --- Chunking and Retrieving---
MAX_CHUNK_SIZE = 500        # about 3-5 sentences
CHUNK_OVERLAP_WORDS = 10    # trailing words carried into the next sentence-chunk
MIN_CHUNK_SIZE = 50         # drop chunks shorter than this (whitespace/noise)
LONG_DOC_THRESHOLD = 6000   # docs >= this many chars use semantic chunking; smaller use sentence chunking
N_RESULTS = 20


# --- Embeddings and store ---
EMBEDDING_MODEL = "BAAI/bge-base-en-v1.5"  
CHROMA_COLLECTION = "uci-housing-dataset"
CHROMA_PATH = "./chromadb_uci_housing_dataset"

# --- LLM ---
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
LLM_MODEL = "llama-3.3-70b-versatile"  # see more at https://console.groq.com/docs/models
DISTANCE_THRESHOLD = 0.4  
