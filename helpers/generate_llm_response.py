from groq import Groq
from config import GROQ_API_KEY, LLM_MODEL, DISTANCE_THRESHOLD

_client = Groq(api_key=GROQ_API_KEY)


def generate_response(query, retrieved_chunks):
    """
    Generate a grounded answer from retrieved rule chunks.
    Return the response as a string
    """
    
    # Filter low-relevance chunks
    relevant_chunks = [c for c in retrieved_chunks if c.get("distance", 1.0) <= DISTANCE_THRESHOLD]
    if not relevant_chunks:
      return "I couldn't find anything relevant in my knowledge base. Please try rephrasing your question or check that your ingestion pipeline is working."
    
    # Build the context blocks separated by delimiters. Include ChunkID if present.
    context_blocks = []
    for c in relevant_chunks:
      context_blocks.append(
        "---\n"
        f"Site: {c.get('site')} | Created date: {c.get('created_date')} | file name: {c.get('filename')} | Distance: {c.get('distance', 0):.4f}\n"
        "Text: " + c.get("text", "") + "\n"
      )
    context_text = "\n".join(context_blocks)

    # System prompt — grounding instruction (strict)
    system_prompt = (
      "Answer using only the retrieved rule text below; do not use outside knowledge or guess. "
      "Do not fabricate, infer, or add information not present in the context. "
      "If the text does not contain the answer, reply exactly: I don't know - the answer is not found in the provided rule text. "
      "If multiple chunks conflict or are ambiguous, state that the rules are ambiguous and list the relevant citations. "
      "Cite sources using the format: [sources: <file_name> - <created_date>, ...] or [sources: <file_name>, ...] if <created_date> is not available. Keep answers concise and quote verbatim only when explicitly quoting."
    )

    # User prompt: include the context and the user's question
    user_prompt = (
      "CONTEXT:\n" + context_text + "\n"
      "QUESTION: " + query + "\n\n"
      "Using only the context above, answer the question concisely and include citation(s) in the stated format. "
      "If the answer is not present, reply exactly: I couldn't find anything relevant in my knowledge base."
    )

    # Call the Groq client.
    try:
      response = _client.chat.completions.create(messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}], model=LLM_MODEL, max_tokens=512)
      return response.choices[0].message.content.strip()
    except Exception:
      return "Exception occurred while generating response. "
        
