# Roadmap — apartment-review

The order everything gets built in, and why. The other three docs each cover one slice:

- [VISION.md](VISION.md) — the product thinking (anonymity, defamation, right of reply)
- [ci-cd-plan.md](ci-cd-plan.md) — how code gets tested and deployed
- [next-features-plan.md](next-features-plan.md) — the step-by-step detail for stages 1–3 and 5 below

This file adds the **AI stages (4, 6, 7)** and puts all of it in one sequence. Stage detail for the AI work lives here; the rest links out.

## Where things stand (checked 2026-11-08)

| Area | State | Evidence |
|---|---|---|
| Frontend | Home page + review dialog exist; "Post review" only logs to the console | [HomeView.vue](apartment-review-vue/src/views/HomeView.vue) |
| Backend | Three routes: create user, create apartment, health check. No review endpoint, no login, no CORS | [main.py:28-46](apartment-review-fastapi/main.py#L28-L46), [README.md:50](apartment-review-fastapi/README.md#L50) |
| CI | Lint, tests and a Docker build run on every push, for both halves. No deploy step yet | [backend.yml](.github/workflows/backend.yml), [frontend.yml](.github/workflows/frontend.yml) |
| Deployed | Nothing. No real data yet, so schema changes are still free | [ci-cd-plan.md](ci-cd-plan.md) |
| AI | Nothing built yet; stages 4, 6 and 7 below are the plan. The vision has one line on it | [VISION.md:16](VISION.md#L16) |

## The sequence

| # | Stage | Outcome | Why here | Size | Detail |
|---|---|---|---|---|---|
| 0 | Ship the pipeline | Push to `main` runs tests and deploys | Everything after this needs a place to run | M | [ci-cd-plan.md](ci-cd-plan.md) |
| 1 | Reading works | An apartment page anyone can read, no login | The public lure; nothing to moderate until people can read | M | [Phase 1](next-features-plan.md#L81) |
| 2 | Google login | Asked for only when you press "Post review" | Posting needs an identity; a login is the first spam filter | M | [Phase 2](next-features-plan.md#L105) |
| 3 | Posting + manual queue | Reviews land in a `pending` queue; an admin publishes or rejects by hand | Human-only screening is the baseline the AI gets measured against | M | [Phase 3](next-features-plan.md#L133) |
| **4** | **AI moderation** | Clean reviews publish themselves; spam, abuse, defamation and leaked personal details wait for a human, with the reason shown | Must exist before real traffic: the queue from stage 3 doesn't scale past a few reviews a day, and an unchecked defamatory review is the legal risk in the vision | M | below |
| 5 | Bring people back | Suburb map, "helpful" votes, save + email, report a review, right of reply, pre-rendering | Traffic and content; only worth it once posting is safe | L | [Phase 4](next-features-plan.md#L153) |
| **6** | **AI on the reading side** | Each review tagged by issue (mould, pests, bond…); each apartment gets a short "what tenants say" summary; browse by issue | Needs reviews to exist first (stage 5); turns a list of reviews into an answer | M | below |
| **7** | **AI writing help** | While writing, the dialog suggests a safer rewrite ("the agent John lied" → "the agent didn't return calls about the heater for 3 weeks") | Fixes defamation at the keyboard, not after; fewer reviews end up waiting for a human | S–M | below |

Not scheduled yet: semantic search over reviews, translation, photo checks, auto-reject. See *Later*.

---

## Stage 4 — AI moderation

**Why.** [VISION.md:16](VISION.md#L16) wants every review screened before it goes live. Stage 3 does that with a human reading each one, which means either every tenant waits a day to see their review appear, or reviews go live unread. The AI reads each review in seconds, publishes the clean ones and queues the rest with a reason. The human only reads the queue.

**Cost of not doing it.** A review that names an agent and accuses them of theft goes live because nobody got to the queue that day. That is the one thing the vision says must not happen.

### Free checks first, the model second

Plain code catches the cheap stuff before any API call, so the model only sees judgement calls:

- Logged in with Google (stage 2) and one review per person per apartment (already enforced: [models.py:80](apartment-review-fastapi/models.py#L80))
- At most 5 reviews per person per day
- Length between 20 and 3,000 characters
- Any `http://` or `https://` link in the text → rejected on the spot, with the message "links aren't allowed"

### What the model checks

One call per review, one structured answer. The model returns a verdict per check plus the exact words that tripped it, so the admin page can highlight them.

| Check | What trips it | Verdict |
|---|---|---|
| Spam | Ads, "DM me for cheap rentals", gibberish, the same text already posted on another apartment | hold |
| Abuse | Slurs, threats, sexual content, heavy swearing (a mild "bloody" is fine) | hold |
| Names a person or accuses them of a crime | "The agent John Smith stole my bond" | hold (defamation) |
| Personal details | Phone numbers, emails, a unit number, the tenant's own name, a landlord's name | hold, and tell the tenant which bit |
| Not a review | "Is this unit still available?", a review clearly about a different address | hold |
| Clean | Everything else | publish |

### How it flows

```
POST /reviews  (stage 3, unchanged)
  └─ review saved with status = "pending"
  └─ response returns straight away: "Thanks. It goes live once we've checked it."
  └─ background task starts after the response is sent
       └─ free checks (above)
       └─ one Claude call → row in review_moderation (verdict, flags, quoted words, model id)
            ├─ every check clean  → status = "published", published_at = now
            └─ anything flagged   → status stays "pending"
                                     admin page (stage 3) now shows WHY, with the words highlighted
                                     admin: Publish / Reject, exactly as in stage 3
```

### Decisions

| # | Decision | Why | Alternative |
|---|---|---|---|
| 1 | **The AI never rejects on its own.** It publishes or holds; only a human rejects | A wrong auto-reject silently loses a real tenant's review. A wrong hold costs the admin one click | Auto-reject spam once stored verdicts show the AI and the admin agree 95%+ of the time (see *Later*) |
| 2 | **Clean reviews publish immediately, no 24–48 hour timer** | The vision's cooling-off exists "to allow AI or manual screening". The screening now takes seconds, so the wait has nothing left to wait for. Replaces [decision 8](next-features-plan.md#L68) in the features plan | Keep a 24h delay as a safety net on top of the AI pass |
| 3 | **The check runs in a FastAPI `BackgroundTasks` job after the response is sent**, never inside the request | The model call takes a few seconds; the tenant shouldn't sit on a spinner. If Anthropic is down, the review simply stays `pending` for the human queue. In plain words: when the AI can't answer, nothing publishes (fail-closed, our own code, not an API feature) | A queue worker (Celery, RQ). More moving parts than one background task deserves at this traffic |
| 4 | **Model: `claude-opus-5-5` through the official `anthropic` Python SDK**, with structured output so the answer arrives as a Pydantic object, never as prose to parse | Anthropic's current default model. Structured output means no "the model wrote JSON with a typo" bugs | `claude-haiku-5-5` is roughly 40× cheaper per review. Switch only if volume ever makes cost matter, not before |
| 5 | **Store every verdict** in a new `review_moderation` table: `review_uid`, `verdict`, `flags` (JSON), `quoted_spans` (JSON), `model`, `created_at` | The admin page shows *why* a review was held. It is also the dataset that tells you later whether the AI is any good (how often the admin overrides it). Storing the model id means you can tell which model made which call after an upgrade | Store only the verdict on `Review` |
| 6 | **Only the review text and star ratings go to the API.** Never the user's name, email or uid | Same principle as the vision: identity stays decoupled from content. Also keeps the privacy note short: "review text is checked by an AI service before publishing" | — |
| 7 | **Tests swap the moderation function with `app.dependency_overrides`**, the same switch the Google verifier uses ([decision 13](next-features-plan.md#L73)). The prompt itself is checked by a folder of ~30 example reviews with expected verdicts, run by hand against the real API (costs cents), not in CI | The backend rule bans mocking libraries; the dependency override is FastAPI's own switch. CI must never need an API key or network | Record-and-replay HTTP fixtures (VCR). Brittle whenever the request body changes |

**Cost per review** (about 1,000 input tokens for the prompt + review, 150 output tokens):

| Model | Per review | 1,000 reviews/month |
|---|---|---|
| `claude-opus-5-5` | ~$0.007 | ~$7 |
| `claude-haiku-5-5` | ~$0.0002 | ~$0.20 |

**Needed before stage 4 deploys:** an `ANTHROPIC_API_KEY` secret on the DigitalOcean app, injected the same way `DATABASE_URL` is. Nothing in this stage runs in production without it.

### Build order

1. The Pydantic model for the moderation answer (one bool per check in the table above, plus the quoted words), and the pure function `decide(result) -> "published" | "pending"`. Tests first, then the function.
2. The free checks, as a plain function with no network.
3. The Claude call and the `review_moderation` table, behind a FastAPI dependency so tests can swap it.
4. The background task wiring in `POST /reviews`.
5. The admin page: reason and highlighted words per held review, plus the false-positive rate ("of the reviews the AI held in the last 7 days, how many did the admin then publish?").

---

## Stage 6 — AI on the reading side

**Why.** Ten reviews of one building is a wall of text. A new renter wants the answer: is the landlord responsive, is there mould, does the bond come back. Tags and a summary give the answer in five seconds, and give Google unique text per page (the vision's SEO goal).

- **Tags per review.** Added to the stage 4 call, so no extra API cost: the model picks up to 5 tags from a fixed list (mould, pests, noise, slow repairs, bond, heating/cooling, water pressure, parking, management, security, natural light). Stored on `Review` as a JSON array. Fixed list, not free text, because free text fragments ("mold", "mould", "damp") and can't be filtered.
- **Summary per apartment.** When a review is published and the apartment has 3 or more published reviews, regenerate a 3-bullet "What tenants say" and 3-bullet "Watch out for", stored on `Apartment` with `summary_updated_at`. Regenerated on publish, not on page view, so the apartment page stays a plain database read. The prompt only allows claims at least one review makes, and the page labels it "AI summary of N reviews".
- **Browse by issue.** `GET /apartments?tag=mould`, a filter on the stage 5 suburb map. "Mentioned by 4 of 7 reviewers" next to each tag on the apartment page.

First query to write: "top 5 tags across all published reviews in postcode 2042, with counts". It drives both the suburb filter and the per-apartment "mentioned by N of M".

---

## Stage 7 — AI writing help

**Why.** [VISION.md:13](VISION.md#L13) says the writing experience should steer people to describe the property, not the person. Stage 4 catches "the agent John is a liar" after the fact; this catches it while the cursor is still in the box, and the tenant fixes it themselves. Fewer holds means less admin time.

- A "Check my review" button in the dialog calls `POST /reviews/check-draft` (login required, 10 per person per hour). It reuses stage 4's prompt and schema, plus one extra field: a suggested rewrite that keeps the facts and drops the names and accusations.
- The dialog shows the flagged words and the rewrite; the tenant accepts it or ignores it. Nothing is changed without a click.
- Same call flags a star/text mismatch: "Your review reads negative but you gave 5 stars. Is that right?"

Mostly frontend work, since the backend is stage 4's function behind a second route.

---

## Later (not scheduled, each needs a reason to move up)

- **Auto-reject spam** once `review_moderation` shows the AI's "spam" hold matches the admin's reject 95%+ of the time over at least 100 reviews.
- **Right-of-reply moderation.** Property-manager replies (stage 5) go through the stage 4 pipeline unchanged.
- **Photo checks** for photos on reviews (stage 5, item 8): the same API with the image attached, holding photos that show faces, documents, or a visible unit number.
- **Semantic search** ("places near Newtown station with responsive landlords"): needs pgvector on Neon and an embedding per review. Only worth it with thousands of reviews.
- **Translate a review on demand**, cached per language.

## Not on the roadmap, on purpose

- AI-written or AI-"improved" reviews that change the facts. Fake content is what the site exists to fight; stage 7 only rewrites phrasing and only with a click.
- A sentiment score replacing the stars.
- A chatbot on the site.
- Rating named agents or landlords ([VISION.md:13](VISION.md#L13)).

## Still deciding

1. **Monthly API budget.** Decides Opus vs Haiku in stage 4 decision 4. Current answer: Opus 5.5 (~$7 per 1,000 reviews) until real volume says otherwise.
2. **Cooling-off.** Publish clean reviews the moment the AI passes them (decision 2), or keep a 24h delay as a safety net? Current answer: immediately.
