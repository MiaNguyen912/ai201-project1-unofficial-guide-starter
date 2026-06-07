import os
import sys
import time
import gradio as gr
from config import DOCS_PATH_RAW, DOCS_PATH_CLEAN, DISTANCE_THRESHOLD
from helpers.embed_and_retrieve import embed_and_store
from helpers.ingest_and_chunk import load_documents, chunk_document
from helpers.pdf_extract import extract_all_pdfs
from helpers.embed_and_retrieve import embed_and_store, retrieve, get_collection, test_retrieve
from helpers.generate_llm_response import generate_response

test_queries = [
    "Which dorms are quieter or more social, and which suit freshmen vs upperclassmen?",
    "What hidden costs should I expect besides housing rates?",
    "Is the UCI housing lottery actually random, or are there patterns students report?",
    "how is the safety level at Middle Earth?",
    "how is the living cost for off‑campus complexes near UCI compared to on‑campus dorm options?",
]
def run_ingestion_pipeline():
    # ------- extract text from all PDFs in DOCS_PATH_RAW directory and save to DOCS_PATH_CLEAN -------
    extracted = extract_all_pdfs(DOCS_PATH_RAW, DOCS_PATH_CLEAN)
    print(f"\nDone. Extracted text from {len(extracted)} PDF(s).")
    print("=" * 0)
    
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
    # for chunk in all_chunks:
        # print(f"Chunk ID: {chunk['chunk_id']}")
        # print(f"Site: {chunk['site']}")
        # print(f"Created Date: {chunk['created_date']}")
        # print(f"Filename: {chunk['filename']}")
        # print(f"Text: {chunk['text']}\n")
        # print("-" * 50)
    print(f"\nDone. Created {len(all_chunks)} chunks from {len(documents)} document(s).")
    print("=" * 50)
    
    # ------ embed the chunks and store them in the vector database (ChromaDB) -------
    if all_chunks:
        embed_and_store(all_chunks)
        print(f"Ingestion complete. {len(all_chunks)} chunks stored.")
        print("=" * 50)
    else:
        print("No chunks to embed and store. Please check the previous steps for issues.")

# Dark-gray glassmorphism base with blue (primary) + yellow (accent) — Gradio 6 applies these at launch().
# Panels use translucent fills here; the frosted blur/borders/gradient live in UI_CSS below.
UI_THEME = gr.themes.Base(
    primary_hue="blue",
    secondary_hue="yellow",
    neutral_hue="gray",
    font=[gr.themes.GoogleFont("Inter"), "system-ui", "sans-serif"],
).set(
    body_background_fill="#1b1f27",
    body_background_fill_dark="#1b1f27",
    block_background_fill="rgba(255, 255, 255, 0.06)",
    block_background_fill_dark="rgba(255, 255, 255, 0.06)",
    block_border_width="1px",
    block_border_color="rgba(255, 255, 255, 0.12)",
    block_radius="18px",
    block_shadow="0 8px 32px rgba(0, 0, 0, 0.30)",
    block_label_text_color="#facc15",
    block_title_text_color="#facc15",
    body_text_color="#e5e7eb",
    body_text_color_dark="#e5e7eb",
    input_background_fill="rgba(255, 255, 255, 0.05)",
    input_background_fill_dark="rgba(255, 255, 255, 0.05)",
    input_border_color="rgba(255, 255, 255, 0.14)",
    input_radius="14px",
    button_primary_background_fill="#2563eb",
    button_primary_background_fill_hover="#1d4ed8",
    button_primary_text_color="#ffffff",
    button_large_radius="14px",
    button_small_radius="14px",
)
UI_CSS = """
/* Dark-gray backdrop with a subtle blue tint for the frosted panels to sit on */
.gradio-container {
    max-width: 900px !important;
    margin: auto !important;
    background:
        radial-gradient(1200px 600px at 15% -10%, rgba(37, 99, 235, 0.18), transparent 60%),
        radial-gradient(1000px 500px at 110% 10%, rgba(250, 204, 21, 0.08), transparent 55%),
        #1b1f27 !important;
}

/* Frosted glass on every panel/component */
.gradio-container .block,
.gradio-container .form,
.gradio-container .gr-box,
.gradio-container .gr-panel {
    backdrop-filter: blur(16px) saturate(140%) !important;
    -webkit-backdrop-filter: blur(16px) saturate(140%) !important;
    border: 1px solid rgba(255, 255, 255, 0.12) !important;
    border-radius: 18px !important;
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.30) !important;
}

/* Inputs / chat as lighter frosted glass */
.gradio-container textarea,
.gradio-container input[type="text"],
.gradio-container .chatbot,
.gradio-container .message {
    background: rgba(255, 255, 255, 0.05) !important;
    backdrop-filter: blur(10px) !important;
    -webkit-backdrop-filter: blur(10px) !important;
}

/* Glassy primary button with a soft glow */
.gradio-container button.primary,
.gradio-container .primary {
    background: linear-gradient(135deg, rgba(37, 99, 235, 0.95), rgba(29, 78, 216, 0.95)) !important;
    border: 1px solid rgba(255, 255, 255, 0.18) !important;
    box-shadow: 0 4px 18px rgba(37, 99, 235, 0.45) !important;
    backdrop-filter: blur(8px) !important;
}

#app-title { color: #facc15; text-align: center; margin-bottom: 0; font-weight: 700; letter-spacing: 0.2px; }
#app-subtitle { color: #93c5fd; text-align: center; margin-top: 4px; margin-bottom: 8px; }
"""

with gr.Blocks(title="UCI Housing Guide") as UI:
    gr.Markdown("<h1 id='app-title'>🏠 The Unofficial UCI Housing Guide</h1>")
    gr.Markdown(
        "<p id='app-subtitle'>Ask about UCI dorms &amp; off-campus housing — "
        "answers grounded in real student reviews.</p>"
    )

    chatbot = gr.Chatbot(label="Conversation", height=440)
    with gr.Row():
        inp = gr.Textbox(
            placeholder="e.g. Which dorms are quieter, Mesa Court or Middle Earth?",
            show_label=False,
            container=False,
            scale=8,
        )
        btn = gr.Button("Ask", variant="primary", scale=1)

    gr.Examples(examples=test_queries, inputs=inp, label="Try one of these")

    def respond(query, history):
        """Submit handler: run the query through generate_response() and append to the chat."""
        if not query or not query.strip():
            return history, ""
        answer = generate_response(query, retrieve(query))
        history = (history or []) + [
            {"role": "user", "content": query},
            {"role": "assistant", "content": answer},
        ]
        return history, ""

    btn.click(respond, inputs=[inp, chatbot], outputs=[chatbot, inp])
    inp.submit(respond, inputs=[inp, chatbot], outputs=[chatbot, inp])




if __name__ == "__main__":
    # ---- Check if the vector store is already populated to avoid redundant ingestion ----
    collection = get_collection()
    if collection.count() > 0:
        print(f"Vector store already populated ({collection.count()} chunks). Skipping ingestion.")
        print("To re-ingest, delete the ./chromadb_uci_housing_dataset folder and restart.")
        print("=" * 50)
    else:
        # ------ Run the full ingestion pipeline: extract, ingest with metadata, chunk, and embed/store -------
        run_ingestion_pipeline()
            
    # ------ (Optional) Retrieve test -------
    # print("\nTesting retrieval with sample queries:")
    # test_retrieve(test_queries)
    # print("\nFinished testing retrieval.")
    # print("=" * 50)
    
    # ------ build an interface for users to input queries and wire up LLM to generate responses -------
    # while True:
    #     user_query = input("\nAsk a question about UCI housing: ")
    #     answer = generate_response(user_query, retrieve(user_query))
    #     print(f"Answer: {answer}")  
    UI.launch(theme=UI_THEME, css=UI_CSS)

