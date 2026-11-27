import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { flushPromises, mount } from "@vue/test-utils";
import { createPinia, setActivePinia } from "pinia";
import GoogleSignIn from "../GoogleSignIn.vue";
import { useAuthStore } from "@/stores/auth";

/** Stand in for Google's sign-in script: records what the page asks of it. */
function googleScript() {
  const calls: { config?: GoogleIdConfig; parent?: HTMLElement } = {};
  vi.stubGlobal("google", {
    accounts: {
      id: {
        initialize: (config: GoogleIdConfig) => (calls.config = config),
        renderButton: (parent: HTMLElement) => (calls.parent = parent),
      },
    },
  });
  return calls;
}

describe("GoogleSignIn", () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    vi.stubEnv("VITE_GOOGLE_CLIENT_ID", "123.apps.googleusercontent.com");
  });

  afterEach(() => {
    vi.unstubAllGlobals();
    vi.unstubAllEnvs();
  });

  it("asks Google to draw its button here, for this site's client ID", () => {
    const google = googleScript();

    const button = mount(GoogleSignIn);

    expect(google.config?.client_id).toBe("123.apps.googleusercontent.com");
    expect(google.parent).toBe(button.find(".google-button").element);
  });

  it("signs in with the credential Google hands back", async () => {
    const google = googleScript();
    vi.stubGlobal("fetch", async (url: string) => {
      expect(url).toContain("/auth/google");
      return new Response(JSON.stringify({ uid: "u1", name: "Tom Leon", email: "t@e.com" }), {
        status: 200,
      });
    });
    mount(GoogleSignIn);

    google.config?.callback({ credential: "google-token" });
    await flushPromises();

    expect(useAuthStore().user?.name).toBe("Tom Leon");
  });

  it("says so when Google's script did not load", () => {
    vi.stubGlobal("google", undefined);

    const button = mount(GoogleSignIn);

    expect(button.text()).toContain("Google sign-in is not available");
  });
});
