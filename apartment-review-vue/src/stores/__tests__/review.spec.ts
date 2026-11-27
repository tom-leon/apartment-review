import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { postReview, type NewReview } from "../review";

const review: NewReview = {
  place: {
    display_name: "12, Smith Street, Newtown, Sydney, 2042, Australia",
    address: {
      house_number: "12",
      road: "Smith Street",
      city: "Sydney",
      postcode: "2042",
      country: "Australia",
      country_code: "au",
    },
  },
  landlordRating: 55,
  locationRating: 90,
  conditionRating: 35,
  quietnessRating: 70,
  reviewText: "Cold in winter, lovely neighbours.",
  unitNumber: "12A",
};

/** Stand in for the API: record each request, answer each path with its status and body. */
function apiAnswers(answers: Record<string, [number, unknown]>) {
  const requests: { url: string; init?: RequestInit }[] = [];
  vi.stubGlobal("fetch", async (url: string, init?: RequestInit) => {
    requests.push({ url, init });
    const [status, body] = answers[new URL(url).pathname];
    return new Response(JSON.stringify(body), { status });
  });
  return requests;
}

describe("postReview", () => {
  beforeEach(() => {
    vi.stubEnv("VITE_API_URL", "https://api.example.com");
  });

  afterEach(() => {
    vi.unstubAllGlobals();
    vi.unstubAllEnvs();
  });

  it("saves the apartment at the picked address, then the review of it", async () => {
    const requests = apiAnswers({
      "/apartments/from-osm": [201, { uid: "a1" }],
      "/reviews": [201, { uid: "r1" }],
    });

    await postReview(review);

    expect(requests.map((request) => request.url)).toEqual([
      "https://api.example.com/apartments/from-osm",
      "https://api.example.com/reviews",
    ]);
    expect(JSON.parse(requests[0].init!.body as string)).toEqual({
      ...review.place.address,
      display_name: review.place.display_name,
    });
    expect(JSON.parse(requests[1].init!.body as string)).toEqual({
      apartment_uid: "a1",
      unit_number: "12A",
      content: "Cold in winter, lovely neighbours.",
      landlord_rating: 55,
      location_rating: 90,
      condition_rating: 35,
      quietness_rating: 70,
    });
  });

  it("sends no unit number when the reviewer left it blank", async () => {
    const requests = apiAnswers({
      "/apartments/from-osm": [201, { uid: "a1" }],
      "/reviews": [201, { uid: "r1" }],
    });

    await postReview({ ...review, unitNumber: "" });

    expect(JSON.parse(requests[1].init!.body as string).unit_number).toBeNull();
  });

  it("sends the sign-in cookie with the review", async () => {
    const requests = apiAnswers({
      "/apartments/from-osm": [201, { uid: "a1" }],
      "/reviews": [201, { uid: "r1" }],
    });

    await postReview(review);

    expect(requests[1].init).toMatchObject({ method: "POST", credentials: "include" });
  });

  it("says so when this person has already reviewed the place", async () => {
    apiAnswers({
      "/apartments/from-osm": [201, { uid: "a1" }],
      "/reviews": [409, { detail: "You have already reviewed this apartment" }],
    });

    await expect(postReview(review)).rejects.toThrow("You’ve already reviewed this place.");
  });

  it("asks to sign in again when the sign-in has run out", async () => {
    apiAnswers({
      "/apartments/from-osm": [201, { uid: "a1" }],
      "/reviews": [401, { detail: "Sign in first" }],
    });

    await expect(postReview(review)).rejects.toThrow("Sign in again to post your review.");
  });

  it("does not post a review when the apartment cannot be saved", async () => {
    const requests = apiAnswers({ "/apartments/from-osm": [503, {}] });

    await expect(postReview(review)).rejects.toThrow("Your review could not be saved.");
    expect(requests).toHaveLength(1);
  });
});
