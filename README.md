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

**Chunk examples**: 

```json
{
  text: roommates been having problems with doing an online meeting study. The bathrooms are nice, there are side mirrors that can open u and be cabinets for your toothbrush and other stuff. You do need to get your own shower curtain (definitely talk with your roommates about this!). I forgot to mention t beds are XL Full size beds so you will need queen sized sheets! 4B2B Virtual Google floorplan Tour: Renovated NonRenovated
  chunk_id: reddit_housing_recs_for_second_yr_r_uci_6
  site: reddit
  created_date: unknown
  filename: reddit_housing recs for second yr _ r_UCI.txt
}, 
{
  text: up so students drop out or change plans last minute. You could also try asking around in UCI housing groups to see if anyoneʼs moving out soon. Craigslist still might have legit listings too, but I just highly recommend checking out UniShack or other apartment sites. Good luck! Disgraced-Academic • 1y ago Undergrad [2026] https://www.reddit.com/r/UCI/comments/1luxaac/where_to_look_for_housing/ Grad students are offered guaranteed UCI housing. Talk to admissions about your options
  chunk_id: reddit_where_to_look_for_housing_r_uci_4
  site: reddit
  created_date: unknown
  filename: reddit_Where to look for housing _ r_UCI.txt
}, 
{
  text: off campus house for the summer an fall quarter ! Itʼs 5-6 min from campus negotiable on price if interested please let me https://www.reddit.com/r/UCI/comments/1b40x2f/housing/ know !!! (Girls only) includes washer/ dryer and free parking 🙌🏻 That-Channel-5227 • 2y ago Heyy guys I am subleasing a private room in an off campus house for the summer an fall quarter ! Itʼs 5-6 min from campus negotiable on price if interested please let me know !!!
  chunk_id: reddit_housing_uci_1
  site: reddit
  created_date: unknown
  filename: reddit_Housing_UCI.txt
},
{
  text: queen sized sheets! 4B2B Virtual Google floorplan Tour: Renovated NonRenovated Edit: I will also say there will be an option of 3 communities, 2 floorplans each that yo can put down! However, there should be a waitlist for each community with residents students, and incoming students applying. Incoming students and some continuing residents only have 2 years of guaranteed housing if they had submitted it in their fir year. https://www.reddit.com/r/UCI/comments/1oa9vmh/housing_recs_for_second_yr/
  chunk_id: reddit_housing_recs_for_second_yr_r_uci_7
  site: reddit
  created_date: unknown
  filename: reddit_housing recs for second yr _ r_UCI.txt
  distance: 0.39555078744888306
},
{
  text: parking fee to park at YOUR ACC apartment parking lot. Guests also have to pay for parking since there are the UCI ticketing ppl are very serious abt their jobs. I would also look at the amenities each community ha to offer: basketball courts, gym, swimming pool, grill, study rooms, game rooms, etc Some apartments will have virtual tours of the general layout of the amenities and floorplan. https://www.reddit.com/r/UCI/comments/1oa9vmh/housing_recs_for_second_yr/
  chunk_id: reddit_housing_recs_for_second_yr_r_uci_2
  site: reddit
  created_date: unknown
  filename: reddit_housing recs for second yr _ r_UCI.txt
}

```



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

## Retrieval test examples
- **Example 1:** Given user query "What hidden costs should I expect besides housing rates?", top 20 chunks returned  (with distance score attached) are:
  <details>
    <summary>Click to expand code</summary>

  ```json
  {
          text: if they had submitted it in their fir year. https://www.reddit.com/r/UCI/comments/1oa9vmh/housing_recs_for_second_yr/ LMK if you have anymore questions though, I know how tough it is with researching about each place. Oh, there utility bill is included with the rent at VDC and VDCN, but one load of laundry (wash & dry) is like $4. I know the utility bill depends on usage but it can range from $40-70 if I remember correctly. Your roomies and you will need to create an account to pay your bills.
          chunk_id: reddit_housing_recs_for_second_yr_r_uci_8
          site: reddit
          created_date: unknown
          filename: reddit_housing recs for second yr _ r_UCI.txt
          distance: 0.3481440544128418
  }
  --------------------------------------------------
  {
          text: ago Thank you for the advice junebug122_ • 1y ago Housing near UCI is tough, especially for out-of-state grad students. The scammy Facebook listings donʼt help either. I would check out UniShack since they've been getting more Irvine listings, and their verification cuts down on scams. Itʼs definitely worth checking often, especially since August is when a lot of spots open up so students drop out or change plans last minute.
          chunk_id: reddit_where_to_look_for_housing_r_uci_3
          site: reddit
          created_date: unknown
          filename: reddit_Where to look for housing _ r_UCI.txt
          distance: 0.36368227005004883
  }
  --------------------------------------------------
  {
          text: expect to be able to sprawl your stuff out tooo much (youʼll still have your own desk/closet ofc) extremely competitive, even if you have 3 other mutually-requested roommates itʼs still a complete lottery (I did this and got a double with one of my requested roommates) https://www.reddit.com/r/UCI/comments/1jckpkn/first_year_housing_scoop/ international / out of state get a touch of priority here iirc so if youʼre in-state itʼs just that much more in the air
          chunk_id: reddit_first_year_housing_scoop_r_uci_3
          site: reddit
          created_date: unknown
          filename: reddit_first year housing scoop _ r_UCI.txt
          distance: 0.37136244773864746
  }
  --------------------------------------------------
  {
          text: Cons: FAR from campus, limited bus options, big parking lot but they do check
  it. laundry room is in a separate building. other than your
  roommates/housemates, you prob won't get to know anyone else in the
  building or community. Very few community activities, if that's your kind of
  thing. Also, you'll need to bring your own cookware and make your own food,
  cuz no dining halls. Also, no elevators, which is a hassle during move in/out - 5
  years ago
  We collected 4 dorm reviews for VDC (Vista del Campo)
  Browse all 4 dorm reviews
  Mesa Court
  based on 29 reviews
  https://www.ratemydorm.com/dorms-ranked/university-of-california-irvine 6/16
  https://www.ratemydorm.com/dorms-ranked/university-of-california-irvine 7/16
  Background: former occupant of a quad in Caballo (Mesa Court Towers)
  Downsides of a quad are privacy and space. I had morning classes all the time,
  so I had to be more mindful of my alarms.
          chunk_id: ratemydorm_uci_dorms_ranked_3
          site: ratemydorm
          created_date: unknown
          filename: ratemydorm_UCI_Dorms_Ranked.txt
          distance: 0.37984758615493774
  }
  --------------------------------------------------
  {
          text: which is what most of your buildings will be on (ME towers are like a minute walk from ICS/Engineering lmao) cheapest option yet by a whole marathon the highest quality rooming option. // cons: 4 people to a room (meaning youʼll have 3 roommates!) so if youʼre not used to that it may be a bit of a change lol. also itʼs bunk beds kinda going off the last one but the rooms are well-sized but not massive, so unless youʼve got amazing roommates donʼt expect to be able to sprawl your stuff out tooo
          chunk_id: reddit_first_year_housing_scoop_r_uci_2
          site: reddit
          created_date: unknown
          filename: reddit_first year housing scoop _ r_UCI.txt
          distance: 0.3809093236923218
  }
  --------------------------------------------------
  {
          text: outdated and would probably not pass modern-day housing inspection regulations. Considering some of this are from the 70ʼs, your ceilings are literally popcorn/asbestos and extremely low. housing office/maintenance does their best but youʼll be filing five times the amount of work orders compared to mesa, and likely for worse reasons. PESTS. In fact, there is actually a mouse my roommate and I cannot find as of the time of this writing that is actively inside of my room.
          chunk_id: reddit_first_year_housing_scoop_r_uci_12
          site: reddit
          created_date: unknown
          filename: reddit_first year housing scoop _ r_UCI.txt
          distance: 0.38348549604415894
  }
  --------------------------------------------------
  {
          text: will need to create an account to pay your bills. I also like VDC since it has individual liability, so I wonʼt be penalized unless damage was found in the common space and no one owns up to it. drcu-lah • 8mo ago • Edited 8mo ago If u have a car, vdc is prob best cos theres close and a lot of parking, pv parking is hit or miss youʼll be able to find spots during the day but after 5pm youʼll have to park very
          chunk_id: reddit_housing_recs_for_second_yr_r_uci_9
          site: reddit
          created_date: unknown
          filename: reddit_housing recs for second yr _ r_UCI.txt
          distance: 0.38871800899505615
  }
  --------------------------------------------------
  {
          text: all the options here. rooms are generally nice, so are the bathrooms (1:4 ratio of people:stall/shower, which comparatively speaking is actually the best for this list). youʼre wayyyyy less likely (if it all) to have pest or other problems with your building. bathroom is connected to the room, and you have elevators! youʼll have one of the two dining halls (Anteatery for Mesa, Brandywine for Middle Earth) right below you + proximity to ring road which is what most of your buildings will be on
          chunk_id: reddit_first_year_housing_scoop_r_uci_1
          site: reddit
          created_date: unknown
          filename: reddit_first year housing scoop _ r_UCI.txt
          distance: 0.39247000217437744
  }
  --------------------------------------------------
  {
          text: queen sized sheets! 4B2B Virtual Google floorplan Tour: Renovated NonRenovated Edit: I will also say there will be an option of 3 communities, 2 floorplans each that yo can put down! However, there should be a waitlist for each community with residents students, and incoming students applying. Incoming students and some continuing residents only have 2 years of guaranteed housing if they had submitted it in their fir year. https://www.reddit.com/r/UCI/comments/1oa9vmh/housing_recs_for_second_yr/
          chunk_id: reddit_housing_recs_for_second_yr_r_uci_7
          site: reddit
          created_date: unknown
          filename: reddit_housing recs for second yr _ r_UCI.txt
          distance: 0.39555078744888306
  }
  --------------------------------------------------
  {
          text: parking fee to park at YOUR ACC apartment parking lot. Guests also have to pay for parking since there are the UCI ticketing ppl are very serious abt their jobs. I would also look at the amenities each community ha to offer: basketball courts, gym, swimming pool, grill, study rooms, game rooms, etc Some apartments will have virtual tours of the general layout of the amenities and floorplan. https://www.reddit.com/r/UCI/comments/1oa9vmh/housing_recs_for_second_yr/
          chunk_id: reddit_housing_recs_for_second_yr_r_uci_2
          site: reddit
          created_date: unknown
          filename: reddit_housing recs for second yr _ r_UCI.txt
          distance: 0.39618051052093506
  }
  --------------------------------------------------
  {
          text: Crystalmancy0906 Housing How expensive is housing at UCI (on and off campus)? 3 14 Share Sort by: Best Search Comments ShiverPike_ • 2y ago better get that kidney ready 58 Reply Award Share mylittlecoochie1989 • 2y ago I lived in a double in Mesa Court from 2022-2023 and it was about $5,500-$6,000 a quarter. Housing is so expensive itʼs ridiculous. 3 Reply Award Share That-Channel-5227 • 2y ago Heyy guys I am subleasing a private room in an off campus house for the summer an fall quarter !
          chunk_id: reddit_housing_uci_0
          site: reddit
          created_date: unknown
          filename: reddit_Housing_UCI.txt
          distance: 0.39650237560272217
  }
  --------------------------------------------------
  {
          text: of the general layout of the amenities and floorplan. https://www.reddit.com/r/UCI/comments/1oa9vmh/housing_recs_for_second_yr/ However, if you have time, you could just walk through each community and join in o events. I would check their instagrams, while it is also mainly for residents I have see nonresidents there. Plaza Verde I and II difference would be what building you choos to live in, this reddit post should be helpful in getting a geographical idea! There see
          chunk_id: reddit_housing_recs_for_second_yr_r_uci_3
          site: reddit
          created_date: unknown
          filename: reddit_housing recs for second yr _ r_UCI.txt
          distance: 0.3975330591201782
  }
  --------------------------------------------------
  {
          text: You have privacy for yourself
  and if you want to bring a friend over. The lodge let’s you print for free. The
  place comes with a washer and dryer. There’s a shuttle so you don’t have to
  walk to campus (it’s about a 25min walk). Cons:
  The walls are very thin so I was able to hear my housemates talk on the phone or
  whenever they had sex LOL (Buy earplugs!). The WiFi sometimes sucks too and
  your calls might end. The lighting sucks so I recommend buying a lamp for your
  room. Oh and buy a shower curtain! Overall:
  It also depends on your housemates and how chill they are. My housemates were very chill. My boyfriend came over every weekend and
  they brought guys over too. One of my housemates’ boyfriend lived with us and
  he was very chill as well. Me and the other two housemates didn’t care. They
  were super understanding.
          chunk_id: ratemydorm_uci_dorms_ranked_7
          site: ratemydorm
          created_date: unknown
          filename: ratemydorm_UCI_Dorms_Ranked.txt
          distance: 0.3985249996185303
  }
  --------------------------------------------------
  {
          text: in the back of Mesa Court rn too, and if you live by Lot 5 in the later phase buildings, you'll be wayy further away from everything (it's nice if you have a car though). https://www.reddit.com/r/UCI/comments/1jckpkn/first_year_housing_scoop/ 10/11 https://www.reddit.com/r/UCI/comments/1jckpkn/first_year_housing_scoop/ 11/11
          chunk_id: reddit_first_year_housing_scoop_r_uci_38
          site: reddit
          created_date: unknown
          filename: reddit_first year housing scoop _ r_UCI.txt
          distance: 0.400068998336792
  }
  --------------------------------------------------
  {
          text: my opinion and the general opinion of those I know. First of all, do NOT get a triple. DO NOT. Thatʼs worst case scenario and a very bad idea. Second, do not get housing at the Middle Earth classics. Theyʼre not great and are not worth it. If you really donʼt want a quad, Mesa Classics are an option for a double, but if Iʼm being honest with you, Iʼve always had my own room growing up and the quad was a million times better.
          chunk_id: reddit_dorms_r_uci_26
          site: reddit
          created_date: unknown
          filename: reddit_Dorms _ r_UCI.txt
          distance: 0.4024650454521179
  }
  --------------------------------------------------
  {
          text: room, grill, pool and etc are available. Also study room. https://www.reddit.com/r/UCI/comments/1b40x2f/housing/ Expectations: male, no pets, no smoking Estimated rent: ~900 Specific_Switch1008 • 1y ago Private room for rent, off campus available Early August - Sept 1st the latest Includin utilities $1,450. monthly 2 UCI students upstairs. Free Parking - bus stop by the hous Super Clean, quiet house For a faster response call Lucy 949 331 7474
          chunk_id: reddit_housing_uci_4
          site: reddit
          created_date: unknown
          filename: reddit_Housing_UCI.txt
          distance: 0.4028562307357788
  }
  --------------------------------------------------
  {
          text: roommates been having problems with doing an online meeting study. The bathrooms are nice, there are side mirrors that can open u and be cabinets for your toothbrush and other stuff. You do need to get your own shower curtain (definitely talk with your roommates about this!). I forgot to mention t beds are XL Full size beds so you will need queen sized sheets! 4B2B Virtual Google floorplan Tour: Renovated NonRenovated
          chunk_id: reddit_housing_recs_for_second_yr_r_uci_6
          site: reddit
          created_date: unknown
          filename: reddit_housing recs for second yr _ r_UCI.txt
          distance: 0.40496110916137695
  }
  --------------------------------------------------
  {
          text: up so students drop out or change plans last minute. You could also try asking around in UCI housing groups to see if anyoneʼs moving out soon. Craigslist still might have legit listings too, but I just highly recommend checking out UniShack or other apartment sites. Good luck! Disgraced-Academic • 1y ago Undergrad [2026] https://www.reddit.com/r/UCI/comments/1luxaac/where_to_look_for_housing/ Grad students are offered guaranteed UCI housing. Talk to admissions about your options
          chunk_id: reddit_where_to_look_for_housing_r_uci_4
          site: reddit
          created_date: unknown
          filename: reddit_Where to look for housing _ r_UCI.txt
          distance: 0.4051750898361206
  }
  --------------------------------------------------
  {
          text: off campus house for the summer an fall quarter ! Itʼs 5-6 min from campus negotiable on price if interested please let me https://www.reddit.com/r/UCI/comments/1b40x2f/housing/ know !!! (Girls only) includes washer/ dryer and free parking 🙌🏻 That-Channel-5227 • 2y ago Heyy guys I am subleasing a private room in an off campus house for the summer an fall quarter ! Itʼs 5-6 min from campus negotiable on price if interested please let me know !!!
          chunk_id: reddit_housing_uci_1
          site: reddit
          created_date: unknown
          filename: reddit_Housing_UCI.txt
          distance: 0.40838485956192017
  }
  --------------------------------------------------
  {
          text: so if youʼre in that field and donʼt mind it being quieter this isnʼt too bad for that. closer to UTC than Mesa, DSC is also very close so if you have a disability youʼll be within pretty feasible walking distance // cons: THE GHETTO OF THIS CAMPUS AND IT IS NON-NEGOTIABLE. Phase 1 are quite literally the oldest dorms on campus, many of which are outdated and would probably not pass modern-day housing inspection regulations.
          chunk_id: reddit_first_year_housing_scoop_r_uci_11
          site: reddit
          created_date: unknown
          filename: reddit_first year housing scoop _ r_UCI.txt
          distance: 0.41319739818573
  }
  --------------------------------------------------
  ```

  </details>

  - **Why these chunks are relevant:** the query targets costs, and the top returned chunks mention the hidden extras such as utility bills ($40–70/mo), per-load laundry ($4), and separate ACC/guest parking fees — plus base-rate anchors ($5,500–6,000/quarter) for comparison. The embedding matched on the "extra cost / fee / bill" signal rather than the word "housing" alone, so it pulled the practical out-of-pocket details students actually pay on top of rent.

- **Example 2:** Given user query "which dorm is more fun?", top 20 chunks returned (with distance score attached) are:
  <details>
  <summary>Click to expand code</summary>

  ```json
    {
          text: and pippin gym/lounge are practically embedded with the dorms so youʼll have decent physical amenities within reach (mesa has courts too, though I personally like ME layout for this more.) Some building have their bathrooms on the first floor actually have locks (as well as the showers for suites on the bottom floor!) quirky names for each of the buildings which is always fun to joke about. also ME is known for being very STEM-side of campus so if youʼre in that field and donʼt mind it
          chunk_id: reddit_first_year_housing_scoop_r_uci_10
          site: reddit
          created_date: unknown
          filename: reddit_first year housing scoop _ r_UCI.txt
          distance: 0.2572186589241028
  }
  --------------------------------------------------
  {
          text: will acknowledge that im not used to sharing my space. i think i might go crazy in a quad, but i am also hearing that the towers are better so im stuck! https://www.reddit.com/r/UCI/comments/1ruj1dt/dorms/ womenloverbot • 3mo ago a lot of people say the towers are the best because theyʼre the newest! als sharing the bathroom with 7 people versus around 12 is simpler. itʼs also easier to socialize but honestly if youʼre going to join clubs, youʼll find peop that way anyway.
          chunk_id: reddit_dorms_r_uci_16
          site: reddit
          created_date: unknown
          filename: reddit_Dorms _ r_UCI.txt
          distance: 0.26378023624420166
  }
  --------------------------------------------------
  {
          text: in amenities but they are newer and therefore nicer. The rooms are all 4 person set-ups and two rooms share one bathroom (aka 8 people to one bathroom). There is a large common space and a larger laundry room. The towers are cheaper, have newer stuff, and are closer to the cafeteria/campus but are more cramped. Dorms can be further from campus/cafeteria, are way older, and pricier but have the option for a single or double. womenloverbot • 3mo ago
          chunk_id: reddit_dorms_r_uci_14
          site: reddit
          created_date: unknown
          filename: reddit_Dorms _ r_UCI.txt
          distance: 0.2742462158203125
  }
  --------------------------------------------------
  {
          text: the walking is manageable despite what anyone else says. 2. Doubles are fine, but if you can adjust Quads are Best, 1. They are cheapest 3. Bathroom shared by 8 people rather than whole floor with 2 showers and toilets Also cleaned everyday. 4. Most space of all the floor plans 5. Lot of newer rooms and feels, classics feel older and also known to have more bugs and roaches. (Almost none in towers) https://www.reddit.com/r/UCI/comments/1ruj1dt/dorms/
          chunk_id: reddit_dorms_r_uci_6
          site: reddit
          created_date: unknown
          filename: reddit_Dorms _ r_UCI.txt
          distance: 0.2872641086578369
  }
  --------------------------------------------------
  {
          text: have more bugs and roaches. (Almost none in towers) https://www.reddit.com/r/UCI/comments/1ruj1dt/dorms/ If I were you or myself and I could do it again, Mesa Court towers are the way to go. ipoopmyself123 • 3mo ago how can a dorm be soecially more social i never understood that StolenApollo • 3mo ago Zot Tuah It canʼt lmao this has always been a dumb take. Middle Earth had so many activities all the time and the common room was lively and fun. No idea
          chunk_id: reddit_dorms_r_uci_7
          site: reddit
          created_date: unknown
          filename: reddit_Dorms _ r_UCI.txt
          distance: 0.2899653911590576
  }
  --------------------------------------------------
  {
          text: The big question I always hear
  from incoming students is, "Which one is better?" The honest answer? It totally depends on what you're looking for. Let's start with the 10,000-foot view. Both communities are located on campus & are primarily for freshmen, which
  is great for meeting people in the same boat as you. Both require you to have a meal plan, so you'll be swiping your
  card at one of the two main dining halls. & both have a mix of housing styles, which is where the real decision-
  making comes in. The biggest debate usually boils down to this: Middle Earth is generally seen as more convenient for classes,
  while Mesa Court is often described as more social & aesthetically pleasing. But let's be real, it's way more
  nuanced than that.
          chunk_id: prked_best_uc_irvine_dorms_middle_earth_vs_mesa_court_guide_3
          site: prked
          created_date: 8/10/25
          filename: prked_Best UC Irvine Dorms_ Middle Earth vs. Mesa Court Guide.txt
          distance: 0.2916187047958374
  }
  --------------------------------------------------
  {
          text: donʼt know why this is but itʼs facts. https://www.reddit.com/r/UCI/comments/1ruj1dt/dorms/ 3. Mesa classics are better than middle earths classics… more storage, bigger rooms, less stuff broken. The towers are the same everywhere but you gotta liv with 4 people in ONE room and REALLY think about that before you decide that what u want to do. yes it might sound fun, but it becomes really old really quick when you want to just chill sometimes. Uhh they also donʼt have bugs… it might
          chunk_id: reddit_dorms_r_uci_3
          site: reddit
          created_date: unknown
          filename: reddit_Dorms _ r_UCI.txt
          distance: 0.292086124420166
  }
  --------------------------------------------------
  {
          text: Now comes the next big puzzle: where are you
  going to live? Choosing your first college dorm is a rite of passage, & honestly, it can feel like a bigger decision than
  picking your major. Your dorm is your home base, your social hub, & your late-night study sanctuary. At UCI, you've
  got some pretty distinct choices, each with its own vibe, perks, & quirks. As someone who's spent a ton of time navigating the ins & outs of UCI life, I'm here to give you the real scoop. We're
  going to break down the main housing communities, compare the shiny new towers to the classic halls, & even look
  at some of the less-common options. By the end of this, you'll have a much clearer picture of where you want to
  spend your freshman year. The Two Kingdoms: Middle Earth & Mesa Court
  For most first-year students at UCI, the housing journey begins with a choice between two legendary communities:
  Middle Earth & Mesa Court. No, you didn't accidentally enroll at Hogwarts or a Spanish villa—though the themes
  are strong.
          chunk_id: prked_best_uc_irvine_dorms_middle_earth_vs_mesa_court_guide_1
          site: prked
          created_date: 8/10/25
          filename: prked_Best UC Irvine Dorms_ Middle Earth vs. Mesa Court Guide.txt
          distance: 0.3019675016403198
  }
  --------------------------------------------------
  {
          text: get a good lock, or park it inside the dorms. Electric skateboard or normal skateboard is fun too. Just don't get an electric scooter. Post_Tip • 1y ago > bathroom is connected to the room, and you have elevators! Do we clean our bathrooms ourselves? Or are there janitors who go around and clean them? Thanks. RarestRaindrop • 1y ago • Edited 1y ago Consumer of Ants Conflict of interest on my part, but my time living in ME Classics Phase 2 wasn't bad at all.
          chunk_id: reddit_first_year_housing_scoop_r_uci_29
          site: reddit
          created_date: unknown
          filename: reddit_first year housing scoop _ r_UCI.txt
          distance: 0.30504441261291504
  }
  --------------------------------------------------
  {
          text: a key to every other floor Independent-Ad2443 • 3mo ago Now tell them about the AC (or search for older posts). https://www.reddit.com/r/UCI/comments/1ruj1dt/dorms/ Tenuous_Fawn • 3mo ago • Edited 3mo ago If you want a double you have the choice between middle earth classics and mesa classics. The difference is in proximity to your classes, middle earth is closer to socia sciences, engineering, and ics, while mesa is closer to humanities. Subsequently, me
          chunk_id: reddit_dorms_r_uci_9
          site: reddit
          created_date: unknown
          filename: reddit_Dorms _ r_UCI.txt
          distance: 0.3081335425376892
  }
  --------------------------------------------------
  {
          text: Mesa Court classics a long time ago and loved it. Back then it was only two to a room. What I like most about my dorm is that it was freshmen only. Since we were all new to the school and had no friends going in, everybody was incentivized to meet other people, and you were all going through the same experience together. We had a great RA who used to plan all kinds of activities both in the dorm and in the area, so it helped us get acclimated to our new hometown.
          chunk_id: reddit_dorms_r_uci_35
          site: reddit
          created_date: unknown
          filename: reddit_Dorms _ r_UCI.txt
          distance: 0.3085612654685974
  }
  --------------------------------------------------
  {
          text: this order: 1. ME Towers quad 2. Mesa Towers quad https://www.reddit.com/r/UCI/comments/1ruj1dt/dorms/ 8/11 3. Mesa Classics double 4. ME Classics double 5. Never get a triple 🙏 😭 Also, a few final notes I forgot to mention. Sharing a bathroom in the quads is MUCH nicer than the hall bathrooms in the classics and it isnʼt even close to comparable. They clean the bathrooms every day and do a nice clean once a week and since there
          chunk_id: reddit_dorms_r_uci_31
          site: reddit
          created_date: unknown
          filename: reddit_Dorms _ r_UCI.txt
          distance: 0.309506356716156
  }
  --------------------------------------------------
  {
          text: which is what most of your buildings will be on (ME towers are like a minute walk from ICS/Engineering lmao) cheapest option yet by a whole marathon the highest quality rooming option. // cons: 4 people to a room (meaning youʼll have 3 roommates!) so if youʼre not used to that it may be a bit of a change lol. also itʼs bunk beds kinda going off the last one but the rooms are well-sized but not massive, so unless youʼve got amazing roommates donʼt expect to be able to sprawl your stuff out tooo
          chunk_id: reddit_first_year_housing_scoop_r_uci_2
          site: reddit
          created_date: unknown
          filename: reddit_first year housing scoop _ r_UCI.txt
          distance: 0.31014347076416016
  }
  --------------------------------------------------
  {
          text: a number of the other dorms in the ME classics… all more expensive than the ME towers and I struggle to call these living conditions manageable sometimes (comparatively speaking to the rest of UCIʼs housing options) science library is much larger than langson though both are great CONFLICT OF INTEREST: I am in the classics at Middle Earth, though flooding and severe leakage has happened more than once for the buildings here so Iʼve had the opportunity to stay in Mesa as well.
          chunk_id: reddit_first_year_housing_scoop_r_uci_16
          site: reddit
          created_date: unknown
          filename: reddit_first year housing scoop _ r_UCI.txt
          distance: 0.3103370666503906
  }
  --------------------------------------------------
  {
          text: staff came once a week to clean our bathroom too! i took stem classes and GEʼs my first year and the walk really isnʼt bad at all (much prefer that over the bus rides from the apartments now). i know people are comparing the dining halls a bunch, but itʼs really not that big of a deal. your meal plan works at both dining halls so just go to whichever has the better options th day. the most important thing about a quad is that you get along with your roommates.
          chunk_id: reddit_dorms_r_uci_19
          site: reddit
          created_date: unknown
          filename: reddit_Dorms _ r_UCI.txt
          distance: 0.3111225366592407
  }
  --------------------------------------------------
  {
          text: better facilities. I also read some reviews on the Middle Earth classics and how they are the worst dorms to live in UCI due to being the oldest and least maintained. Is any of this true or just a myth? Also, for anyone living in quad towers, how is the spacing like and does the room really get that crowded with four people? Are you able to leave your stuff overnight in the shared bathrooms? How many rooms share a bathroom in the classics and can you leave your stuff there?
          chunk_id: reddit_dorm_recommendations_and_application_tips_for_starting_in_uci_as_a_freshman_r_uci_2
          site: reddit
          created_date: unknown
          filename: reddit_Dorm recommendations and application tips for starting in UCI as a freshman _ r_UCI.txt
          distance: 0.3115377426147461
  }
  --------------------------------------------------
  {
          text: Large number of couches and
  a good number of outlets in the common areas, perfect for game nights or study
  sessions. Brandywine dining hall is okay, seating is limited at peak hours and the
  food is decent, but gets boring after a quarter. My suite had 2 bathrooms for 11 people, with there being 1 toilet, 1 shower, and
  two sinks per bathroom. Private showers and toilets. The first floor has the ADA
  bathroom which is VERY spacious. Room sizes varied greatly, as the upper floors tended to have smaller rooms on
  average and size varied depending on where in the suite it was. Heaters on the
  first floor are either constantly on or need maintenance to turn on during the
  winter and to shut off in the spring. Bugs are an issue, mainly crickets. The kitchens can either be extremely cramped or very open depending on the
  individual floor plan of the hall. The Shire has a extremely narrow one while
  Rivendell has one that is completely open to the common room. My hall cooked
  a friendsgiving dinner in that kitchen, 20 lb turkey and all the sides, so it's
  doable, but limiting. The sink is small so dishes pile up. - 6 years ago
  We collected 27 dorm reviews for Middle Earth
  Browse all 27 dorm reviews
  https://www.ratemydorm.com/dorms-ranked/university-of-california-irvine 11/16
  Camino del Sol
  based on 3 reviews
  Camino Del Sol 4bedrooms/4.5bathrooms. Pros:
  You get an entire room and bathroom to yourself.
          chunk_id: ratemydorm_uci_dorms_ranked_6
          site: ratemydorm
          created_date: unknown
          filename: ratemydorm_UCI_Dorms_Ranked.txt
          distance: 0.3116529583930969
  }
  --------------------------------------------------
  {
          text: it later… https://www.reddit.com/r/UCI/comments/1ruj1dt/dorms/ The_Great-- • 3mo ago Take middle earth. It is was more social, people say it is not but they hating. They dining has more homely vibe to it and the food is exactly the same Unhappy-Welder3281 • 3mo ago I stayed in a Mesa Court double for orientation and am currently living in a Middle Earth double so here's my opinion for both: Mesa Court - Cons: Unless you are a humanities or arts major, most of your classes are
          chunk_id: reddit_dorms_r_uci_21
          site: reddit
          created_date: unknown
          filename: reddit_Dorms _ r_UCI.txt
          distance: 0.31186461448669434
  }
  --------------------------------------------------
  {
          text: agree with this too FlareKittens • 1y ago Undergrad [junior] I'd like to also add into the cons and pro list for ME (with specifics for classics): Pros: - You get access to that one building next to ME housing that is extremely quiet, very good for studying. They used to have a bean bag chair too but it's gone this year :( - Also close to campus for phase 1 - At least with my dorm, there's a bathtub for girls in the first floor if you want to take baths Cons:
          chunk_id: reddit_first_year_housing_scoop_r_uci_22
          site: reddit
          created_date: unknown
          filename: reddit_first year housing scoop _ r_UCI.txt
          distance: 0.3125799894332886
  }
  --------------------------------------------------
  {
          text: going to join clubs, youʼll find peop that way anyway. for privacy or personal space, towers are not better!!! whatʼs your priority for dorms? if you donʼt mind the classics being a bit old and less social, i would say itʼs worth it for having more privacy. abowlofsoupp • 3mo ago i lived in mesa towers my first year and iʼm an oldest sibling with a large ag gap whoʼs never shared a room. ik not the same as only child, but until college i had never shared my living space with anyone.
          chunk_id: reddit_dorms_r_uci_17
          site: reddit
          created_date: unknown
          filename: reddit_Dorms _ r_UCI.txt
          distance: 0.31305426359176636
  }
  --------------------------------------------------

  
  ```

  </details>

  - **Why these chunks are relevant:** keyword "fun" maps semantically to *social atmosphere*, and the closest chunks (distances ~0.26–0.31) are precisely the Middle Earth vs. Mesa Court "which is more social" debate. The retriever correctly read the keyword "fun" as the social-vibe dimension of the dorm comparison rather than a literal keyword, returning the threads where students argue over which community is livelier.

- **Example 3:** Given user query "is ACC apartments great?", top 20 chunks returned (with distance score attached) are:
  <details>
    <summary>Click to expand code</summary>

  ```json
    {
          text: Holiday_Wrongdoer595 housing recs for second yr hi guys!! iʼm a freshman and looking into acc apartments for next year. i had some question about which one you guys would recommend or the process of applying and leasing in general. iʼm interested in the 4 bed room ones at plaza verde (whatʼs the diff between 1 an 2?), vista del campo, and camino. pls lemme know thank you 🙏 🙏 10 2 Share Sort by: Best Search Comments xXColdRoseXx • 8mo ago • Edited 8mo ago Hello!
          chunk_id: reddit_housing_recs_for_second_yr_r_uci_0
          site: reddit
          created_date: unknown
          filename: reddit_housing recs for second yr _ r_UCI.txt
          distance: 0.21796143054962158
  }
  --------------------------------------------------
  {
          text: parking fee to park at YOUR ACC apartment parking lot. Guests also have to pay for parking since there are the UCI ticketing ppl are very serious abt their jobs. I would also look at the amenities each community ha to offer: basketball courts, gym, swimming pool, grill, study rooms, game rooms, etc Some apartments will have virtual tours of the general layout of the amenities and floorplan. https://www.reddit.com/r/UCI/comments/1oa9vmh/housing_recs_for_second_yr/
          chunk_id: reddit_housing_recs_for_second_yr_r_uci_2
          site: reddit
          created_date: unknown
          filename: reddit_housing recs for second yr _ r_UCI.txt
          distance: 0.2508244514465332
  }
  --------------------------------------------------
  {
          text: Comments xXColdRoseXx • 8mo ago • Edited 8mo ago Hello! Okay so I would recommend looking at the shuttle stop locations and line departures They donʼt run weekends so you might have to walk on campus if you have any on- campus weekend plans! There also should be places to lock your scooter/bike if you have that, but I have heard of ppl stealing at ACC still so be careful. If you plan to brin a car, you will have to pay a SEPARATE parking fee to park at YOUR ACC apartment parking lot.
          chunk_id: reddit_housing_recs_for_second_yr_r_uci_1
          site: reddit
          created_date: unknown
          filename: reddit_housing recs for second yr _ r_UCI.txt
          distance: 0.25631183385849
  }
  --------------------------------------------------
  {
          text: and dont have to super worry about sharing the space! https://www.reddit.com/r/UCI/comments/1ruj1dt/dorms/ 10/11 No-Employment-7629 • 3mo ago Just so you know, there's no AC @ UCI dorms. Amans4 • 3mo ago Ngl you should double in ACC or UTC apartments, on campus housing sucks. Great campus though, you will love your time here! https://www.reddit.com/r/UCI/comments/1ruj1dt/dorms/ 11/11
          chunk_id: reddit_dorms_r_uci_38
          site: reddit
          created_date: unknown
          filename: reddit_Dorms _ r_UCI.txt
          distance: 0.263935387134552
  }
  --------------------------------------------------
  {
          text: Each room has a restroom, and there’s a small common area with a
  kitchen/living room. It’s actually kind of terrible living in this situation unless you
  know your roommates beforehand; there’s barely any space in your room—if
  you can fit a desk in there, you’re lucky—and the common area offers little in the
  way of quiet/privacy. ACC is frankly a rip-off, but there are no better choices in Irvine unless you want
  to live in a cramped condo with 4-6 other people for $100-$200 less per month. -
  6 years ago
  We collected 1 dorm reviews for Puerta del Sol
  Browse all 1 dorm review
  VDC (Vista del Campo)
  based on 4 reviews
  https://www.ratemydorm.com/dorms-ranked/university-of-california-irvine 5/16
  I was in VDC and had a single with a shared bathroom. Pros: single rooms for decent price (compared to the other options around UCI),
  pretty quiet unless you're very unlucky in your neighbors, you only have to share
  communal space with ~4 people so things are usually much cleaner. furniture is
  provided.
          chunk_id: ratemydorm_uci_dorms_ranked_2
          site: ratemydorm
          created_date: unknown
          filename: ratemydorm_UCI_Dorms_Ranked.txt
          distance: 0.2712599039077759
  }
  --------------------------------------------------
  {
          text: The living room and kitchen are spacious and easy
  to clean, the bathrooms are modern and large, and the fixtures all around are
  decent. - 1 year ago
  We collected 1 dorm reviews for Plaza Verde II
  Browse all 1 dorm review
  Campus Village
  https://www.ratemydorm.com/dorms-ranked/university-of-california-irvine 13/16
  based on 2 reviews
  The room itself was quite large, single unfurnis
  apt. The apartment itself was a tad old and had a st
  quickly spruced up the place. Campus Village is co
  campus and was able to see Swagman on the regu
  CV (free for CV residents) just don't park under the
  is nice, and has a clean/useful community center. O
  really recommend it! - 5 years ago
  We collected 2 dorm reviews for Campus Villag
  Browse all 2 dorm reviews
  Verano Place
  based on 1 review
  I’m an undergrad, but was able to live in grad h
  daughter. “New” Verano is much nicer than “old” V
  area, clean, and close to the ARC and shuttle. I wish
  though.
          chunk_id: ratemydorm_uci_dorms_ranked_9
          site: ratemydorm
          created_date: unknown
          filename: ratemydorm_UCI_Dorms_Ranked.txt
          distance: 0.27224963903427124
  }
  --------------------------------------------------
  {
          text: Less of a "Freshman Experience": If you're looking for that classic, chaotic, freshman dorm experience, you
  might not find it here. Beyond the Dorms: Other Housing & Practicalities
  American Campus Communities (ACC)
  UCI also partners with a third-party company called American Campus Communities (ACC) to provide apartment-
  style housing on campus. These communities (like Vista del Campo, Camino del Sol, & Plaza Verde) are generally
  for upperclassmen & graduate students, but occasionally some freshmen might find their way in. These are full-on
  https://prked.com/post/deciphering-the-dorms-an-insiders-guide-to-the-best-housing-at-uc-irvine 6/9
  apartments with your own bedroom (or a shared one), a living room, & a kitchen. They offer a lot of independence
  but can be more expensive & less social for a first-year student. The Parking Predicament
  Now, let's talk about something every UCI student stresses about: parking. Parking on campus is notoriously
  competitive & expensive.
          chunk_id: prked_best_uc_irvine_dorms_middle_earth_vs_mesa_court_guide_11
          site: prked
          created_date: 8/10/25
          filename: prked_Best UC Irvine Dorms_ Middle Earth vs. Mesa Court Guide.txt
          distance: 0.2852713465690613
  }
  --------------------------------------------------
  {
          text: earth classics once and never wanted to come back again. None of the dorms have air conditioning. There was heating but I don't think it ever worked in the room, only in the small common rooms and big room on the first floor (mesa classic). Only ACC apartments have A/C (VDC has free A/C). If you're worried about the distance from classes, just get a cheap bike. Bike theft is very common here so don't spend too much and get a good lock, or park it inside the dorms.
          chunk_id: reddit_first_year_housing_scoop_r_uci_28
          site: reddit
          created_date: unknown
          filename: reddit_first year housing scoop _ r_UCI.txt
          distance: 0.28778499364852905
  }
  --------------------------------------------------
  {
          text: They are privately operated by
  American Campus Communities and located on the east side of campus. Although it is fastest to take
  a shuttle to the campus core, utilities are covered in rent and each apartment comes entirely
  furnished. These apartments are a sure way to get used to luxurious living with their beautiful
  architecture and fabulous pools! While every anteater would surely love to live in these resort-like
  apartments, it is almost like a right of passage. Graduates are the only Irvine students with access to
  the ACC Apartment complexes and maybe that is the only reason they are not ranked first. Advertisement
  #2 “Classic Halls” at Mesa Court
  This is homey, welcoming first year living, the place that makes us little freshman (we have all been
  there) feel like we can actually do this living away from home thing. The Classic Halls at Mesa Court
  have between 48 and 85 beds per hall. There are 6 rooms per each single gender suite and shared
  bathrooms per floor. The Classic Halls contain hall kitchens and living rooms, as well as laundry and
  study rooms. The Classic Hall’s inviting atmosphere is also home to themed housing for freshman to
  get involved in their school and meet new people. I personally love the Classic Hall’s abundance of
  vegetation and thoughtful foliage, it adds a lot to these building’s already peaceful ambiance. Advertisement
  #1 “Towers” at Mesa Court
  Can you say brand-spankin new? The Mesa Court Towers are just that, and you can live in them if
  you are a lucky freshman this coming fall. The Towers are scheduled to be finished just before the
  beginning of the 2016 fall quarter. The three, six story towers contain 275 beds per hall with co-ed
  floors but single gender rooms. This housing option contains a study space on each floor and a great
  room with a kitchen. There are also laundry facilities in each hall. The best part about The Towers is that each will come equip with their own fitness center and
  dining facility! You can eat up your freshman fifteen and then go burn it all off— all without having to
  leave the comfort of your new home. And let’s be honest, everyone loves something new. There is just
  something about knowing you will be the first student to have slept in your room, the first student to
  decorate those walls, and the first student to walk those shiny new halls. It’s magical and exciting to
  be the first at anything your freshman year… we all know there won’t be too many of those
  authoritative moments when you are at the bottom of the totem pole! What is your favorite and least favorite of the UCI dorms? Comment below and share
  this article with friends and students! Featured image source: sustainability.uci.edu, housing.uci.edu
  TAGS CAMPUS (HTTPS://WWW.SOCIETY19.COM/TAG/CAMPUS/) DORMS (HTTPS://WWW.SOCIETY19.COM/TAG/DORMS/)
  UCI (HTTPS://WWW.SOCIETY19.COM/TAG/UCI/) UCI - AROUND CAMPUS (HTTPS://WWW.SOCIETY19.COM/TAG/UCI-AROUND-CAMPUS/)
  UCI AROUND CAMPUS (HTTPS://WWW.SOCIETY19.COM/TAG/UCI-AROUND-CAMPUS/)
  UCI DORM RANKING (HTTPS://WWW.SOCIETY19.COM/TAG/UCI-DORM-RANKING/)
  UCI FRESHMAN TIPS (HTTPS://WWW.SOCIETY19.COM/TAG/UCI-FRESHMAN-TIPS/)
  UCI FRESHMEN (HTTPS://WWW.SOCIETY19.COM/TAG/UCI-FRESHMEN/) UCI STUDENTS (HTTPS://WWW.SOCIETY19.COM/TAG/UCI-STUDENTS/)
  UNIVERSITY OF CALIFORNIA IRVINE (HTTPS://WWW.SOCIETY19.COM/TAG/UNIVERSITY-OF-CALIFORNIA-IRVINE/)
  NICOLE LUSZCZAK (HTTPS://WWW.SOCIETY19.COM/AUTHOR/NICOLE-LUSZCZAK/)
  Nicole is an eighteen year old writer from Southern California. When not writing, she is cooking, reading, or hiking in Malibu. A
  freshman at the University of California, Irvine, Nicole plans on double majoring in Business Administration and Literary
  Journalism. One day she will be the editor in chief of Self Magazine and will live in New York City with her three mini pigs. url=https://www.society19.com/ultimate-ranking-uci- (https://www.facebook.com
   PIN 2dorms/&media=https://i0.wp.com/www.society19.com/wp-  SHARE 0u=https://www.society19.co
  content/uploads/2017/01/UCIDorms.jpg?
          chunk_id: society19_ultimate_ranking_of_uci_dorms_society19_5
          site: society19
          created_date: DECEMBER 5, 2024
          filename: society19_Ultimate Ranking of UCI Dorms - Society19.txt
          distance: 0.2890319228172302
  }
  --------------------------------------------------
  {
          text: the walking is manageable despite what anyone else says. 2. Doubles are fine, but if you can adjust Quads are Best, 1. They are cheapest 3. Bathroom shared by 8 people rather than whole floor with 2 showers and toilets Also cleaned everyday. 4. Most space of all the floor plans 5. Lot of newer rooms and feels, classics feel older and also known to have more bugs and roaches. (Almost none in towers) https://www.reddit.com/r/UCI/comments/1ruj1dt/dorms/
          chunk_id: reddit_dorms_r_uci_6
          site: reddit
          created_date: unknown
          filename: reddit_Dorms _ r_UCI.txt
          distance: 0.29149889945983887
  }
  --------------------------------------------------
  {
          text: which is what most of your buildings will be on (ME towers are like a minute walk from ICS/Engineering lmao) cheapest option yet by a whole marathon the highest quality rooming option. // cons: 4 people to a room (meaning youʼll have 3 roommates!) so if youʼre not used to that it may be a bit of a change lol. also itʼs bunk beds kinda going off the last one but the rooms are well-sized but not massive, so unless youʼve got amazing roommates donʼt expect to be able to sprawl your stuff out tooo
          chunk_id: reddit_first_year_housing_scoop_r_uci_2
          site: reddit
          created_date: unknown
          filename: reddit_first year housing scoop _ r_UCI.txt
          distance: 0.3045780062675476
  }
  --------------------------------------------------
  {
          text: and pippin gym/lounge are practically embedded with the dorms so youʼll have decent physical amenities within reach (mesa has courts too, though I personally like ME layout for this more.) Some building have their bathrooms on the first floor actually have locks (as well as the showers for suites on the bottom floor!) quirky names for each of the buildings which is always fun to joke about. also ME is known for being very STEM-side of campus so if youʼre in that field and donʼt mind it
          chunk_id: reddit_first_year_housing_scoop_r_uci_10
          site: reddit
          created_date: unknown
          filename: reddit_first year housing scoop _ r_UCI.txt
          distance: 0.3064853549003601
  }
  --------------------------------------------------
  {
          text: Unique_County_2236 Where to look for housing Hi everyone, I'm an incoming Masters student starting in the fall. I was accepted after the housing application opened and it looks like I won't be getting on campus or ACC housing. I looked at Facebook groups, but the listings I see are very scammy. UCI's off campus hous portal has a few options but the people I talked to are looking for tenants immediately. I wo be moving to Irvine until September (out of state student).
          chunk_id: reddit_where_to_look_for_housing_r_uci_0
          site: reddit
          created_date: unknown
          filename: reddit_Where to look for housing _ r_UCI.txt
          distance: 0.3065216541290283
  }
  --------------------------------------------------
  {
          text: These can be academic (like Humanities, Chemistry, or Engineering), cultural (like the International House), or
  interest-based (like Culinary Arts or Outdoor Adventure). AV is also home to most of UCI's sorority & fraternity
  houses. Living in AV is a step towards more independent living. You live in a house with 16-32 other students, sharing a full
  kitchen, a living room, & a study room. You're not required to have a meal plan, as you're expected to cook for
  yourself. The Pros of Arroyo Vista:
  Built-in Community: You're living with people who share your interests, which is an amazing way to make
  friends. More Independence: Having your own kitchen & more of an "apartment" feel is a big plus for some students. Usually Quieter: Since it's not a freshman-dominated community, it tends to be a bit more low-key. The Cons of Arroyo Vista:
  Location: AV is on the east side of campus, near the Anteater Recreation Center (the ARC). It's a bit of a walk
  (10-15 minutes) to the main part of campus, though there is a shuttle.
          chunk_id: prked_best_uc_irvine_dorms_middle_earth_vs_mesa_court_guide_10
          site: prked
          created_date: 8/10/25
          filename: prked_Best UC Irvine Dorms_ Middle Earth vs. Mesa Court Guide.txt
          distance: 0.3095179796218872
  }
  --------------------------------------------------
  {
          text: And when it comes to the facilities themselves, there’s much
  less murmurs of discontent among the ranks of the residents
  at the Middle Earth Classics, too. Despite the dated furniture
  on par with those at Mesa Court, the bathrooms seem well
  taken care of, and rooms seem updated with newer carpets,
  as well as wider windows that let in a great amount of natural
  light. https://campusobscura.wordpress.com/2024/06/11/the-best-and-worst-of-ucis-undergrad-on-campus-housing/ 5/15
  Spiro Sun is a third-year who’s called Middle Earth Classics
  home for the past year. Like many of its residents, he’s had a
  middling living experience. “To be honest, it’s a lot less modernized than I expected,” Sun
  says, having got a brief taste of some of the other halls on
  offer at UCI. “I also visited the towers for SPOP (Student
  Parent Orientation Program) and those rooms looked a lot
  nicer. But I can’t complain because it could be a lot worse,
  too.”
  With single- and double-occupancy rooms, the Classics
  represent the most expensive option on-campus. According to
  Sun, those living in single-occupancy rooms can expect to pay
  upwards of an eye-watering $5,500 per quarter. Luckily, for those who aren’t keen on selling away their
  firstborn son to the University of California system, things
  get better. #3- ACC Apartments
  https://campusobscura.wordpress.com/2024/06/11/the-best-and-worst-of-ucis-undergrad-on-campus-housing/ 6/15
  “Living in the apartments is basically just like living in any
  other apartment building. The only difference is that all of
  your neighbors go to school with you,” says Jessica Yang, a
  third-year who was lucky enough to navigate through the
  infamous housing application portal and come out the other
  side with a spot in the Camino del Sol community, one of six
  designed and managed by American Campus Communities-
  the largest such company in the country.
          chunk_id: campusobscura_the_best_and_worst_of_uci_s_undergrad_on_campus_housing_campus_obscura_4
          site: campusobscura
          created_date: 24/06/11
          filename: campusobscura_The Best (and Worst) of UCI’s Undergrad On-Campus Housing – Campus Obscura.txt
          distance: 0.3105281591415405
  }
  --------------------------------------------------
  {
          text: living in ME Classics Phase 2 wasn't bad at all. https://www.reddit.com/r/UCI/comments/1jckpkn/first_year_housing_scoop/ 8/11 Yes there isn't any AC, but none of the on-campus dorms have AC besides maybe the towers, but those aren't specific to the room. Each room does have a heater though. It Create does get hot during the start and end of the school year, but that's what fans and windows are for. The kitchen and laundry situation sucks sometimes, but I realized that I didn't really
          chunk_id: reddit_first_year_housing_scoop_r_uci_30
          site: reddit
          created_date: unknown
          filename: reddit_first year housing scoop _ r_UCI.txt
          distance: 0.31625181436538696
  }
  --------------------------------------------------
  {
          text: of the general layout of the amenities and floorplan. https://www.reddit.com/r/UCI/comments/1oa9vmh/housing_recs_for_second_yr/ However, if you have time, you could just walk through each community and join in o events. I would check their instagrams, while it is also mainly for residents I have see nonresidents there. Plaza Verde I and II difference would be what building you choos to live in, this reddit post should be helpful in getting a geographical idea! There see
          chunk_id: reddit_housing_recs_for_second_yr_r_uci_3
          site: reddit
          created_date: unknown
          filename: reddit_housing recs for second yr _ r_UCI.txt
          distance: 0.31955063343048096
  }
  --------------------------------------------------
  {
          text: expect to be able to sprawl your stuff out tooo much (youʼll still have your own desk/closet ofc) extremely competitive, even if you have 3 other mutually-requested roommates itʼs still a complete lottery (I did this and got a double with one of my requested roommates) https://www.reddit.com/r/UCI/comments/1jckpkn/first_year_housing_scoop/ international / out of state get a touch of priority here iirc so if youʼre in-state itʼs just that much more in the air
          chunk_id: reddit_first_year_housing_scoop_r_uci_3
          site: reddit
          created_date: unknown
          filename: reddit_first year housing scoop _ r_UCI.txt
          distance: 0.32099437713623047
  }
  --------------------------------------------------
  {
          text: better facilities. I also read some reviews on the Middle Earth classics and how they are the worst dorms to live in UCI due to being the oldest and least maintained. Is any of this true or just a myth? Also, for anyone living in quad towers, how is the spacing like and does the room really get that crowded with four people? Are you able to leave your stuff overnight in the shared bathrooms? How many rooms share a bathroom in the classics and can you leave your stuff there?
          chunk_id: reddit_dorm_recommendations_and_application_tips_for_starting_in_uci_as_a_freshman_r_uci_2
          site: reddit
          created_date: unknown
          filename: reddit_Dorm recommendations and application tips for starting in UCI as a freshman _ r_UCI.txt
          distance: 0.3224860429763794
  }
  --------------------------------------------------
  {
          text: college i had never shared my living space with anyone. i was the only one my three roommates who was 1. a complete stranger, and 2. not from the area. i absolutely loved my dorm, my roommates and i got along really well and i never had any of the issues will maintenance that my friends in the classic had. also because the bathroom was shared by only 8 people, everyone was very clean (bc anyone who left a mess could be identified), t staff came once a week to clean our bathroom too!
          chunk_id: reddit_dorms_r_uci_18
          site: reddit
          created_date: unknown
          filename: reddit_Dorms _ r_UCI.txt
          distance: 0.32536381483078003
  }
  --------------------------------------------------

  ```

  </details>

  - **Why these chunks are relevant:** the query mentions "ACC apartments" directly, and the nearest chunks (distances starting ~0.22) are the ones that explicitly discuss ACC communities (Plaza Verde, Vista del Campo, Camino del Sol) and their quality.


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

Example:
- ```Mesa Court is considered more social, but one user disagrees, stating that their hall in Mesa classics is "completely dead" [sources: reddit_Dorms _ r_UCI.txt]. Middle Earth is known for being social, with a lively common room and many activities [sources: reddit_Dorms _ r_UCI.txt, prked_Best UC Irvine Dorms_ Middle Earth vs. Mesa Court Guide.txt]. Quieter dorms are not explicitly mentioned, but Middle Earth classics are noted for being older and potentially quieter [sources: reddit_first year housing scoop _ r_UCI.txt].```

- ```You should expect utility bills, which can range from $40-70, and laundry costs, with one load of laundry (wash & dry) costing around $4 [sources: reddit_housing recs for second yr _ r_UCI.txt]. Additionally, if you have a car, you may need to pay for parking, including a parking fee to park at your apartment complex [sources: reddit_housing recs for second yr _ r_UCI.txt].```

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
