# apartment-review-frontend

This template should help get you started developing with Vue 3 in Vite.

## Production stack

| Layer | Service | Plan |
|---|---|---|
| Frontend (this repo) | Cloudflare Pages | Free tier |
| API | DigitalOcean App Platform | `apps-s-1vcpu-0.5gb` — $5/mo |
| Database | Neon (managed Postgres) | Free tier — `aws-ap-southeast-1` |

Cloudflare Pages builds this repo directly (`npm run build`, serving `dist/`) and deploys the API
(`apartment-review-fastapi`) to DigitalOcean, built straight from that repo's `Dockerfile`.

All three production services are defined as code in **`infra/`** — a Pulumi (TypeScript)
program living in this repo since it's the TS one, even though it also provisions the backend and
database. See `infra/README.md` for the one-time GitHub authorizations, API tokens/secrets to
configure, and `pulumi up` / `pulumi destroy`.

**Before real users hit this:** the frontend calls a hardcoded relative `/api/apartments`
(`src/stores/apartment.ts`) rather than reading the `VITE_API_URL` the Pulumi program sets, and
the backend has no CORS middleware yet — cross-origin requests from the deployed frontend will
fail until both are fixed.

## Local stack (Docker Compose)

`docker-compose.yml` in this folder runs all three local services — Postgres, the FastAPI
backend (built from `../apartment-review-fastapi`), and this frontend. See `DOCKER_GUIDE.md` for
the actual port mapping (frontend on 5273, backend on 8100, Postgres on 5532 — not the container
-internal ports the guide used to say).

## Recommended IDE Setup

[VS Code](https://code.visualstudio.com/) + [Vue (Official)](https://marketplace.visualstudio.com/items?itemName=Vue.volar) (and disable Vetur).

## Recommended Browser Setup

- Chromium-based browsers (Chrome, Edge, Brave, etc.):
  - [Vue.js devtools](https://chromewebstore.google.com/detail/vuejs-devtools/nhdogjmejiglipccpnnnanhbledajbpd)
  - [Turn on Custom Object Formatter in Chrome DevTools](http://bit.ly/object-formatters)
- Firefox:
  - [Vue.js devtools](https://addons.mozilla.org/en-US/firefox/addon/vue-js-devtools/)
  - [Turn on Custom Object Formatter in Firefox DevTools](https://fxdx.dev/firefox-devtools-custom-object-formatters/)

## Type Support for `.vue` Imports in TS

TypeScript cannot handle type information for `.vue` imports by default, so we replace the `tsc` CLI with `vue-tsc` for type checking. In editors, we need [Volar](https://marketplace.visualstudio.com/items?itemName=Vue.volar) to make the TypeScript language service aware of `.vue` types.

## Customize configuration

See [Vite Configuration Reference](https://vite.dev/config/).

## Project Setup

```sh
npm install
```

### Compile and Hot-Reload for Development

```sh
npm run dev
```

### Type-Check, Compile and Minify for Production

```sh
npm run build
```
