import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { createPinia, setActivePinia } from "pinia";
import { useAuthStore, type User } from "../auth";

const tom: User = { uid: "u1", name: "Tom Leon", email: "tom@example.com" };

/** Stand in for the API: record each request, answer with this status and body. */
function apiAnswers(status: number, body: unknown) {
  const requests: { url: string; init?: RequestInit }[] = [];
  vi.stubGlobal("fetch", async (url: string, init?: RequestInit) => {
    requests.push({ url, init });
    return new Response(body === null ? null : JSON.stringify(body), { status });
  });
  return requests;
}

describe("auth store", () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    vi.stubEnv("VITE_API_URL", "https://api.example.com");
  });

  afterEach(() => {
    vi.unstubAllGlobals();
    vi.unstubAllEnvs();
  });

  it("finds out who is signed in when the page opens", async () => {
    const requests = apiAnswers(200, tom);
    const auth = useAuthStore();

    await auth.fetchMe();

    expect(requests).toEqual([
      { url: "https://api.example.com/auth/me", init: { credentials: "include" } },
    ]);
    expect(auth.user).toEqual(tom);
  });

  it("knows nobody is signed in when nobody is", async () => {
    apiAnswers(401, { detail: "Sign in first" });
    const auth = useAuthStore();

    await auth.fetchMe();

    expect(auth.user).toBeNull();
  });

  it("signs in with the proof from Google and remembers the user", async () => {
    const requests = apiAnswers(200, tom);
    const auth = useAuthStore();

    await auth.loginWithGoogle("google-token");

    expect(requests[0].url).toBe("https://api.example.com/auth/google");
    expect(requests[0].init).toMatchObject({
      method: "POST",
      credentials: "include",
      body: JSON.stringify({ credential: "google-token" }),
    });
    expect(auth.user).toEqual(tom);
  });

  it("signing out tells the server and forgets the user", async () => {
    const auth = useAuthStore();
    auth.user = tom;
    const requests = apiAnswers(204, null);

    await auth.logout();

    expect(requests).toEqual([
      {
        url: "https://api.example.com/auth/logout",
        init: { method: "POST", credentials: "include" },
      },
    ]);
    expect(auth.user).toBeNull();
  });
});
