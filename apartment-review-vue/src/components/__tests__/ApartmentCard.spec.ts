import { describe, expect, it } from "vitest";
import { mount } from "@vue/test-utils";
import PrimeVue from "primevue/config";
import ApartmentCard from "../ApartmentCard.vue";
import type { RecentApartment } from "@/stores/apartment";

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

function mountCard(changes: Partial<RecentApartment> = {}) {
  return mount(ApartmentCard, {
    props: { apartment: { ...brunswick, ...changes } },
    global: { plugins: [PrimeVue] },
  });
}

describe("ApartmentCard", () => {
  it("shows the address, score, review count and newest review", () => {
    const card = mountCard();

    expect(card.find(".address").text()).toBe("12 Brunswick Street");
    expect(card.find(".suburb").text()).toBe("Melbourne Victoria 3065");
    expect(card.find(".score").text()).toBe("72 / 100");
    expect(card.find(".review-count").text()).toBe("3 reviews");
    expect(card.find(".quote").text()).toBe("“Great light, but repairs took six weeks.”");
  });

  it("says “1 review” when there is only one", () => {
    const card = mountCard({ review_count: 1 });

    expect(card.find(".review-count").text()).toBe("1 review");
  });

  it("shows the street photo with Google's credit", () => {
    const card = mountCard();

    const photo = card.find("img");
    expect(photo.attributes("src")).toBe(brunswick.photo_url);
    expect(photo.attributes("alt")).toBe("Street view of 12 Brunswick Street");
    expect(card.find(".photo-credit").text()).toBe("Google Maps");
    expect(card.find(".photo-placeholder").exists()).toBe(false);
  });

  it("shows a placeholder, and no Google credit, when there is no photo", () => {
    const card = mountCard({ photo_url: null });

    expect(card.find("img").exists()).toBe(false);
    expect(card.find(".photo-credit").exists()).toBe(false);
    expect(card.find(".photo-placeholder").exists()).toBe(true);
  });

  it("swaps to the placeholder when the photo fails to load", async () => {
    const card = mountCard();

    await card.find("img").trigger("error");

    expect(card.find("img").exists()).toBe(false);
    expect(card.find(".photo-credit").exists()).toBe(false);
    expect(card.find(".photo-placeholder").exists()).toBe(true);
  });

  it("falls back to the full address when the street is unknown", () => {
    const card = mountCard({ house_number: null, street: null });

    expect(card.find(".address").text()).toBe(brunswick.display_name);
    expect(card.find(".suburb").exists()).toBe(false);
  });

  it("shows a street with no house number as just the street", () => {
    const card = mountCard({ house_number: null });

    expect(card.find(".address").text()).toBe("Brunswick Street");
  });

  it("leaves the score out when no review gave a rating", () => {
    const card = mountCard({ average_score: null });

    expect(card.find(".score").exists()).toBe(false);
    expect(card.find(".review-count").text()).toBe("3 reviews");
  });

  it("leaves the quote out when the newest review has no text", () => {
    const card = mountCard({ latest_review_text: null });

    expect(card.find(".quote").exists()).toBe(false);
  });
});
