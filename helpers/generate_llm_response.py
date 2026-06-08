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
    
    # Build compact, citation-ready context blocks. The header doubles as the exact
    # citation tag the model should reuse; distance/site are omitted as the model
    # doesn't need them and they only burn tokens.
    context_blocks = []
    for c in relevant_chunks:
      date = c.get("created_date") or "n/a"
      context_blocks.append(
        f"[{c.get('filename')} - {date}]\n" + c.get("text", "")
      )
    context_text = "\n\n".join(context_blocks)

    # System prompt — all behavior lives here (grounding, refusal, citations).
    # system_prompt = (
    #   "You answer questions about UC Irvine housing using ONLY the sources in CONTEXT. Do not use outside knowledge, infer, guess, or add information not present in the context."
    #   "If the text does not contain the answer, reply exactly: `I couldn't find anything relevant in my knowledge base.` and finish your response without citations."
    #   "You may summarize and combine what the sources say. If multiple chunks conflict or are ambiguous, state that the rules are ambiguous and list the relevant citations"
    #   "Be concise. End your answer with a list of citation of the source headers you used, each item should be in format: - <file_name>"
    # )

    # # User prompt: just the data — context and the question.
    # user_prompt = "CONTEXT:\n" + context_text + "\n\nQUESTION: " + query
    
    system_prompt = (
      "Answer using only the retrieved rule text below; do not use outside knowledge or guess. "
      "Do not fabricate, infer, or add information not present in the context. "
      "If the text does not contain the answer, reply exactly:`I don't know - the answer is not found in the provided rule text.` and finish your response without citations. "
      "If multiple chunks conflict or are ambiguous, state that the rules are ambiguous and list the relevant citations. "
      "Cite sources using the format: [sources: <file_name>, ...]. Keep answers concise and quote verbatim only when explicitly quoting."
      # "Only if the text does contain the answer, end your answer with a list of citation of the sources you used, each item should be in format: - <file_name>. Keep answers concise and quote verbatim only when explicitly quoting."
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
    except Exception as e:
      return "Exception occurred while generating response: " + str(e)
        
