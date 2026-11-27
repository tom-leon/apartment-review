import { ref } from "vue";
import { defineStore } from "pinia";
import { apiUrl } from "@/stores/apartment";

/** The signed-in user, as the API's /auth routes return it. */
export interface User {
  uid: string;
  name: string;
  email: string;
}

/** Who is signed in. The API knows from its cookie, so every call sends it. */
export const useAuthStore = defineStore("auth", () => {
  const user = ref<User | null>(null);

  async function fetchMe() {
    const response = await fetch(apiUrl("/auth/me"), { credentials: "include" });
    user.value = response.ok ? await response.json() : null;
  }

  async function loginWithGoogle(credential: string) {
    const response = await fetch(apiUrl("/auth/google"), {
      method: "POST",
      credentials: "include",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ credential }),
    });
    if (!response.ok) throw new Error("Google sign-in failed");
    user.value = await response.json();
  }

  async function logout() {
    await fetch(apiUrl("/auth/logout"), { method: "POST", credentials: "include" });
    user.value = null;
  }

  return { user, fetchMe, loginWithGoogle, logout };
});
