# Infra — Pulumi (TypeScript)

## Secrets

Decision: use Pulumi secrets, not a separate secret manager (Vault, GCP Secret Manager, 1Password
CLI, etc.) — those add real value at team/multi-service scale (rotation, audit logs, access
control), which doesn't apply to a one-person project with one secret. `neonProject.connectionUri`
is wrapped in `pulumi.secret()` and passed to the DigitalOcean app as `type: "SECRET"`
([index.ts](index.ts)), so the DB URL is encrypted in Pulumi state and injected straight into the
DO app — nobody hand-types it into the DO dashboard.

Lives at the repo root and provisions both apps:

- **Neon** — managed Postgres (`apartment-review` project + `apartment_review` database)
- **DigitalOcean App Platform** — the FastAPI backend, built straight from `apartment-review-fastapi`'s `Dockerfile`
- **Cloudflare Pages** — the Vue frontend, built from `apartment-review-vue`

All three providers are first-party/official in Pulumi's registry, so this is one `pulumi up`
with no Terraform-bridge hacks — except Neon, which ships as a dynamically-generated provider
(see step 2 below).

## One-time manual setup (can't be done from Pulumi)

1. **DigitalOcean ↔ GitHub.** DO's App Platform needs its GitHub App authorized on your account
   before it will let Pulumi deploy from a repo. In the DO control panel: Apps → Create App →
   GitHub → authorize, and grant it access to `apartment-review`. You can cancel out of
   the wizard once it's authorized — Pulumi will do the actual app creation.
2. **Cloudflare ↔ GitHub.** Same idea: Pages → Create a project → Connect to Git, authorize once,
   then cancel — Pulumi will create the actual project.
3. Get a **DigitalOcean API token** (API → Generate New Token, full read/write).
4. Get a **Cloudflare API token** (My Profile → API Tokens → Create Token, needs `Cloudflare
   Pages:Edit` and `Account Settings:Read`) and your **Cloudflare account ID** (right sidebar of
   any zone's Overview page, or Account Home URL).
5. Get a **Neon API key** (Neon console → Account settings → API keys) and your **Neon org ID**
   (Neon console → Settings, or `npx neonctl orgs list` after `npx neonctl auth`).

## Install

```bash
cd infra
npm install
# Neon has no plain npm package — this generates a local SDK from its Terraform provider
# and adds "@pulumi/neon" to package.json/node_modules for you:
pulumi package add terraform-provider kislerdm/neon
```

## Configure

```bash
pulumi stack init dev   # if you haven't already

pulumi config set cloudflareAccountId <your-cloudflare-account-id>
pulumi config set neonOrgId <your-neon-org-id>

pulumi config set --secret digitalocean:token <your-do-token>
pulumi config set --secret cloudflare:apiToken <your-cloudflare-token>
pulumi config set --secret neonApiKey <your-neon-api-key>
```

Defaults for everything else (repo names, branch, region, instance size) live in
`Pulumi.dev.yaml` — override any of them with `pulumi config set <key> <value>` if needed.

## Deploy

```bash
pulumi preview   # see what it would create, no changes made
pulumi up        # actually create Neon project + DO app + Cloudflare Pages project
```

```bash
pulumi stack output backendUrl                              # DO app's live URL
pulumi stack output frontendUrl                              # Cloudflare Pages domain(s)
pulumi stack output databaseConnectionString --show-secrets  # Neon connection string
```

## Two things this program does NOT fix — do these before pointing real users at it

1. **CORS.** The frontend and backend end up on different origins (`*.pages.dev` /
   `*.ondigitalocean.app`), and `main.py` has no `CORSMiddleware`. Add one, scoped to the actual
   Pages domain — not `allow_origins=["*"]`, since these endpoints will eventually carry
   credentials.
2. **The frontend doesn't read `VITE_API_URL` yet.** This program sets it as a Cloudflare Pages
   build-time env var, but `src/stores/apartment.ts` currently calls a hardcoded relative
   `/api/apartments`. Change it to read `import.meta.env.VITE_API_URL`, or the env var this
   program wires up does nothing.

## Cost at this sizing

- DigitalOcean App Platform (`apps-s-1vcpu-0.5gb`): **$5/mo**
- Cloudflare Pages: **$0** (free tier, no commercial-use restriction)
- Neon (`aws-ap-southeast-1`, free tier): **$0** until you outgrow 0.5 GB storage / 100 CU-hours

**~$5/mo total** to start, growing only as Neon usage crosses the free tier.

## Tearing down

```bash
pulumi destroy
```

Deletes the DO app, the Cloudflare Pages project, and the Neon project (including the database —
back it up first if there's real data in it).
