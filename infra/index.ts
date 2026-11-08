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
const githubOwner = cfg.get("githubOwner") ?? "tom-leon";
const githubRepo = cfg.get("githubRepo") ?? "apartment-review";
const branch = cfg.get("branch") ?? "main";

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

// Cloudflare Pages serves production at https://<project name>.pages.dev. Deriving the
// origin from the name (instead of reading it off the Pages resource) avoids a cycle:
// the Pages build needs the backend's URL, and the backend needs the Pages origin.
const pagesProjectName = "apartment-review";
const frontendOrigin = `https://${pagesProjectName}.pages.dev`;

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
          repo: `${githubOwner}/${githubRepo}`,
          branch,
          deployOnPush: false,
        },
        sourceDir: "apartment-review-fastapi",
        dockerfilePath: "apartment-review-fastapi/Dockerfile",
        httpPort: 8000,
        instanceCount: 1,
        instanceSizeSlug: doInstanceSize,
        envs: [
          {
            key: "DATABASE_URL",
            value: databaseUrl,
            type: "SECRET",
          },
          {
            key: "CORS_ORIGINS",
            value: frontendOrigin,
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
  name: pagesProjectName,
  productionBranch: branch,
  buildConfig: {
    buildCommand: "npm run build",
    destinationDir: "dist",
    rootDir: "apartment-review-vue",
  },
  source: {
    type: "github",
    config: {
      owner: githubOwner,
      repoName: githubRepo,
      productionBranch: branch,
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
export const backendAppId = backendApp.id;
export const frontendUrl = frontendProject.domains;
export const databaseConnectionString = databaseUrl;
