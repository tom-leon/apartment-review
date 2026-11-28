import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { createPinia, setActivePinia } from "pinia";
import { apiUrl, useApartmentStore, type RecentApartment } from "../apartment";

describe("apartment store", () => {
  beforeEach(() => {
    setActivePinia(createPinia());
  });

  it("finds an apartment the app already knows", () => {
    const store = useApartmentStore();
    store.apartments = [
      { uid: "a1", address: "1 Test St" },
      { uid: "a2", address: "2 Test St" },
    ];

    expect(store.getApartmentById("a2")).toEqual({ uid: "a2", address: "2 Test St" });
  });

  it("finds nothing for an apartment the app does not know", () => {
    const store = useApartmentStore();

    expect(store.getApartmentById("nope")).toBeUndefined();
  });
});

describe("the address of the server", () => {
  afterEach(() => {
    vi.unstubAllEnvs();
  });

  it("uses the server address from the settings when there is one", () => {
    vi.stubEnv("VITE_API_URL", "https://api.example.com");

    expect(apiUrl("/api/apartments")).toBe("https://api.example.com/api/apartments");
  });

  it("uses this same site when no server address is set", () => {
    vi.stubEnv("VITE_API_URL", undefined);

    expect(apiUrl("/api/apartments")).toBe("/api/apartments");
  });
});

describe("loading the recently reviewed apartments", () => {
  const brunswick: RecentApartment = {
    uid: "a1",
    house_number: "12",
    street: "Brunswick Street",
    city: "Melbourne",
    state: "Victoria",
    postcode: "3065",
    display_name: "12, Brunswick Street, Fitzroy, Melbourne, Victoria, 3065, Australia",
    review_count: 3,
    average_score: 72,
    latest_review_text: "Great light, but repairs took six weeks.",
    photo_url: "https://maps.googleapis.com/maps/api/streetview?location=12+Brunswick+Street",
  };

  beforeEach(() => {
    setActivePinia(createPinia());
  });

  afterEach(() => {
    vi.unstubAllGlobals();
    vi.unstubAllEnvs();
  });

  it("loads the recently reviewed apartments from the server", async () => {
    vi.stubEnv("VITE_API_URL", "https://api.example.com");
    const requested: string[] = [];
    vi.stubGlobal("fetch", async (url: string) => {
      requested.push(url);
      return new Response(JSON.stringify([brunswick]), { status: 200 });
    });
    const store = useApartmentStore();

    await store.fetchRecentApartments(4);

    expect(requested).toEqual(["https://api.example.com/apartments/recent?limit=4"]);
    expect(store.recentApartments).toEqual([brunswick]);
    expect(store.error).toBeNull();
    expect(store.loading).toBe(false);
  });

  it("sets an error and keeps the list empty when the server is down", async () => {
    vi.stubGlobal(
      "fetch",
      async () =>
        new Response(JSON.stringify({ detail: "Reviews are unavailable right now" }), {
          status: 503,
        }),
    );
    const store = useApartmentStore();

    await store.fetchRecentApartments(4);

    expect(store.recentApartments).toEqual([]);
    expect(store.error).toBeTruthy();
    expect(store.loading).toBe(false);
  });
});
