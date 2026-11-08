import { ref } from "vue";
import { defineStore } from "pinia";

/** Prefix a path with the API base URL set at build time (see env.d.ts). */
export function apiUrl(path: string): string {
  return `${import.meta.env.VITE_API_URL ?? ""}${path}`;
}

export interface Apartment {
  uid: string;
  address: string;
}

export const useApartmentStore = defineStore("apartment", () => {
  const apartments = ref<Apartment[]>([]);
  const loading = ref(false);
  const error = ref<string | null>(null);

  async function fetchApartments() {
    loading.value = true;
    error.value = null;
    try {
      // TODO: the backend has no list route yet; see the plan for the rename
      const response = await fetch(apiUrl("/api/apartments"));
      if (!response.ok) throw new Error("Failed to fetch apartments");
      apartments.value = await response.json();
    } catch (e) {
      error.value = e instanceof Error ? e.message : "Unknown error";
    } finally {
      loading.value = false;
    }
  }

  async function createApartment(address: string) {
    loading.value = true;
    error.value = null;
    try {
      // TODO: the backend route is POST /apartment; see the plan for the rename
      const response = await fetch(apiUrl("/api/apartments"), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ address }),
      });
      if (!response.ok) throw new Error("Failed to create apartment");
      const newApartment = await response.json();
      apartments.value.push(newApartment);
      return newApartment;
    } catch (e) {
      error.value = e instanceof Error ? e.message : "Unknown error";
      throw e;
    } finally {
      loading.value = false;
    }
  }

  function getApartmentById(uid: string) {
    return apartments.value.find((apt) => apt.uid === uid);
  }

  return {
    apartments,
    loading,
    error,
    fetchApartments,
    createApartment,
    getApartmentById,
  };
});
