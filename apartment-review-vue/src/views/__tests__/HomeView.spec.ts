import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { flushPromises, mount } from "@vue/test-utils";
import { createPinia } from "pinia";
import PrimeVue from "primevue/config";
import HomeView from "../HomeView.vue";
import CreateReviewModal from "@/components/CreateReviewModal.vue";
import type { RecentApartment } from "@/stores/apartment";

function reviewed(uid: string, street: string): RecentApartment {
  return {
    uid,
    house_number: "12",
    street,
    city: "Melbourne",
    state: "Victoria",
    postcode: "3065",
    display_name: `12, ${street}, Melbourne, Victoria, 3065, Australia`,
    review_count: 2,
    average_score: 72,
    latest_review_text: "Great light, but repairs took six weeks.",
    photo_url: null,
  };
}

/** Stand in for the API: answer every request with this status and JSON body. */
function apiAnswers(status: number, body: unknown) {
  const requested: string[] = [];
  vi.stubGlobal("fetch", async (url: string) => {
    requested.push(url);
    return new Response(JSON.stringify(body), { status });
  });
  return requested;
}

async function mountHome() {
  const home = mount(HomeView, { global: { plugins: [createPinia(), PrimeVue] } });
  await flushPromises();
  return home;
}

describe("HomeView", () => {
  beforeEach(() => {
    vi.stubEnv("VITE_API_URL", "https://api.example.com");
  });

  afterEach(() => {
    vi.unstubAllGlobals();
    vi.unstubAllEnvs();
  });

  it("shows a card for each recently reviewed apartment, in the API's order", async () => {
    const requested = apiAnswers(200, [
      reviewed("a1", "Brunswick Street"),
      reviewed("a2", "Glebe Point Road"),
    ]);

    const home = await mountHome();

    expect(requested).toEqual(["https://api.example.com/apartments/recent?limit=4"]);
    expect(home.find("h2").text()).toBe("Recently reviewed");
    expect(home.findAll(".address").map((address) => address.text())).toEqual([
      "12 Brunswick Street",
      "12 Glebe Point Road",
    ]);
  });

  it("has no “Recently reviewed” section when nothing has been reviewed", async () => {
    apiAnswers(200, []);

    const home = await mountHome();

    expect(home.find("h2").exists()).toBe(false);
  });

  it("says so when the recent reviews cannot be loaded", async () => {
    apiAnswers(503, { detail: "Reviews are unavailable right now" });

    const home = await mountHome();

    expect(home.find(".p-message-error").text()).toContain("could not be loaded");
    expect(home.find("h2").exists()).toBe(false);
  });

  it("thanks the reviewer once their review is posted", async () => {
    apiAnswers(200, []);
    const home = await mountHome();
    expect(home.find(".p-message-success").exists()).toBe(false);

    await home.findComponent(CreateReviewModal).vm.$emit("submit");
    await flushPromises();

    expect(home.find(".p-message-success").text()).toContain(
      "Thanks. Your review goes live once we’ve checked it.",
    );
  });
});
