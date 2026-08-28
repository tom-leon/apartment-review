import * as pulumi from "@pulumi/pulumi";
import * as digitalocean from "@pulumi/digitalocean";
import * as cloudflare from "@pulumi/cloudflare";
// Neon has no first-party npm package; it's generated locally from its Terraform
// provider. Run this once before `pulumi up` (see README):
//   pulumi package add terraform-provider kislerdm/neon
// That command adds "@pulumi/neon" to package.json and node_modules for you.
import * as neon from "@pulumi/neon";

const cfg = new pulumi.Config();

// --- repo / branch locations -------------------------------------------------
const githubOwner = cfg.get("githubOwner") ?? "yilin-chao";
const backendRepo = cfg.get("backendRepo") ?? "apartment-review-fastapi";
const frontendRepo = cfg.get("frontendRepo") ?? "apartment-review-vue";
const backendBranch = cfg.get("backendBranch") ?? "main";
const frontendBranch = cfg.get("frontendBranch") ?? "main";

// --- sizing / region -----------------------------------------------------------
// apps-s-1vcpu-0.5gb = $5/mo (cheapest real DO App Platform tier, Aug 2026 pricing).
const doInstanceSize = cfg.get("doInstanceSize") ?? "apps-s-1vcpu-0.5gb";
// DO App Platform has no Sydney region; sgp (Singapore) is the closest to AU.
const doRegion = cfg.get("doRegion") ?? "sgp";

// --- secrets -------------------------------------------------------------------
// Set these with:
//   pulumi config set --secret digitalocean:token <token>
//   pulumi config set --secret cloudflare:apiToken <token>
//   pulumi config set --secret neonApiKey <key>
const cloudflareAccountId = cfg.require("cloudflareAccountId");
const neonApiKey = cfg.requireSecret("neonApiKey");
const neonOrgId = cfg.require("neonOrgId");

// =================================================================================
// 1. Neon — managed Postgres
// =================================================================================

const neonProvider = new neon.Provider("neon-provider", {
  apiKey: neonApiKey,
});

const neonProject = new neon.Project(
  "apartment-review-db",
  {
    name: "apartment-review",
    pgVersion: 16,
    regionId: "aws-ap-southeast-1", // Singapore — pairs with the DO app region above
    orgId: neonOrgId,
  },
  { provider: neonProvider },
);

const neonDatabase = new neon.Database(
  "apartment-review-app-db",
  {
    projectId: neonProject.id,
    branchId: neonProject.defaultBranchId,
    name: "apartment_review",
    ownerName: "neondb_owner",
  },
  { provider: neonProvider },
);

// Full connection string, kept secret end-to-end.
const databaseUrl = pulumi.secret(neonProject.connectionUri);

// =================================================================================
// 2. DigitalOcean App Platform — FastAPI backend, built from the repo's Dockerfile
// =================================================================================

const backendApp = new digitalocean.App("apartment-review-backend", {
  spec: {
    name: "apartment-review-backend",
    region: doRegion,
    services: [
      {
        name: "api",
        github: {
          repo: `${githubOwner}/${backendRepo}`,
          branch: backendBranch,
          deployOnPush: true,
        },
        dockerfilePath: "Dockerfile",
        httpPort: 8000,
        instanceCount: 1,
        instanceSizeSlug: doInstanceSize,
        envs: [
          {
            key: "DATABASE_URL",
            value: databaseUrl,
            type: "SECRET",
          },
        ],
        healthCheck: {
          httpPath: "/",
          initialDelaySeconds: 10,
          periodSeconds: 10,
        },
      },
    ],
  },
});

// =================================================================================
// 3. Cloudflare Pages — Vue frontend, built from the repo directly
// =================================================================================

const frontendProject = new cloudflare.PagesProject("apartment-review-frontend", {
  accountId: cloudflareAccountId,
  name: "apartment-review",
  productionBranch: frontendBranch,
  buildConfig: {
    buildCommand: "npm run build",
    destinationDir: "dist",
    rootDir: "",
  },
  source: {
    type: "github",
    config: {
      owner: githubOwner,
      repoName: frontendRepo,
      productionBranch: frontendBranch,
      deploymentsEnabled: true,
    },
  },
  deploymentConfigs: {
    production: {
      environmentVariables: {
        VITE_API_URL: backendApp.liveUrl,
      },
    },
  },
});

// =================================================================================
// Outputs
// =================================================================================

export const backendUrl = backendApp.liveUrl;
export const frontendUrl = frontendProject.domains;
export const databaseConnectionString = databaseUrl;
