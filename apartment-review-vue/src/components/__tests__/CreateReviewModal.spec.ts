import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { flushPromises, mount } from "@vue/test-utils";
import { createPinia, setActivePinia } from "pinia";
import PrimeVue from "primevue/config";
import AutoComplete from "primevue/autocomplete";
import CreateReviewModal from "../CreateReviewModal.vue";
import { useAuthStore } from "@/stores/auth";

const tom = { uid: "u1", name: "Tom Leon", email: "tom@example.com" };

async function mountModal() {
  const modal = mount(CreateReviewModal, {
    props: { visible: true },
    global: { plugins: [PrimeVue], stubs: { teleport: true } },
  });
  await flushPromises(); // the dialog draws its content one tick after mounting
  return modal;
}

type Modal = Awaited<ReturnType<typeof mountModal>>;

function postButton(modal: Modal) {
  return modal.findAll("button").find((button) => button.text() === "Post review")!;
}

const place = {
  display_name: "12, Smith Street, Newtown, Sydney, 2042, Australia",
  address: { house_number: "12", road: "Smith Street", city: "Sydney" },
};

/** Pick an address from the search results, as a click on a suggestion does. */
async function pickAddress(modal: Modal) {
  await modal.findComponent(AutoComplete).setValue(place);
}

/** Stand in for the API: answer every request with this status, and record the paths. */
function apiAnswers(status: number) {
  const requested: string[] = [];
  vi.stubGlobal("fetch", async (url: string) => {
    requested.push(url);
    return new Response(JSON.stringify({ uid: "a1" }), { status });
  });
  return requested;
}

describe("CreateReviewModal sign-in gate", () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    vi.stubGlobal("google", {
      accounts: { id: { initialize: () => {}, renderButton: () => {} } },
    });
    apiAnswers(201);
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("asks a signed-out visitor to sign in and keeps what they typed", async () => {
    const modal = await mountModal();
    await modal.find("#review").setValue("Great light, slow repairs.");

    await postButton(modal).trigger("click");

    expect(modal.emitted("submit")).toBeUndefined();
    expect(modal.text()).toContain(
      "Sign in to post. Your name is never shown with your review.",
    );
    expect(modal.find(".google-button").exists()).toBe(true);
    expect((modal.find("#review").element as HTMLTextAreaElement).value).toBe(
      "Great light, slow repairs.",
    );
  });

  it("posts straight away for a signed-in user", async () => {
    useAuthStore().user = tom;
    const modal = await mountModal();
    await pickAddress(modal);
    await modal.find("#review").setValue("Great light, slow repairs.");

    await postButton(modal).trigger("click");
    await flushPromises();

    expect(modal.emitted("submit")?.[0][0]).toMatchObject({
      reviewText: "Great light, slow repairs.",
    });
    expect(modal.text()).not.toContain("Sign in to post");
  });

  it("posts on the next click once the visitor has signed in", async () => {
    const modal = await mountModal();
    await pickAddress(modal);
    await modal.find("#review").setValue("Great light, slow repairs.");
    await postButton(modal).trigger("click");

    useAuthStore().user = tom;
    await modal.vm.$nextTick();
    await postButton(modal).trigger("click");
    await flushPromises();

    expect(modal.text()).not.toContain("Sign in to post");
    expect(modal.emitted("submit")?.[0][0]).toMatchObject({
      reviewText: "Great light, slow repairs.",
    });
  });
});

describe("CreateReviewModal posting", () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    useAuthStore().user = tom;
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("saves the review of the picked address, then closes", async () => {
    const requested = apiAnswers(201);
    const modal = await mountModal();
    await pickAddress(modal);
    await modal.find("#review").setValue("Great light, slow repairs.");

    await postButton(modal).trigger("click");
    await flushPromises();

    expect(requested).toEqual(["/apartments/from-osm", "/reviews"]);
    expect(modal.emitted("submit")).toHaveLength(1);
    expect(modal.emitted("update:visible")?.at(-1)).toEqual([false]);
  });

  it("asks for an address from the list when none was picked", async () => {
    const requested = apiAnswers(201);
    const modal = await mountModal();
    await modal.find("#review").setValue("Great light, slow repairs.");

    await postButton(modal).trigger("click");
    await flushPromises();

    expect(modal.find(".p-message-error").text()).toContain(
      "Pick the address from the list.",
    );
    expect(requested).toEqual([]);
    expect(modal.emitted("submit")).toBeUndefined();
  });

  it("stays open with what was typed when the review cannot be saved", async () => {
    apiAnswers(503);
    const modal = await mountModal();
    await pickAddress(modal);
    await modal.find("#review").setValue("Great light, slow repairs.");

    await postButton(modal).trigger("click");
    await flushPromises();

    expect(modal.find(".p-message-error").text()).toContain(
      "Your review could not be saved.",
    );
    expect(modal.emitted("submit")).toBeUndefined();
    expect((modal.find("#review").element as HTMLTextAreaElement).value).toBe(
      "Great light, slow repairs.",
    );
  });
});
