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

**The cost of not doing this plan:** today the site can't show a single review to anyone. The "Post review" button logs to the browser console and throws the review away ([HomeView.vue:52](apartment-review-vue/src/views/HomeView.vue#L52)). There is nothing to lure anyone with, and nothing a visitor could ever come back to.

## What's true today (checked 2026-11-04)

| Area | Fact | Evidence |
|---|---|---|
| Reading | No endpoint returns a review. The home page can list addresses but the fetch is commented out | [HomeView.vue:44](apartment-review-vue/src/views/HomeView.vue#L44), [main.py:28-46](apartment-review-fastapi/main.py#L28-L46) |
| Writing | Modal collects address, optional unit number, 4 slider ratings (0–100), text; submit only console-logs | [CreateReviewModal.vue:38-53](apartment-review-vue/src/components/CreateReviewModal.vue#L38-L53), [HomeView.vue:52](apartment-review-vue/src/views/HomeView.vue#L52) |
| Drafted but unused | Read/create endpoints for apartments and reviews already exist in a file nobody imports, with `user_uid` taken from the request instead of a login | [example_endpoints.py:69-162](apartment-review-fastapi/example_endpoints.py#L69-L162), [example_endpoints.py:114](apartment-review-fastapi/example_endpoints.py#L114) |
| Users | `User` has a plaintext `password` column and a public `POST /user` that creates accounts for anyone | [models.py:15](apartment-review-fastapi/models.py#L15), [main.py:28](apartment-review-fastapi/main.py#L28) |
| Ratings mismatch | Model stores ratings 1–10; UI collects 0–100 on a slider | [models.py:103-112](apartment-review-fastapi/models.py#L103-L112), [CreateReviewModal.vue:38](apartment-review-vue/src/components/CreateReviewModal.vue#L38) |
| Schema drift | `ReviewCreate` has a `value_rating` the model doesn't have; `calculate_apartment_average_rating` averages `Review.rating`, a column that doesn't exist (would crash if called) | [schemas.py:106](apartment-review-fastapi/schemas.py#L106), [utils.py:158](apartment-review-fastapi/utils.py#L158) |
| Route naming | `main.py` uses singular `/user`, `/apartment`; the drafted file uses plural `/apartments`, `/reviews`; the store calls `/api/apartments` | [main.py:37](apartment-review-fastapi/main.py#L37), [example_endpoints.py:69](apartment-review-fastapi/example_endpoints.py#L69), [apartment.ts:19](apartment-review-vue/src/stores/apartment.ts#L19) |
| Frontend → API URL | Store hardcodes `/api/apartments`. `.env.development` sets `API_URL`, but Vite only exposes variables prefixed `VITE_`, so the app can't read it. Pulumi sets `VITE_API_URL` in production | [apartment.ts:19](apartment-review-vue/src/stores/apartment.ts#L19), [.env.development](apartment-review-vue/.env.development), [index.ts:129](infra/index.ts#L129) |
| CORS | No CORS middleware, so the deployed frontend (Cloudflare) can't call the deployed API (DigitalOcean) | [README.md:51](apartment-review-fastapi/README.md#L51) |
| One review per person per apartment | Already enforced by a unique constraint | [models.py:80](apartment-review-fastapi/models.py#L80) |
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

Not in this plan, on purpose: migrations (nothing is deployed, see [ci-cd-plan.md](ci-cd-plan.md)); pre-rendering for SEO (Phase 4, item 6); property-manager replies (Phase 4, item 5).

---

## Phase 1 — Reading works (the public lure)

**Outcome:** search an address on the home page, land on that apartment's page, see its averages and reviews. Nothing to sign in to yet.

### Backend
- [ ] Add `CORSMiddleware` to `main.py`: origins = `http://localhost:5173` plus the Cloudflare Pages URL, `allow_credentials=True` (needed in Phase 2 for the cookie). Explicit origins, never `*`.
- [ ] Rename `POST /apartment` → `POST /apartments/from-osm` taking `OSMAddressData` (what Nominatim actually returns) and calling the existing `get_or_create_apartment` ([utils.py:9](apartment-review-fastapi/utils.py#L9)). Same address picked twice = same apartment row. Delete the old raw-fields endpoint and its two tests; write two new ones (creates; returns existing on repeat).
- [ ] `GET /apartments/{uid}` → address fields + `review_count` + the four averages, published reviews only. One query with `func.avg`. Delete the broken `calculate_apartment_average_rating` ([utils.py:151](apartment-review-fastapi/utils.py#L151)).
  Test: apartment with 2 published + 1 pending review → count 2, averages ignore the pending one.
- [ ] `GET /apartments/{uid}/reviews` → published only, newest first. Response shape per decision 9 (no identity fields).
- [ ] `GET /apartments?q=smith` → apartments whose `display_name` contains the text, case-insensitive, limit 20. Also `GET /apartments/recent` → the 10 apartments with the newest published review (for the home page).
- [ ] Move what's left of `example_endpoints.py` into `main.py` (or a `routers/` folder if `main.py` passes ~150 lines) and delete the example file.

### Frontend
- [ ] `.env.development`: rename `API_URL` → `VITE_API_URL=http://localhost:8000`. Store: build URLs from `import.meta.env.VITE_API_URL`. Delete `createApartment` (replaced by from-osm) and `getApartmentById` (unused).
- [ ] Home page: replace the bare address `DataTable` **and** the "Review an apartment" button with one address `AutoComplete` (move the Nominatim call out of the modal into a `useAddressSearch` composable; the modal no longer searches, see decision 14). Keep the whole Nominatim result object, not just `display_name`, because `from-osm` needs its fields. Picking a result → `POST /apartments/from-osm` → `router.push('/apartments/<uid>')`.
- [ ] Home page below the search: "Recently reviewed" `DataTable` from `GET /apartments/recent` (address, average score, review count), rows link to the apartment page.
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
- [ ] `uv add google-auth itsdangerous` (`SessionMiddleware` needs `itsdangerous` to sign the cookie).
- [ ] `config.py`: read `GOOGLE_CLIENT_ID` and `SESSION_SECRET` from the environment. ⚠️ BLOCKING for deploy: add both to the DigitalOcean app's env list in [index.ts](infra/index.ts) and set them as Pulumi secrets; add `VITE_GOOGLE_CLIENT_ID` to the Cloudflare env.
- [ ] `User`: delete `password`; add `google_sub: str` (unique, indexed) — Google's permanent id for the account; emails can change, this can't. Delete `POST /user`, `UserCreate`, and their two tests.
- [ ] `verify_google_token(credential: str) -> dict` as a FastAPI dependency wrapping `google.oauth2.id_token.verify_oauth2_token(credential, google.auth.transport.requests.Request(), GOOGLE_CLIENT_ID)`. Tests override it with a function returning `{"sub": "123", "email": ..., "name": ...}` (decision 13).
- [ ] `POST /auth/google` body `{ "credential": "<id token>" }` → verify → find user by `sub` or create one → `request.session["user_uid"] = str(user.uid)` → return `UserResponse`.
- [ ] `current_user` dependency: reads the session, loads the user, raises 401 when missing. Two tests.
- [ ] `GET /auth/me` → current user or 401. `POST /auth/logout` → clear session.
- [ ] `SessionMiddleware(secret_key=SESSION_SECRET, https_only=True in prod, same_site="lax")`.

### Frontend
- [ ] `index.html`: load `https://accounts.google.com/gsi/client`. New Pinia store `auth.ts`: `user`, `fetchMe()` (called once in `App.vue` on mount), `loginWithGoogle(credential)` → `POST /auth/google`, `logout()`. Every API `fetch` gets `credentials: "include"`.
- [ ] `App.vue`: a PrimeVue `Toolbar` header: site name left; right side either the Google button (rendered by `google.accounts.id.renderButton` into a `div`) or "Hi <first name>" + a "Sign out" `Button`.
- [ ] Modal gate: on "Post review", if `auth.user` is null, show a `Message` "Sign in to post. Your name is never shown with your review." with the Google button under it; the form keeps its values. When `auth.user` becomes set, the "Post review" button is enabled again and the next click submits.
- [ ] Vitest: `auth` store `fetchMe` 401 → `user` stays null; modal shows the sign-in message when logged out and the submit emits when logged in.

**How this connects:** Phase 1's "Review this apartment" button opens the modal; this phase makes the modal's "Post review" demand a login; Phase 3 makes that post actually save.

---

## Phase 3 — Posting for real, with the check-before-publish queue

**Outcome:** a signed-in person posts a review, sees it marked "awaiting check" on the apartment page, and it appears publicly once an admin publishes it from an admin page.

### Backend
- [ ] `Review`: ratings `ge=0, le=100`; delete `title`; add `lived_in_year: int`, `status: str = "pending"`, `published_at: datetime | None`. Delete `value_rating` from `schemas.py`.
- [ ] `POST /reviews` (needs `current_user`): body = `apartment_uid`, four ratings, `content`, `lived_in_year`; `user_uid` from the session, never from the body. 404 unknown apartment; 409 if this user already reviewed it (keep the drafted logic from [example_endpoints.py:109](apartment-review-fastapi/example_endpoints.py#L109)).
- [ ] `PUT /reviews/{uid}` (owner only, else 403): edits put it back to `pending`.
- [ ] `GET /apartments/{uid}/reviews`: published ones, plus the caller's own pending/rejected one if logged in (flagged with `status`; still no identity fields).
- [ ] Admin: `is_admin` on `User`; `require_admin` dependency; `GET /admin/reviews?status=pending`; `POST /admin/reviews/{uid}/publish` (sets `published_at`) and `/reject`.

### Frontend
- [ ] Modal: remove unit number; add "Year you lived here" (`Select` of the last 30 years). `handleSubmit` → `POST /reviews` → `Toast` "Thanks. Your review goes live once we've checked it." 409 → "You've already reviewed this place — edit your review instead".
- [ ] Apartment page: the caller's own review shows first with a `Tag` "Awaiting check" / "Rejected" and an Edit button that reopens the modal filled in.
- [ ] `/admin` route (guard: redirect home unless `auth.user.is_admin`): `DataTable` of pending reviews with address, text, Publish / Reject buttons.
- [ ] Vitest: modal emits the right payload; admin route guard redirects a non-admin.

---

## Phase 4 — Features that bring people back (ranked by payoff ÷ effort)

| # | Feature | Why it earns its place | Size | Login? |
|---|---|---|---|---|
| 1 | **Browse by suburb + map** (Leaflet with OpenStreetMap tiles, free). `GET /apartments/nearby` is already drafted ([example_endpoints.py:83](apartment-review-fastapi/example_endpoints.py#L83)) | Turns "look up one address" into "explore where I'm moving to". The second reason to visit | M | No |
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
3. **Ratings scale** (decision 6): store 0–100 to match the slider, or keep 1–10?
4. **Test rule** (decision 13): OK to swap the Google verifier with a dependency override in tests, or do you want something else?
5. **Railway-Oriented Programming.** [apartment-review-fastapi/CLAUDE.md:6](apartment-review-fastapi/CLAUDE.md#L6) says "Always use Railway-Oriented Programming with the `returns` library" (every service function returns a `Success`/`Failure` value instead of raising, and the endpoint maps a `Failure` to the HTTP error). Nothing in the repo does this yet and `returns` isn't installed. Does the rule still stand for the ~12 endpoints and 3 dependencies this plan adds? It decides the shape of every handler, so it has to be settled before Phase 1 starts. Default: follow the rule.

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
