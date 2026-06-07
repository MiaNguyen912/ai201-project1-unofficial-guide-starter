import chromadb
from chromadb.utils import embedding_functions
from torch import chunk
from config import CHROMA_COLLECTION, CHROMA_PATH, EMBEDDING_MODEL, N_RESULTS

# Embedding function and ChromaDB client are initialized once at module load.
# (If you need to re-ingest (e.g. after a config change), delete the `./chroma_db` folder first:
#   - rm -rf chroma_db/ 
#   - python app.py
# sentence-transformers downloads the model on first use — this may take
# 30–60 seconds the very first time. Subsequent runs use a local cache.
_ef = embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name=EMBEDDING_MODEL
)
_client = chromadb.PersistentClient(path=CHROMA_PATH)
_collection = _client.get_or_create_collection(
    name=CHROMA_COLLECTION,
    embedding_function=_ef,
    metadata={"hnsw:space": "cosine"},
)


def get_collection():
    """Return the ChromaDB collection. Used by app.py during ingestion."""
    return _collection


def embed_and_store(chunks):
    """
    Embed a list of chunks and store them in the vector database.

    Chunks come from chunk_document() in the ingestion pipeline; each is a dict
    with "text", "chunk_id", and source metadata ("site", "created_date",
    "filename"). _collection.add() takes three parallel lists:
      - documents : raw text strings — ChromaDB's embedding function converts
                    these to vectors automatically using bge-base-en-v1.5
                    (sentence-transformers), the model named in EMBEDDING_MODEL
      - metadatas : one dict per chunk, stored alongside the vector so that
                    retrieve() can surface which source each result came from
      - ids       : the unique chunk_id strings used to identify each entry

    You don't generate embeddings manually here — you hand over the text
    and ChromaDB handles the vector math.
    """
    _collection.add(
        documents=[c["text"] for c in chunks],
        metadatas=[
            {
                "site": c["site"],
                "created_date": c["created_date"],
                "filename": c["filename"],
                "chunk_id": c["chunk_id"],
            }
            for c in chunks
        ],
        ids=[c["chunk_id"] for c in chunks],
    )
    print(f"Stored {_collection.count()} total chunks in the vector database.")


def retrieve(query, n_results=N_RESULTS):
    """
    Find the most relevant chunks for a user's question via semantic search.

    Embeds the query with bge-base-en-v1.5 and runs a cosine-similarity, top-k
    search over the stored chunks (k = N_RESULTS = 10 per planning.md).

    _collection.query() takes:
      - query_texts : a list containing your query string
      - n_results   : how many results to return (top-k)
      - include     : ["documents", "metadatas", "distances"]

    Returns a list of dicts, each with the chunk text, its source information
    (site, created_date, filename) for attribution, and the cosine distance
    (lower = more similar). Results come back sorted by distance ascending.

    Note: _collection.query() returns nested lists (one per query). We only
    pass one query, so we index [0] to get the actual results.
    """
    if _collection.count() == 0:
        return []

    # Run semantic search via _collection.query()
    relevant_chunks = _collection.query( # type: dict of lists with keys "documents", "metadatas", "distances"
        query_texts=[query],
        n_results=n_results,
        include=["documents", "metadatas", "distances"]
    )

    # Extract results for this single query (index [0])
    documents = relevant_chunks["documents"][0]
    metadatas = relevant_chunks["metadatas"][0]
    distances = relevant_chunks["distances"][0]

    # Build return list: each item has text, source info, and distance
    print(f"Retrieved {len(documents)} relevant chunk(s) for query: '{query}'")
    retrieved_chunks = []
    for text, metadata, distance in zip(documents, metadatas, distances):
        retrieved_chunks.append({
            "text": text,
            "site": metadata["site"],
            "created_date": metadata["created_date"],
            "filename": metadata["filename"],
            "chunk_id": metadata["chunk_id"],
            "distance": distance,
        })
        # print(f"[{metadata['filename']} --- text: {text[:20]}...] (dist: {distance:.3f})")

        print("{\n\ttext: " + text)
        print("\tchunk_id: " + metadata["chunk_id"])
        print("\tsite: " + metadata["site"])
        print("\tcreated_date: " + metadata["created_date"])
        print("\tfilename: " + metadata["filename"])
        print("\tdistance: " + str(distance) + "\n}")
        print("-" * 50)
        
    print("\n" + "="*20 + " Done retrieving relevant chunks " + "=" * 20)


    # Results are already sorted by distance (ascending) from ChromaDB
    return retrieved_chunks



def test_retrieve(test_queries):
    """Test the retrieve() function with a list of queries."""
    for test_query in test_queries:
        test_results = retrieve(test_query)
        print(f"Test results for query: '{test_query}'\n")
        for chunk in test_results[:3]:  # Show top 3 results for brevity
            print(f"Text: {chunk['text']}")
            print(f"Site: {chunk['site']}")
            print(f"Created Date: {chunk['created_date']}")
            print(f"Filename: {chunk['filename']}")
            print(f"Distance: {chunk['distance']:.3f}")
            print("-" * 50)