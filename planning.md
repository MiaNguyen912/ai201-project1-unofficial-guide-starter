# Project 1 Planning: The Unofficial Guide

> Write this document before you write any pipeline code.
> Your spec and architecture diagram are what you'll use to direct AI tools (Claude, Copilot, etc.) to generate your implementation — the more specific they are, the more useful the generated code will be.
> Update the Retrieval Approach and Chunking Strategy sections if you change your approach during implementation.
> Update this file before starting any stretch features.

---

## Domain

<!-- What domain did you choose? Why is this knowledge valuable and hard to find through official channels? -->
I have chosen the domain "Housing and Dorms at UC Irvine" because I used to have questions like:
- "Which dorms are quiet versus social, and which suit freshmen vs upperclassmen?"
- "What hidden costs should I expect besides housing rates?"
- "Is the UCI housing lottery actually random, or are there patterns students report?"
- "how is the safety level at dorm X?"
- "how is the living cost for off‑campus complexes near UCI compared to on‑campus dorm options?"

This knowledge is valuable because it usually comes from students' practical experience about on‑campus and nearby housing, including lottery behavior, waitlist tactics, roommate fit, maintenance responsiveness, hidden costs, and move‑in logistics, etc. The official pages list rules and rates but rarely capture timing tricks, social dynamics, or real-world issues that students depend on.

---

## Documents

<!-- List your specific sources: URLs, subreddit names, forum threads, or file descriptions.
     Aim for at least 10 sources that together cover different subtopics or perspectives within your domain. -->

| # | Source | Description | URL or location |
|---|--------|-------------|-----------------|
| 1 |Reddit|students sharing and comparing their experiences and opinions on housing at UCI, including costs, availability, and the challenges of finding affordable on-campus or nearby housing.|https://www.reddit.com/r/UCI/comments/1b40x2f/housing/|
| 2 |ratemydorm|a student review-based ranking of UC Irvine dorms that compares housing options using crowd-sourced ratings and written experiences about comfort, location, cost, and overall living quality.|https://www.ratemydorm.com/dorms-ranked/university-of-california-irvine|
| 3 |wordpress blog|a detailed student-written review of UC Irvine undergraduate housing that compares and ranks the on-campus dorms and apartment communities based on livability, amenities, social life, and overall student experience.|https://campusobscura.wordpress.com/2024/06/11/the-best-and-worst-of-ucis-undergrad-on-campus-housing/|
| 4 |Reddit|student asking for advice about freshman dorm options and get advice|https://www.reddit.com/r/UCI/comments/1ruj1dt/dorms/|
| 5 |Reddit|a first-year student’s breakdown of UC Irvine dorm life, comparing Mesa Court and Middle Earth, sharing pros and cons like location, bathroom quality, social life, and overall living experience.|https://www.reddit.com/r/UCI/comments/1jckpkn/first_year_housing_scoop/|
| 6 |society19 blog|article about a student's ranking of UC Irvine dorms that compares the different housing communities and explains their pros and cons based on location, amenities, room quality, and overall freshman experience.|https://www.society19.com/ultimate-ranking-uci-dorms/|
| 7 |prked blog|an insider guide to UC Irvine undergraduate housing that explains the different dorm communities and compares their layouts, social atmosphere, amenities, and tradeoffs to help incoming students choose where to live.|https://prked.com/post/deciphering-the-dorms-an-insiders-guide-to-the-best-housing-at-uc-irvine|
| 8 |tripalink blog|a comparison of UC Irvine dorms versus off-campus housing|https://tripalink.com/blog/uc-irvine:-dorms-vs.-off-campus-housing|
| 9 |Reddit|dorm recommendations and application tips for incoming UCI freshmen|https://www.reddit.com/r/UCI/comments/1t00phj/dorm_recommendations_and_application_tips_for/|
| 10 |Reddit|advice on how to find housing near UCI|https://www.reddit.com/r/UCI/comments/1luxaac/where_to_look_for_housing/|
| 11 |Reddit|advice on housing options for continuing students|https://www.reddit.com/r/UCI/comments/1oa9vmh/housing_recs_for_second_yr/|

---

## Chunking Strategy

<!-- How will you split documents into chunks?
     State your chunk size (in tokens or characters), overlap size, and explain why those
     numbers fit the structure of your documents.
     A review-heavy corpus warrants different chunking than a long FAQ. -->

**Chunk size:**

**Overlap:**

**Reasoning:**

---

## Retrieval Approach

<!-- Which embedding model are you using (e.g., all-MiniLM-L6-v2 via sentence-transformers)?
     How many chunks will you retrieve per query (top-k)?
     If you were deploying this for real users and cost wasn't a constraint, what tradeoffs
     would you weigh in choosing a different embedding model — context length, multilingual
     support, accuracy on domain-specific text, latency? -->

**Embedding model:**

**Top-k:**

**Production tradeoff reflection:**

---

## Evaluation Plan

<!-- List your 5 test questions with their expected correct answers.
     Questions should be specific enough that you can judge whether the system's response
     is right or wrong. "What are good dining halls?" is too vague.
     "What do students say about wait times at [dining hall name] during lunch?" is testable. -->

| # | Question | Expected answer |
|---|----------|-----------------|
| 1 | | |
| 2 | | |
| 3 | | |
| 4 | | |
| 5 | | |

---

## Anticipated Challenges

<!-- What could go wrong? Name at least two specific risks with reasoning.
     Consider: noisy or inconsistent documents, missing source attribution, off-topic
     retrieval, chunks that split key information across boundaries. -->

1.

2.

---

## Architecture

<!-- Draw a diagram of your pipeline showing the five stages:
     Document Ingestion → Chunking → Embedding + Vector Store → Retrieval → Generation
     Label each stage with the tool or library you're using.
     You can use ASCII art, a Mermaid diagram, or embed a sketch as an image.
     You'll use this diagram as context when prompting AI tools to implement each stage. -->

---

## AI Tool Plan

<!-- For each part of the pipeline below, describe:
     - Which AI tool you plan to use (Claude, Copilot, ChatGPT, etc.)
     - What you'll give it as input (which sections of this planning.md, which requirements)
     - What you expect it to produce
     - How you'll verify the output matches your spec

     "I'll use AI to help me code" is not a plan.
     "I'll give Claude my Chunking Strategy section and ask it to implement chunk_text()
     with my specified chunk size and overlap" is a plan. -->

**Milestone 3 — Ingestion and chunking:**

**Milestone 4 — Embedding and retrieval:**

**Milestone 5 — Generation and interface:**
