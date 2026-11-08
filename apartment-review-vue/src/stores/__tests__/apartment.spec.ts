import { describe, expect, it, beforeEach } from "vitest";
import { createPinia, setActivePinia } from "pinia";
import { useApartmentStore } from "../apartment";

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
