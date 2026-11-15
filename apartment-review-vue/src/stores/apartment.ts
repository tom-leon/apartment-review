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

/** One card on the home page, as GET /apartments/recent returns it. */
export interface RecentApartment {
  uid: string;
  house_number: string | null;
  street: string | null;
  city: string;
  state: string | null;
  postcode: string | null;
  display_name: string;
  review_count: number;
  /** 0–100, or null when no review gave a rating. */
  average_score: number | null;
  latest_review_text: string | null;
  /** Street photo of the building, or null when the API has no photo source. */
  photo_url: string | null;
}

export const useApartmentStore = defineStore("apartment", () => {
  const apartments = ref<Apartment[]>([]);
  const recentApartments = ref<RecentApartment[]>([]);
  const loading = ref(false);
  const error = ref<string | null>(null);

  async function fetchRecentApartments(limit: number) {
    loading.value = true;
    error.value = null;
    try {
      const response = await fetch(apiUrl(`/apartments/recent?limit=${limit}`));
      if (!response.ok) throw new Error("Recent reviews could not be loaded");
      recentApartments.value = await response.json();
    } catch (e) {
      error.value = e instanceof Error ? e.message : "Unknown error";
    } finally {
      loading.value = false;
    }
  }

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
    recentApartments,
    loading,
    error,
    fetchRecentApartments,
    fetchApartments,
    createApartment,
    getApartmentById,
  };
});
