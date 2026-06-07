import os
from dotenv import load_dotenv

load_dotenv()

# --- Chunking ---
CHUNK_SIZE = 1000           # target max chars per fixed/sentence chunk (short docs)
CHUNK_OVERLAP_WORDS = 10    # trailing words carried into the next sentence-chunk
MIN_CHUNK_SIZE = 50         # drop chunks shorter than this (whitespace/noise)
LONG_DOC_THRESHOLD = 6000   # docs >= this many chars use semantic chunking; smaller use sentence chunking


# --- LLM ---
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
LLM_MODEL = "llama-3.3-70b-versatile"

# --- Embeddings ---
EMBEDDING_MODEL = "BAAI/bge-base-en-v1.5"   # full HuggingFace repo id (loadable by sentence-transformers / langchain)

# --- Vector store ---
CHROMA_COLLECTION = "uci-housing-dataset"
CHROMA_PATH = "./chromadb_uci_housing_dataset"

# --- Retrieval ---
N_RESULTS = 10

# --- Documents ---
DOCS_PATH_RAW = "./documents_raw_pdf"
DOCS_PATH_CLEAN = "./documents_clean_txt"
