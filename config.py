import os
from dotenv import load_dotenv

load_dotenv()

# --- Chunking ---
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200
MIN_CHUNK_SIZE = 50


# --- LLM ---
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
LLM_MODEL = "llama-3.3-70b-versatile"

# --- Embeddings ---
EMBEDDING_MODEL = "bge-base-en-v1.5"

# --- Vector store ---
CHROMA_COLLECTION = "uci-housing-dataset"
CHROMA_PATH = "./chromadb_uci_housing_dataset"

# --- Retrieval ---
N_RESULTS = 10

# --- Documents ---
DOCS_PATH_RAW = "./documents_raw_pdf"
DOCS_PATH_CLEAN = "./documents_clean_txt"
