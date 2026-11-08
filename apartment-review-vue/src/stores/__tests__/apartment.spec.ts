import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { createPinia, setActivePinia } from "pinia";
import { apiUrl, useApartmentStore } from "../apartment";

describe("apartment store", () => {
  beforeEach(() => {
    setActivePinia(createPinia());
  });

  it("getApartmentById returns the apartment with that uid", () => {
    const store = useApartmentStore();
    store.apartments = [
      { uid: "a1", address: "1 Test St" },
      { uid: "a2", address: "2 Test St" },
    ];

    expect(store.getApartmentById("a2")).toEqual({ uid: "a2", address: "2 Test St" });
  });

  it("getApartmentById returns undefined for an unknown uid", () => {
    const store = useApartmentStore();

    expect(store.getApartmentById("nope")).toBeUndefined();
  });
});

describe("apiUrl", () => {
  afterEach(() => {
    vi.unstubAllEnvs();
  });

  it("prefixes the path with VITE_API_URL", () => {
    vi.stubEnv("VITE_API_URL", "https://api.example.com");

    expect(apiUrl("/api/apartments")).toBe("https://api.example.com/api/apartments");
  });

  it("keeps the path relative when VITE_API_URL is not set", () => {
    vi.stubEnv("VITE_API_URL", undefined);

    expect(apiUrl("/api/apartments")).toBe("/api/apartments");
  });
});
