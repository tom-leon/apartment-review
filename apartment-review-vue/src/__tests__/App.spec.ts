import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { flushPromises, mount } from "@vue/test-utils";
import { createPinia } from "pinia";
import { createMemoryHistory, createRouter } from "vue-router";
import PrimeVue from "primevue/config";
import App from "../App.vue";

const tom = { uid: "u1", name: "Tom Leon", email: "tom@example.com" };

/** Stand in for the API: /auth/me answers as given, everything else is an empty list. */
function apiAnswers(me: { status: number; body: unknown }) {
  const requests: { url: string; method: string }[] = [];
  vi.stubGlobal("fetch", async (url: string, init?: RequestInit) => {
    requests.push({ url, method: init?.method ?? "GET" });
    if (url.endsWith("/auth/me")) return new Response(JSON.stringify(me.body), me);
    if (url.endsWith("/auth/logout")) return new Response(null, { status: 204 });
    return new Response("[]", { status: 200 });
  });
  return requests;
}

async function mountApp() {
  const router = createRouter({
    history: createMemoryHistory(),
    routes: [{ path: "/", component: { template: "<div />" } }],
  });
  const app = mount(App, { global: { plugins: [createPinia(), PrimeVue, router] } });
  await flushPromises();
  return app;
}

describe("App header", () => {
  beforeEach(() => {
    vi.stubEnv("VITE_API_URL", "https://api.example.com");
    vi.stubGlobal("google", {
      accounts: { id: { initialize: () => {}, renderButton: () => {} } },
    });
  });

  afterEach(() => {
    vi.unstubAllGlobals();
    vi.unstubAllEnvs();
  });

  it("greets the signed-in user by first name with a sign-out button", async () => {
    const requests = apiAnswers({ status: 200, body: tom });

    const app = await mountApp();

    expect(requests).toContainEqual({ url: "https://api.example.com/auth/me", method: "GET" });
    expect(app.find("header").text()).toContain("Hi Tom");
    expect(app.find("header button").text()).toBe("Sign out");
    expect(app.find(".google-button").exists()).toBe(false);
  });

  it("shows the Google button when nobody is signed in", async () => {
    apiAnswers({ status: 401, body: { detail: "Sign in first" } });

    const app = await mountApp();

    expect(app.find(".google-button").exists()).toBe(true);
    expect(app.find("header").text()).not.toContain("Hi ");
  });

  it("signing out tells the API and brings the Google button back", async () => {
    const requests = apiAnswers({ status: 200, body: tom });
    const app = await mountApp();

    await app.find("header button").trigger("click");
    await flushPromises();

    expect(requests).toContainEqual({
      url: "https://api.example.com/auth/logout",
      method: "POST",
    });
    expect(app.find(".google-button").exists()).toBe(true);
  });
});
