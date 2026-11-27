# Next features plan — apartment-review (Vue + FastAPI)

**Goal:** a stranger who Googles an address lands on that apartment's page, reads every review without signing in, and is asked to sign in with Google only at the moment they press "Post review". Reading is free forever; writing and personal features need an account.

**Tech stack (unchanged):** Vue 3 + PrimeVue 4 + Pinia + vue-router · FastAPI + SQLModel + Postgres (Neon) · Google Identity Services for login · Nominatim (OpenStreetMap address search).

**Spec:** the *Why*, *What's true today* and *Decisions* sections of this file, plus [VISION.md](VISION.md).

---

## Why — and the answer to "is gating the reading bad for growing the user base?"

**Yes, at this stage it is bad. Don't gate reading.** Three reasons:

1. **You already decided this.** [VISION.md:4](VISION.md#L4) says "Free-to-browse, login-to-post. All reviews are public to maximize SEO." The "give them something public, then make them log in to see the rest" idea contradicts your own vision doc, and the vision doc is right.
2. **A wall before the content costs you the visitors you're trying to win.** Pinterest's growth team tested a sign-up prompt you couldn't dismiss: those users had lower retention, and the gap kept widening over time ([Pinterest Engineering](https://medium.com/@Pinterest_Engineering/lessons-in-growth-and-increasing-signups-d6e7d8fef479)). Quora walled everything behind registration and had to back off after complaints ([Adweek](https://www.adweek.com/?p=347039)). Google also ranks what it can read: pages hidden behind a login don't rank, and the whole vision is "found via Google" ([GGV Capital](https://medium.com/@GGVCapital/to-wall-or-not-to-wall-the-user-sign-up-question-3caa2a729adc)).
3. **The sites that do gate reading (Glassdoor, openigloo) gate it behind *writing a review*, not behind *logging in*, and only because they already have a mountain of content to unlock.** Glassdoor's own study says the "give to get" rule makes ratings less extreme ([PR Newswire](https://prnewswire.com/news-releases/new-study-reveals-glassdoor-give-to-get-policy-leads-to-more-balanced-company-ratings-300534547.html)); openigloo makes you submit one review to unlock the rest ([openigloo blog](https://blog.openigloo.com/6-ways-to-use-openigloo-during-your-nyc-apartment-search/)). You have zero reviews. There is nothing to unlock, so a wall today just bounces people. Revisit "write one to see the rest" as an experiment once there are thousands of reviews (Phase 4, item 9).

**So what does login gate?** The things that are *about the user*: posting a review, editing it, voting "helpful", saving an apartment, reporting a review. That's the model of Yelp, Google Maps and Zillow, and it's the one that grows.

**The cost of not doing this plan:** today the site can't show a single review to anyone. The "Post review" button logs to the browser console and throws the review away ([HomeView.vue:54](apartment-review-vue/src/views/HomeView.vue#L54)). There is nothing to lure anyone with, and nothing a visitor could ever come back to.

## What's true today (checked 2026-11-04)

| Area | Fact | Evidence |
|---|---|---|
| Reading | Changed 2026-11-16: `GET /apartments/recent` lists apartments that have a published review, and the home page shows them as cards. Changed 2026-11-28: `GET /apartments/{uid}/reviews` returns one apartment's published reviews. Still no endpoint for one apartment's averages, and no page that shows its reviews | [main.py:73](apartment-review-fastapi/main.py#L73), [reviews.py:57](apartment-review-fastapi/routers/reviews.py), [HomeView.vue:50](apartment-review-vue/src/views/HomeView.vue#L50) |
| Writing | Modal collects address, optional unit number, 4 slider ratings (0–100), text. Changed 2026-11-28: "Post review" saves the review for the signed-in user (`pending` until checked); the unit number is still on the form but is not saved | [CreateReviewModal.vue:146](apartment-review-vue/src/components/CreateReviewModal.vue#L146), [review.ts:40](apartment-review-vue/src/stores/review.ts#L40), [reviews.py:43](apartment-review-fastapi/routers/reviews.py) |
| Drafted but unused | Changed 2026-11-28: the review endpoints moved into `routers/reviews.py` and take the user from the sign-in. `example_endpoints.py` deleted 2026-11-28; `GET /apartments/{uid}` is still to build (Phase 1) | [routers/](apartment-review-fastapi/routers/) |
| Users | Changed 2026-11-16: the plaintext `password` column and the public `POST /user` are gone. `User` now carries `google_sub`, Google's permanent id for the account. Changed 2026-11-27: `POST /auth/google` creates the user on first sign-in and starts a session cookie; `GET /auth/me` and `POST /auth/logout` exist. Changed 2026-11-28: posting, editing and deleting a review require sign-in | [routers/auth.py](apartment-review-fastapi/routers/auth.py), [main.py](apartment-review-fastapi/main.py) |
| Ratings mismatch | Changed 2026-11-16: `Review` ratings are 0–100, same as the slider (decision 6). Changed 2026-11-28: `ReviewCreate` is 0–100 too | [models/review.py](apartment-review-fastapi/models/review.py), [schemas.py:79-93](apartment-review-fastapi/schemas.py#L79-L93), [CreateReviewModal.vue:38](apartment-review-vue/src/components/CreateReviewModal.vue#L38) |
| Schema drift | Changed 2026-11-28: `value_rating` is gone from `ReviewCreate`. `calculate_apartment_average_rating` still averages `Review.rating`, a column that doesn't exist (would crash if called) | [utils.py:194](apartment-review-fastapi/controllers/reviews.py) |
| Route naming | `main.py` still has the singular `POST /apartment` next to the new plural routes; the store's two older functions call `/api/apartments`, which does not exist | [main.py:52](apartment-review-fastapi/main.py#L52), [apartment.ts:56](apartment-review-vue/src/stores/apartment.ts#L56) |
| Frontend → API URL | Store hardcodes `/api/apartments`. `.env.development` sets `API_URL`, but Vite only exposes variables prefixed `VITE_`, so the app can't read it. Pulumi sets `VITE_API_URL` in production | [apartment.ts:56](apartment-review-vue/src/stores/apartment.ts#L56), [.env.development](apartment-review-vue/.env.development), [index.ts:129](infra/index.ts#L129) |
| CORS | No CORS middleware, so the deployed frontend (Cloudflare) can't call the deployed API (DigitalOcean) | [README.md:51](apartment-review-fastapi/README.md#L51) |
| One review per person per apartment | Already enforced by a unique constraint | [models/review.py](apartment-review-fastapi/models/review.py) |
| Deployed? | Nothing is deployed yet, so schema changes are free today (no migrations needed until production has data) | [ci-cd-plan.md](ci-cd-plan.md) |

## The journey after this plan

```
Google: "12 Smith St Newtown review"
  └─ /apartments/<uid>  (public, no login)
       ├─ address · 4 average star ratings · review count
       ├─ every published review: "Lived here in 2023" · 4 scores out of 100 · text
       └─ [Review this apartment]
            └─ modal (already built) → [Post review]
                 ├─ logged in  → POST /reviews → "Thanks. It goes live once we've checked it."
                 └─ logged out → Google sign-in popup inside the modal, form stays filled
                                  → logged in → same click posts
```

Terms used once: **SPA** = single-page app, a site whose HTML is empty until JavaScript runs (what Vite + Vue builds). **ID token** = the signed note Google hands the browser after sign-in saying "this is account X"; our server checks Google's signature on it. **Session cookie** = a small signed cookie our server sets after that check, so later requests know who you are. **CORS** = the browser rule that stops site A's JavaScript calling site B's API unless B says it's allowed.

## Decisions

| # | Decision | Why | Alternative |
|---|---|---|---|
| 1 | Reading never needs login | See *Why* above | — |
| 2 | **Google only.** No X/Twitter. Apple later only if an iOS app ships | X had ~7% of social logins when Google had 31% in the last share data I found ([MarketingCharts](https://www.marketingcharts.com/interactive/in-q4-google-gained-in-social-logins-at-facebooks-expense-26065/)); today about half of tracked apps offer Google sign-in ([Lazyweb](https://www.lazyweb.com/research/how-many-apps-offer-sign-in-with-google.md)). Apple needs a paid developer account and only becomes compulsory inside an App Store app | Add Apple when there's an iOS app |
| 3 | **Login = Google's "Sign in with Google" button (popup) + our API verifies the ID token** with Google's `google-auth` Python library | No page reload, so a half-written review isn't lost. About 20 lines on the backend. Nothing else to configure | Server redirect flow with Authlib ([Authlib guide](https://blog.authlib.org/2020/fastapi-google-login)): standard, but the page unloads, so the draft must be stashed in `sessionStorage` and restored |
| 4 | **Session = signed HTTP-only cookie** via Starlette's `SessionMiddleware` | No session table, no JWT library, 3 lines. The cookie can't be read by JavaScript, so a script injection can't steal it | JWT in a header: works cross-site without cookie fuss, but the token sits in JavaScript-readable storage |
| 5 | **Delete `User.password` and `POST /user`.** Users are created by signing in, never by a public endpoint | Social-only login means there is no password to hash, store or leak. Fixes the README's "plaintext passwords" gap by removing the column | Keep email + password alongside Google (needs hashing, reset emails, a lot more surface) |
| 6 | **Ratings stored 0–100.** Change the model's `ge=1, le=10` to `ge=0, le=100` | The UI is a 0–100 slider (changed 2026-11-08). Storing 1–10 means a made-up conversion in both directions | Keep 1–10 and divide by 10 |
| 7 | **Drop `value_rating` and `title`.** Keep the 4 ratings the UI asks for and `content` | Schema has fields the model and UI don't; a title field nobody fills is clutter | Add both to model and UI |
| 8 | **Review `status`: pending → published / rejected. Publishing is a manual admin click, no timer** | [VISION.md:16](VISION.md#L16) wants a 24–48h cooling-off *so someone can screen it*. Manual publish *is* the screening; a timer on top is extra code for no extra safety | Auto-publish after 48h unless rejected (needs a scheduled job) |
| 9 | **Public review responses carry no identity**: no `user_uid`, no name, no email. Only ratings, text, "Lived here in <year>" | [VISION.md:7-10](VISION.md#L7-L10): identity decoupled from display | — |
| 10 | **Remove the unit-number field from the modal** | It has no column today, and a unit number plus a year identifies a tenant to their landlord — exactly what [VISION.md:10](VISION.md#L10) says to avoid | Keep it and add a column (never shown publicly) |
| 11 | **Plural routes everywhere**: `/apartments`, `/reviews`, `/auth/...`. No `/api` prefix (the API is its own host) | The drafted endpoints and the store are already plural; `main.py` is the odd one out | — |
| 12 | **Admin = `is_admin` bool on `User`, set by hand in the DB** | Smallest possible moderation: one flag, one page | Separate admin table / roles |
| 13 | **Tests swap the Google verifier through `app.dependency_overrides`**, the same way `get_db` is already swapped in [conftest.py](apartment-review-fastapi/tests/conftest.py) | Verifying a real ID token needs Google's public keys over the network. The backend rules ban mocking libraries; a FastAPI dependency override is the framework's own switch, not a mock | Hit Google for real in tests (flaky, needs a real token) |
| 14 | **The review modal has one entry point: the apartment page.** It takes `apartmentUid` + `address` props; the address search lives only on the home page | Two entry points (home button and apartment page) means a modal with two modes, a two-step submit from the home path (create apartment, then review), and double the login-gate and edit-mode tests. One entry point is half the component | Keep the home-page button and let the modal search too |
| 15 | **Backend code style: pending Open question 5.** Default if unanswered: follow the backend rule and use `returns` | The rule is written in [apartment-review-fastapi/CLAUDE.md:6](apartment-review-fastapi/CLAUDE.md#L6), but no existing code follows it and the library isn't installed | Plain FastAPI style, as the existing code and the drafted endpoints are written |
| 16 | **Card photos: Google Street View, loaded by the visitor's browser.** The API hands out one `photo_url` per apartment, built from the address and the `GOOGLE_MAPS_API_KEY` setting; no key or no photo = a placeholder | OpenStreetMap has no photos. Google has one for nearly every Australian address and aims it at the building. 10,000 photos a month are free; 4 cards = about 2,500 home-page visits. Changing the photo source later only touches the API | Mapillary: free, but many streets have no photo and most look down the road |

Not in this plan, on purpose: migrations (nothing is deployed, see [ci-cd-plan.md](ci-cd-plan.md)); pre-rendering for SEO (Phase 4, item 6); property-manager replies (Phase 4, item 5).

---

## Phase 1 — Reading works (the public lure)

**Outcome:** search an address on the home page, land on that apartment's page, see its averages and reviews. Nothing to sign in to yet.

### One-time setup for the card photos
- [ ] Google Cloud console → enable **Street View Static API** → create an API key.
  - Limit the key to this site's address (website restriction) and to that one API. The key is readable in every photo address.
  - Set a daily quota of about 300 photos, so a month can never pass the free 10,000.
- [ ] Give the API the key as `GOOGLE_MAPS_API_KEY`. ⚠️ Needed for photos in production: add it to the DigitalOcean app's env list in [index.ts](infra/index.ts) as a Pulumi secret.
- Google's rules for these photos: they stay on Google's servers (no copies), the "Google Maps" label stays on the photo, and no non-Google map on the same screen.

### Backend
- [ ] Add `CORSMiddleware` to `main.py`: origins = `http://localhost:5173` plus the Cloudflare Pages URL, `allow_credentials=True` (needed in Phase 2 for the cookie). Explicit origins, never `*`.
- [ ] Rename `POST /apartment` → `POST /apartments/from-osm` taking `OSMAddressData` (what Nominatim actually returns) and calling the existing `get_or_create_apartment` ([utils.py:14](apartment-review-fastapi/controllers/reviews.py)). Same address picked twice = same apartment row. Delete the old raw-fields endpoint and its two tests; write two new ones (creates; returns existing on repeat).
  - Done 2026-11-28: `POST /apartments/from-osm` and its two tests ([main.py:61](apartment-review-fastapi/main.py#L61)). Still to do: delete the old `POST /apartment` and its two tests.
- [ ] `GET /apartments/{uid}` → address fields + `review_count` + the four averages, published reviews only. One query with `func.avg`. Delete the broken `calculate_apartment_average_rating` ([utils.py:163](apartment-review-fastapi/controllers/reviews.py)).
  Test: apartment with 2 published + 1 pending review → count 2, averages ignore the pending one.
- [x] `GET /apartments/{uid}/reviews` → published only, newest first. Response shape per decision 9 (no identity fields). Done 2026-11-28 ([reviews.py:57](apartment-review-fastapi/routers/reviews.py)).
- [ ] `GET /apartments?q=smith` → apartments whose `display_name` contains the text, case-insensitive, limit 20.
- [x] `GET /apartments/recent?limit=` (1–20, default 10) → apartments with the newest published review first, for the home page. Done 2026-11-16.
  - Each one: address fields, `review_count`, `average_score` (0–100), `latest_review_text`, `photo_url`. No identity fields (decision 9).
  - Needed `Review.status` early (default `pending`), see Phase 3.
- [x] `seed.py`: sample data for a local database, so pages have something to show before sign-in and posting exist. Done 2026-11-16.
  - 5 sample reviewers, 6 apartments, 10 reviews (9 published, 1 pending). Street names are made up on purpose.
  - Run: `cd apartment-review-fastapi && uv run python seed.py`. A second run adds nothing; it refuses a database that is not on this machine.
- [x] Routes live in `routers/`, the work they call in `controllers/`, tables in `models/`; `example_endpoints.py` deleted. Done 2026-11-28.

### Frontend
- [ ] `.env.development`: rename `API_URL` → `VITE_API_URL=http://localhost:8000`. Store: build URLs from `import.meta.env.VITE_API_URL`. Delete `createApartment` (replaced by from-osm) and `getApartmentById` (unused).
- [ ] Home page: replace the bare address `DataTable` **and** the "Review an apartment" button with one address `AutoComplete` (move the Nominatim call out of the modal into a `useAddressSearch` composable; the modal no longer searches, see decision 14). Keep the whole Nominatim result object, not just `display_name`, because `from-osm` needs its fields. Picking a result → `POST /apartments/from-osm` → `router.push('/apartments/<uid>')`.
- [x] Home page: "Recently reviewed" cards from `GET /apartments/recent?limit=4`, in place of the bare address `DataTable`. Done 2026-11-16 (decision 16).
  - Each card: street photo or a placeholder, address, score out of 100, review count, the newest review's text.
  - 4 across on a computer, one per row on a phone.
  - Still open: a card opens the apartment page, once that page exists (next bullet).
- [ ] New route `/apartments/:uid` → `ApartmentView.vue`: address as `h1`; a `Card` with the four averages as `ProgressBar`s (0–100) + "(n reviews)"; one `Card` per review showing "Lived here in <year>", four `ProgressBar`s, text; a `Message` empty state "No reviews yet — be the first"; a "Review this apartment" `Button` opening the existing modal, which now takes `apartmentUid` and `address` props and shows the address as plain text (decision 14).
- [ ] Vitest: store test for `fetchApartment(uid)` happy path and error path; `ApartmentView` renders the empty state.

**How this connects:** the apartment page is the thing Google indexes and the thing people share. Phase 2 adds the one button on it that needs a login.

---

## Phase 2 — Google login, asked for only when posting

**Outcome:** a visitor can press "Post review" without an account; they get a Google popup inside the modal, the form keeps what they typed, and after the popup the same click posts.

### One-time setup (must be done before any of this runs)
- [ ] Google Cloud console → APIs & Services → Credentials → OAuth client ID, type **Web**. Authorised JavaScript origins: `http://localhost:5173` and the production frontend URL. Copy the client ID. (A client secret is not needed for this flow.)
- [ ] Decide the cookie question (Open question 1 below): same-site domain, or cross-site cookie.

### Backend
- [x] `uv add "google-auth[requests]" itsdangerous` (`SessionMiddleware` needs `itsdangerous` to sign the cookie; `requests` is only an extra of `google-auth` and the verifier's transport needs it). Done 2026-11-27.
- [x] `config.py`: read `GOOGLE_CLIENT_ID`, `SESSION_SECRET` and `SESSION_HTTPS_ONLY` from the environment. Unset: sign-in answers 503; a new random secret each start (cookies can never be forged, logins just stop surviving a restart); no `Secure` flag on the cookie. Done 2026-11-27.
- [ ] ⚠️ BLOCKING for deploy: add `GOOGLE_CLIENT_ID`, `SESSION_SECRET` and `SESSION_HTTPS_ONLY=true` to the DigitalOcean app's env list in [index.ts](infra/index.ts), the first two as Pulumi secrets; add `VITE_GOOGLE_CLIENT_ID` to the Cloudflare env.
- [x] `User`: delete `password`; add `google_sub: str` (unique, indexed) — Google's permanent id for the account; emails can change, this can't. Delete `POST /user`, `UserCreate`, and their two tests. `email` is no longer unique: Google's guide says not to treat an email as the identifier.
- [x] `verify_google_token` as a FastAPI dependency in `controllers/auth.py` (routes in `routers/auth.py`): reads `{"credential": ...}` through `GoogleCredential`, wraps `google.oauth2.id_token.verify_oauth2_token(credential, google.auth.transport.requests.Request(), GOOGLE_CLIENT_ID)`; 401 when Google rejects the token, 503 when no client ID is set. Tests swap it through the `google_accounts` fixture in `tests/conftest.py` (decision 13). Done 2026-11-27.
- [x] `POST /auth/google` body `{ "credential": "<id token>" }` → verify → find user by `sub` or create one → `request.session["user_uid"] = str(user.uid)` → return `UserResponse`. Name falls back to the email when Google sends none; a repeat sign-in reuses the row and copies nothing over it. Done 2026-11-27.
- [x] `current_user` dependency (`main.py`): reads the session, loads the user, 401 when there is no session, a forged cookie or a deleted user. Done 2026-11-27.
- [x] `GET /auth/me` → current user or 401. `POST /auth/logout` → clear session (204). Done 2026-11-27.
- [x] `SessionMiddleware(secret_key=SESSION_SECRET, https_only=SESSION_HTTPS_ONLY, same_site="lax")`, added before CORS so CORS stays outermost. Done 2026-11-27. ⚠️ `lax` only works while site and API share one domain (open question 1): with today's `*.pages.dev` + `*.ondigitalocean.app` the browser never sends the cookie to the API, so sign-in looks fine but `GET /auth/me` answers 401.
- [x] Proven 2026-11-28 in the local Docker stack with a real Google account: sign-in 200, `/auth/me` 200, logout 204, `/auth/me` 401. On the way: the backend Dockerfile ignored `uv.lock` and pulled a newer SQLModel that rejects the models' naive datetimes (503 on any save in Docker); fixed by installing the locked versions ([Dockerfile](apartment-review-fastapi/Dockerfile)). `docker-compose.yml` now passes `GOOGLE_CLIENT_ID` through.

### Frontend
- [x] `index.html`: load `https://accounts.google.com/gsi/client` (`defer`, so it is ready before the app runs). New Pinia store `auth.ts`: `user`, `fetchMe()` (called once in `App.vue` on mount), `loginWithGoogle(credential)` → `POST /auth/google`, `logout()`. The auth store's fetches send the cookie (`credentials: "include"`); the apartment store's reads do not need it yet, Phase 3's `POST /reviews` will. `VITE_GOOGLE_CLIENT_ID` in `.env.development`. Done 2026-11-28.
- [x] `App.vue`: a PrimeVue `Toolbar` header: site name left; right side either the Google button (`components/GoogleSignIn.vue`, rendered by `google.accounts.id.renderButton` into a `div`; says so when Google's script did not load) or "Hi <first name>" + a "Sign out" `Button`. Done 2026-11-28.
- [x] Modal gate: on "Post review", if `auth.user` is null, show a `Message` "Sign in to post. Your name is never shown with your review." with the Google button under it; the form keeps its values. When `auth.user` becomes set the message goes and the next click submits. Done 2026-11-28.
- [x] Vitest: 13 new tests (auth store 4, GoogleSignIn 3, App header 3, modal gate 3); `npm test` 31 passed, `npm run type-check` and `npm run build-only` clean (Node 22, per `.nvmrc`). Done 2026-11-28.
- [ ] Unproven in a browser: the header button and the modal gate with a real Google account (`npm run dev` on :5173 against the Docker API on :8100).

**How this connects:** Phase 1's "Review this apartment" button opens the modal; this phase makes the modal's "Post review" demand a login; Phase 3 makes that post actually save.

---

## Phase 3 — Posting for real, with the check-before-publish queue

**Outcome:** a signed-in person posts a review, sees it marked "awaiting check" on the apartment page, and it appears publicly once an admin publishes it from an admin page.

### Backend
- [ ] `Review`: ratings `ge=0, le=100`; delete `title`; add `lived_in_year: int`, `status: str = "pending"`, `published_at: datetime | None`. Delete `value_rating` from `schemas.py`.
  - Done early, 2026-11-16: ratings 0–100 and `status` (the home page cards needed both). The rest is open.
- [x] `POST /reviews` (needs `current_user`): body = `apartment_uid`, four ratings, `content`; `user_uid` from the session, never from the body. 404 unknown apartment; 409 if this user already reviewed it. Done 2026-11-28 ([reviews.py:43](apartment-review-fastapi/routers/reviews.py)). `lived_in_year` is not in it yet; it comes with the `Review` change above.
- [x] `PUT /reviews/{uid}` (owner only, else 403): edits put it back to `pending`. Done 2026-11-28: loaded in the app, user from `current_user` ([reviews.py:67](apartment-review-fastapi/routers/reviews.py)).
- [x] `DELETE /reviews/{uid}` (owner only, else 403): removes the review for good, answers 204. Done 2026-11-28, same as the PUT ([reviews.py:87](apartment-review-fastapi/routers/reviews.py)).
- [ ] `GET /apartments/{uid}/reviews`: published ones, plus the caller's own pending/rejected one if logged in (flagged with `status`; still no identity fields).
- [ ] Admin: `is_admin` on `User`; `require_admin` dependency; `GET /admin/reviews?status=pending`; `POST /admin/reviews/{uid}/publish` (sets `published_at`) and `/reject`.

### Frontend
- [ ] Modal: remove unit number; add "Year you lived here" (`Select` of the last 30 years). `handleSubmit` → `POST /reviews` → `Toast` "Thanks. Your review goes live once we've checked it." 409 → "You've already reviewed this place — edit your review instead".
  - Done 2026-11-28: "Post review" → `POST /apartments/from-osm` → `POST /reviews`, a thank-you message on the home page, an error message in the form on failure ([review.ts:40](apartment-review-vue/src/stores/review.ts#L40)). Still to do: remove unit number, add the year.
- [ ] Apartment page: the caller's own review shows first with a `Tag` "Awaiting check" / "Rejected" and an Edit button that reopens the modal filled in.
- [ ] `/admin` route (guard: redirect home unless `auth.user.is_admin`): `DataTable` of pending reviews with address, text, Publish / Reject buttons.
- [ ] Vitest: modal emits the right payload; admin route guard redirects a non-admin.

---

## Phase 4 — Features that bring people back (ranked by payoff ÷ effort)

| # | Feature | Why it earns its place | Size | Login? |
|---|---|---|---|---|
| 1 | **Browse by suburb + map** (Leaflet with OpenStreetMap tiles, free). The suburb list works off `city`/`postcode`; the map pins need `latitude`/`longitude` back on `Apartment` (removed 2026-11-16) | Turns "look up one address" into "explore where I'm moving to". The second reason to visit | M | No |
| 2 | **"Was this helpful?"** vote on a review | Cheap engagement, sorts good reviews up, and a gentle reason to sign in | S | Yes |
| 3 | **Save an apartment + email when a new review is published** | The retention loop: the site comes back to the user. Needs an email provider (Resend or Mailgun free tier). This is the right kind of login gate | M | Yes |
| 4 | **Report a review** → lands in the admin queue | Lets readers do the moderation legwork; needed before any real traffic | S | Yes |
| 5 | **Right of reply for property managers** ([VISION.md:19](VISION.md#L19)) | Balance, and a reason for the other side to visit. Hard part is proving a manager really manages that building | L | Yes |
| 6 | **Pre-render apartment pages** (vite-ssg, or move to Nuxt) | The vision is "maximise SEO", but the page Google fetches today is an empty `<div id="app">`; Google does run JavaScript, but slower and less reliably than plain HTML | M–L | No |
| 7 | **Share buttons + Open Graph tags** (the title/image a link shows on WhatsApp, Facebook) | Word of mouth between renters. Only works after item 6: link-preview crawlers don't run JavaScript | S | No |
| 8 | **Photos on reviews** | Strong proof, but storage cost, moderation load, and a photo of a specific unit identifies the tenant. Not before 4 and 5 exist | L | Yes |
| 9 | **"Write one to see the breakdown" experiment** (openigloo style) | Only once there are thousands of reviews, as an A/B test on the detailed breakdown, never on the whole page | S | — |

**Don't build:** rating named agents or landlords (defamation risk, [VISION.md:13](VISION.md#L13)); password login; X/Twitter login.

---

## Open questions (each changes what gets built)

1. **Cookie site.** The login cookie is only sent automatically when the frontend and API are on the same site (same registered domain, e.g. `example.com` + `api.example.com`). Today they're `*.pages.dev` and `*.ondigitalocean.app`, two different sites. Options: (a) buy a domain and point both at it (my recommendation; it also fixes the ugly URLs), or (b) set the cookie `SameSite=None; Secure` and keep two sites (works, but Safari and Brave restrict such cookies). Which?
2. **Unit number** (decision 10): drop it, or keep it as a never-shown column?
3. **Ratings scale** (decision 6): store 0–100 to match the slider, or keep 1–10? → Went with 0–100 on 2026-11-16 (the cards show a score out of 100). Still easy to flip: nothing is stored yet.
4. **Test rule** (decision 13): OK to swap the Google verifier with a dependency override in tests, or do you want something else?
5. **Railway-Oriented Programming.** [apartment-review-fastapi/CLAUDE.md:6](apartment-review-fastapi/CLAUDE.md#L6) says "Always use Railway-Oriented Programming with the `returns` library" (every service function returns a `Success`/`Failure` value instead of raising, and the endpoint maps a `Failure` to the HTTP error). Nothing in the repo does this yet and `returns` isn't installed. Does the rule still stand for the ~12 endpoints and 3 dependencies this plan adds? It decides the shape of every handler, so it has to be settled before Phase 1 starts. Default: follow the rule. → Followed the default on 2026-11-16: `returns` is installed and `GET /apartments/recent` uses it.

## Research sources
- Pinterest, forced sign-up modal lowers retention: https://medium.com/@Pinterest_Engineering/lessons-in-growth-and-increasing-signups-d6e7d8fef479
- Quora softens its registration wall: https://www.adweek.com/?p=347039
- Walls and search traffic (GGV Capital): https://medium.com/@GGVCapital/to-wall-or-not-to-wall-the-user-sign-up-question-3caa2a729adc
- Nielsen Norman Group on login walls: https://www.nngroup.com/articles/login-walls/
- Glassdoor's give-to-get study (self-reported): https://prnewswire.com/news-releases/new-study-reveals-glassdoor-give-to-get-policy-leads-to-more-balanced-company-ratings-300534547.html
- openigloo: submit one review to unlock: https://blog.openigloo.com/6-ways-to-use-openigloo-during-your-nyc-apartment-search/
- Australian rental review sites (Rent Rabbit pays $30 per review and charges to read; Property Reviewed, Rate My Rental are free): https://www.moneymag.com.au/rental-property-reviews-online-tools
- Social login share, Google vs Twitter: https://www.marketingcharts.com/interactive/in-q4-google-gained-in-social-logins-at-facebooks-expense-26065/
- Apps offering Google sign-in (2026 tracker): https://www.lazyweb.com/research/how-many-apps-offer-sign-in-with-google.md
- FastAPI auth options compared: https://workos.com/blog/top-authentication-solutions-fastapi-2026
- Authlib's Google login for FastAPI (the alternative in decision 3): https://blog.authlib.org/2020/fastapi-google-login
