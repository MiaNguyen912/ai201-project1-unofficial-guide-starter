# The Unofficial Guide — Project 1

> **How to use this template:**
> Complete each section *after* you've built and tested the corresponding part of your system.
> Do not write placeholder text — if a section isn't done yet, leave it blank and come back.
> Every section below is required for submission. One-liners will not receive full credit.

---

## Getting Started

### 1. Fork and clone

Fork this repo, then clone your fork locally.

### 2. Create a virtual environment

```bash
python -m venv .venv
source .venv/bin/activate      # Mac/Linux
# or: .venv\Scripts\activate   # Windows
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

> **Note:** on first run, `sentence-transformers` downloads the embedding model
> `BAAI/bge-base-en-v1.5` (~440MB). The same model also backs LangChain's
> `SemanticChunker` during ingestion. This download only happens once — it's
> cached locally afterward.

### 4. Add your Groq API key

```bash
cp .env.example .env
```

Open `.env` and replace `your_key_here` with your key from [console.groq.com](https://console.groq.com). No credit card required.

### 5. (optional) clear the stale chromadb store to re-ingest docs after chunking configuration changes

ChromaDB persists to disk in `./chromadb_uci_housing_dataset`. If you change your chunking strategy and want to re-ingest, delete that folder and restart the app:
 
``` bash
rm -rf chromadb_uci_housing_dataset/
```

### 6. Run the app
Run the app using the command below, then open http://localhost:7860 to access it
```bash
python app.py
```

---

## Domain

<!-- What topic or category of knowledge does your system cover?
     Why is this knowledge valuable, and why is it hard to find through official channels? -->

**Housing and dorms at UC Irvine.** The system answers practical questions
incoming and continuing students actually ask, such as:

- Which dorms are quiet versus social, and which suit freshmen vs. upperclassmen?
- What hidden costs should I expect besides the published housing rates?
- Is the UCI housing lottery actually random, or are there patterns students report?
- How safe is a given dorm (e.g., Middle Earth)?
- How do off-campus complexes near UCI compare in cost to on-campus dorms?

This knowledge is valuable because it comes from students' lived experience —
lottery behavior, waitlist tactics, roommate fit, maintenance responsiveness,
hidden costs, and move-in logistics. Official UCI housing pages list rules and
rates but rarely capture the timing tricks, social dynamics, and real-world
problems that students rely on when choosing where to live.

---

## Document Sources

<!-- List every source you collected documents from. -->

All sources were saved as browser-printed PDFs in `documents_raw_pdf/`, then
extracted and cleaned into plain text in `documents_clean_txt/`.
spanning forum discussion, crowd-sourced reviews, and editorial blogs:

| # | Source | Type | URL or file path |
|---|--------|------|-----------------|
| 1 | Reddit - r/UCI — "Housing" | Reddit thread | https://www.reddit.com/r/UCI/comments/1b40x2f/housing/ |
| 2 | RateMyDorm — UC Irvine Dorms Ranked | Crowd-sourced review site | https://www.ratemydorm.com/dorms-ranked/university-of-california-irvine |
| 3 | Campus Obscura | WordPress blog | https://campusobscura.wordpress.com/2024/06/11/the-best-and-worst-of-ucis-undergrad-on-campus-housing/ |
| 4 | Reddit - r/UCI — "Dorms" | Reddit thread | https://www.reddit.com/r/UCI/comments/1ruj1dt/dorms/ |
| 5 | Reddit - r/UCI — "first year housing scoop" | Reddit thread | https://www.reddit.com/r/UCI/comments/1jckpkn/first_year_housing_scoop/ |
| 6 | Society19 — Ultimate Ranking of UCI Dorms | Editorial blog | https://www.society19.com/ultimate-ranking-uci-dorms/ |
| 7 | Prked — Deciphering the Dorms | Editorial blog | https://prked.com/post/deciphering-the-dorms-an-insiders-guide-to-the-best-housing-at-uc-irvine |
| 8 | Tripalink — Dorms vs. Off-Campus Housing | Editorial blog | https://tripalink.com/blog/uc-irvine:-dorms-vs.-off-campus-housing |
| 9 | Reddit - r/UCI — "Dorm recommendations and application tips" | Reddit thread | https://www.reddit.com/r/UCI/comments/1t00phj/dorm_recommendations_and_application_tips_for/ |
| 10 | Reddit - r/UCI — "Where to look for housing" | Reddit thread | https://www.reddit.com/r/UCI/comments/1luxaac/where_to_look_for_housing/ |
| 11 | Reddit - r/UCI — "housing recs for second yr" | Reddit thread | https://www.reddit.com/r/UCI/comments/1oa9vmh/housing_recs_for_second_yr/ |

---

## Chunking Strategy

<!-- Describe your chunking approach with enough specificity that someone else could reproduce it. -->

The corpus mixes two different document shapes (short comments vs. long article), so a single fixed chunk
size won't fit any case. Therefore, each document is routed by length to one of the following two strategies:

- **Long guides and large comment threads (>= 6000 chars) → semantic chunking.**
  LangChain's `SemanticChunker` (backed by the same `bge-base-en-v1.5` model)
  embeds each sentence and cuts where consecutive-sentence similarity drops most
  sharply (90th-percentile breakpoint). This keeps multi-topic guides split
  along topic boundaries instead of arbitrary character counts.
- **Short Reddit comment/Q&A docs (< 6000 chars) → sentence chunking.** Whole 3-5
  sentences are packed into a single chunk, up to  `MAX_CHUNK_SIZE = 500` characters (while `MIN_CHUNK_SIZE = 50`), then the
  next chunk is seeded with the last `CHUNK_OVERLAP_WORDS = 10` words of the
  previous one. Keeping sentences intact avoids cutting a short opinion in half.

**Chunk size:** target max **500 characters** per chunk for the sentence
strategy; semantic chunks are variable-length (decided by topic shifts).

**Overlap:** **10 words** carried between sentence chunks. (Semantic chunks rely
on topic boundaries rather than fixed overlap.)

**Why these choices fit your documents:** short reviews state one opinion per
sentence — too-small chunks would scatter a single judgment; too-large chunks
would blend multiple dorms. The 10-word overlap keeps a fact that straddles a
boundary retrievable. Long guides cover many subtopics, so topic-aware semantic
splits keep related details together. A final `MIN_CHUNK_SIZE = 50` filter drops
whitespace/noise fragments from both strategies.

**Preprocessing before chunking:** PDFs are extracted with `pdfplumber`
(`helpers/pdf_extract.py`), which (1) detects and drops right-side sidebar
columns of related-post links on Reddit pages so left/right text doesn't
interleave, (2) strips nav chrome, ads, share widgets, and pagination via
line-level noise patterns, and (3) removes the browser print header
(`<date>, <time> <title>`) repeated on every page. Ingestion
(`helpers/ingest_and_chunk.py`) then augments each cleaned doc with metadata:
`site` (first token of the filename), `created_date` (first date found in the
text), and `filename`.

**Final chunk count:** **161 chunks** across the 11 documents.

---

## Embedding Model

<!-- Name the embedding model you used and explain your choice. -->

**Model used:** `BAAI/bge-base-en-v1.5` via `sentence-transformers`, stored in
ChromaDB with cosine similarity (`hnsw:space: cosine`). Retrieval returns the
**top-k = 20** nearest chunks per query.

**Production tradeoff reflection:** a lighter model (e.g., `all-MiniLM-L6-v2`)
would use less memory and be faster, and is likely sufficient for a small corpus.
I chose the stronger `bge-base-en-v1.5` because the content is subjective,
opinion-heavy student text where exact keywords rarely match the query, so
better semantic matching matters more than latency here. If deploying for real
users with no cost constraint, I'd weigh: context length (bge-base caps at 512
tokens, which interacts with chunk size), multilingual needs (bge-base is
English-only), accuracy on domain-specific slang ("Middle", "ME", "classics"),
and local vs. API-hosted latency. Choosing k is also a tradeoff: higher k gives
richer context but adds noise that can dilute the answer; k=10 plus a distance
filter at generation time balances coverage against focus.

---

## Grounded Generation

<!-- Explain how your system enforces grounding. -->

Grounding is enforced at two layers (`helpers/generate_llm_response.py`), using
the Groq-hosted `llama-3.3-70b-versatile` model.

**Structural filter (before the prompt):** retrieved chunks are filtered by
`DISTANCE_THRESHOLD = 0.4` (cosine distance). If no chunk is close enough, the
system returns a canned "I couldn't find anything relevant in my knowledge base"
message and never calls the LLM — this is what stops off-topic queries (e.g.,
"Is the weather good today?") from being answered at all. The
surviving chunks are formatted into a delimited context block, each labeled with
its `site`, `created_date`, `filename`, and distance.

**System prompt grounding instruction:**
``` 
Answer using only the retrieved rule text below; do not use outside knowledge or guess. 
Do not fabricate, infer, or add information not present in the context. 
If the text does not contain the answer, reply exactly:`I don't know - the answer is not found in the provided rule text.` and finish your response without citations. 
If multiple chunks conflict or are ambiguous, state that the rules are ambiguous and list the relevant citations. 
Cite sources using the format: [sources: <file_name>, ...]. Keep answers concise and quote verbatim only when explicitly quoting.
```

**How source attribution is surfaced in the response:** the model is required to
append inline citations in `[sources: <file_name> - <created_date>]` form, drawn
from the metadata in each context block. Observed answers cite real source
files, e.g. `[sources: reddit_Dorms _ r_UCI.txt, prked_Best UC Irvine Dorms_...]`.

---

## Evaluation Report

<!-- Run your 5 test questions from planning.md through your system and record the results. -->

Results below are the actual system outputs (top-k = 10, distance threshold 0.4).

| # | Question | Expected answer | System response (summarized) | Retrieval quality | Response accuracy |
|---|----------|-----------------|------------------------------|-------------------|-------------------|
| 1 | Which dorms are quieter or more social? | Middle Earth is often more social and Mesa Court is more quiet | Middle Earth is often seen as more social and community-oriented, opinions on Mesa Court’s social atmosphere are mixed. | Relevant (all chunks have distance scores of around 0.30) | Partially accurate |
| 2 | What hidden costs should I expect besides housing rates? | Common extra costs include meal plans for on-campus dorms, separate parking fees for ACC/off-campus housing, and utilities in some apartments. | You should expect utility bills ($40-70), and laundry costs ($4), and parking fee | Partially relevant (chunks has distance score around 0.38) | accurate |
| 3 | Is the UCI housing lottery actually random, or are there patterns students report? | The process is competitive and lottery-like. | It's described as a "complete lottery" | relevant (many chunks have distances of 0.2x) | accurate |
| 4 | How is the safety level at Middle Earth? | I couldn't find anything relevant in my knowledge base. (There's not really direct information about Middle Earth's safety, but students mention some practical issues in the classics like older facilities, pests, and maintenance problems) | I couldn't find anything relevant in my knowledge base. | Partially relevant (Middle Earth chunks retrieved, but few explicitly discuss safety) | accurate | 
| 5 | How does off-campus cost compare to on-campus? | On-campus dorms can be expensive especially when meal plan are required. Off-campus can be more flexible, but not always cheaper. | On-campus housing prices range from $5,500 to $6,000 per quarter. Off-campus housing prices are negotiable and can be $100-$200 less per month | partially relevant (with distances around 0.35) | Accurate |
| 6 |Where can i stay as a transfer student?| For continuing/transfer students, the ACC apartments are one of the housing choices for them | As a transfer student, you can consider on-campus housing options such as Middle Earth or Mesa Court, or off-campus options like the ACC apartments | Off-target (pulled from docs for first year students) | inaccurate |
| 7 |Is the weather good today?|I couldn't find anything relevant in my knowledge base.| I couldn't find anything relevant in my knowledge base | Off-target (but all chunks have distances > 0.45, which is expected for out-of-context-questions) | accurate |


**Retrieval quality:** Relevant / Partially relevant / Off-target
**Response accuracy:** Accurate / Partially accurate / Inaccurate

---

## Failure Case Analysis

<!-- Identify at least one question where retrieval or generation did not work as expected. -->

**Question that failed:** "Where can i stay as a transfer student?"

**What the system returned:** "As a transfer student, you can consider on-campus housing options such as Middle Earth or Mesa Court, or off-campus options like American Campus Communities (ACC) apartments [sources: prked_Best UC Irvine Dorms_ Middle Earth vs. Mesa Court Guide.txt, society19_Ultimate Ranking of UCI Dorms - Society19.txt]. However, it is recommended to check with UCI admissions for available options [sources: reddit_Where to look for housing _ r_UCI.txt]."

**Root cause (tied to a specific pipeline stage):** This is a
retrieval / corpus-coverage failure. The corpus is heavily skewed toward *first-year* housing content (most Reddit threads and ranking guides discuss Middle Earth vs. Mesa Court for incoming freshmen). When the query mentions "transfer student," the embedding model matches on the dominant signal: "housing / dorms / where to stay", and the nearest chunks are all about freshman dorms. The audience qualifier ("first-year only") is usually implicit or in a separate sentence from the dorm name, so it doesn't travel with the retrieved chunk. The model was grounded but on an incorrect context.

**What you would change to fix it:**
- **Corpus coverage:** ingest more transfer/continuing-student sources
- **Metadata filtering:** tag chunks by audience (first-year vs.
  continuing/transfer) at ingestion and filter on it when the query names an
  audience, so freshman-only chunks are excluded from a transfer query.

---

## Spec Reflection

<!-- Reflect on how planning.md shaped your implementation. -->

**One way the spec helped you during implementation:** 
- The Chunking Strategy and
Retrieval Approach sections settled every hard design choice before any code
was written. The spec had already identified that the corpus has two shapes:
short Reddit comments vs. long guides, and that they shouldn't share one chunk
size, which directly dictated the length-routing implementation: semantic
chunking for long docs, sentence chunking for short ones.

- naming the embedding model (`bge-base-en-v1.5`), top-k, and cosine similarity up front meant
`chunk_document()`, `embed_and_store()`, and `retrieve()` had no open design
questions left at coding time. The AI Tool Plan's prompts mapped almost
one-to-one onto the shipped functions, so directing the AI was mostly
transcription rather than redesign.

**One way your implementation diverged from the spec, and why:** The spec
underestimated the work in two stages, and I expanded both once I saw real output.

- **Ingestion / PDF cleaning.** Planning.md described preprocessing as a single
  step: extract the PDFs, strip navigation and ads, and drop the right-side
  column of related-post links on Reddit pages. Once I actually ran extraction I
  found the raw text was far noisier than the spec assumed, so
  `helpers/pdf_extract.py` grew several cleaning passes the plan never mentioned:
  removing the browser print header (`<date>, <time> <title>`) that repeats on
  every printed page, stripping share widgets and pagination via line-level noise
  patterns, and more careful detection of the sidebar columns so left/right text
  doesn't interleave. The spec didn't anticipate how much chrome a browser-printed PDF carries.

- **Generation / system prompt.** The spec gave a single grounding paragraph for
  the prompt, but testing showed early answers still drifted or cited inconsistently. 
  Therefore, i had to refine the prompt and reformat the output many times. I also moved
  the no-answer decision out of the prompt entirely into a code-level
  `DISTANCE_THRESHOLD = 0.4` filter in `generate_response()`, so off-topic queries
  are blocked deterministically before the LLM is even called, rather than relying
  on the model to obey a refusal instruction.

  Additionally The planned `retrieve_v2()` hybrid (semantic + BM25) also remains unimplemented and stays a stretch item.

---

## AI Usage

<!-- Describe at least 2 specific instances where you used an AI tool during this project. -->

**Instance 1 — Chunking implementation**

- *What I gave the AI:* my Chunking Strategy section from planning.md, the loaded
  document dicts from `load_documents()`, and the existing fixed-size stub, with
  the instruction to implement `chunk_document(doc_item)` using semantic chunking
  for long docs and sentence/fixed-size chunking for short ones.
- *What it produced:* a length-routed implementation — LangChain `SemanticChunker`
  for docs ≥ 6000 chars that are not from Reddit, and a sentence-packing chunker with 10-word overlap for remaining docs 
- *What I changed or overrode:* I routed documents by text length + site name rather
  instead of just text length, because after testing the pipeline, I notice many Reddit threads, which contain many short comments, sum up to be a very long page

**Instance 2 — Gradio chat interface**

- *What I gave the AI:* a minimal Gradio `Blocks` skeleton and a request for a
  chatbox + submit button wired to `generate_response(query)`, styled dark gray
  with blue/yellow accents, later refined toward a glassmorphism look from a
  reference screenshot.
- *What it produced:* a `gr.Blocks` UI with a `gr.Chatbot`, input row, example
  prompts, a `respond()` handler tying `retrieve()` → `generate_response()`, and
  a custom theme + CSS (translucent frosted panels, blurred backdrop, tinted
  gradients).
- *What I changed or overrode:* I directed it to keep my exact palette while
  restyling, and it adapted to Gradio 6 API changes (theme/CSS moved to
  `launch()`, `gr.Chatbot` dropping the `type` argument) that the first draft
  got wrong.
