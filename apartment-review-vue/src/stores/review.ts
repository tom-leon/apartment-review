import { apiUrl } from "@/stores/apartment";

/** One result of the OpenStreetMap (Nominatim) address search. */
export interface Place {
  display_name: string;
  /** The address in parts: road, house_number, city, postcode, country_code… */
  address: Record<string, string>;
}

/** What the review form collects. */
export interface NewReview {
  place: Place;
  landlordRating: number;
  locationRating: number;
  conditionRating: number;
  quietnessRating: number;
  reviewText: string;
}

const FAILURES: Record<number, string> = {
  401: "Sign in again to post your review.",
  409: "You’ve already reviewed this place.",
};

/** POST JSON to the API with the sign-in cookie; throws a message fit to show the user. */
async function send(path: string, body: unknown) {
  const response = await fetch(apiUrl(path), {
    method: "POST",
    credentials: "include",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!response.ok) {
    throw new Error(FAILURES[response.status] ?? "Your review could not be saved.");
  }
  return response.json();
}

/** Save the apartment at the picked address (the API reuses a known one), then the review of it. */
export async function postReview(review: NewReview) {
  const apartment = await send("/apartments/from-osm", {
    ...review.place.address,
    display_name: review.place.display_name,
  });
  await send("/reviews", {
    apartment_uid: apartment.uid,
    content: review.reviewText,
    landlord_rating: review.landlordRating,
    location_rating: review.locationRating,
    condition_rating: review.conditionRating,
    quietness_rating: review.quietnessRating,
  });
}
