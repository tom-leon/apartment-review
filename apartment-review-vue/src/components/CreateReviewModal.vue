<template>
  <Dialog
    v-model:visible="isVisible"
    modal
    header="Review an apartment"
    :style="{ width: '36rem' }"
    :breakpoints="{ '640px': '94vw' }"
  >
    <div class="report">
      <div class="field">
        <label for="address">Address</label>
        <AutoComplete
          id="address"
          v-model="address"
          :suggestions="filteredAddresses"
          optionLabel="display_name"
          @complete="searchAddress"
          placeholder="Start typing a street address"
          dropdown
        />
      </div>

      <div class="field">
        <label for="unitNumber">Unit number (optional)</label>
        <InputText
          id="unitNumber"
          v-model="unitNumber"
          placeholder="e.g. 12A"
          aria-describedby="unitNumber-help"
        />
        <Message id="unitNumber-help" size="small" severity="secondary" variant="simple">
          Leave blank to stay anonymous.
        </Message>
      </div>

      <Fieldset legend="Ratings">
        <div class="rating-row">
          <label for="landlordRating">Landlord</label>
          <Slider v-model="landlordRating" :min="0" :max="100" :step="1" />
          <span>{{ landlordRating }}</span>
        </div>
        <div class="rating-row">
          <label for="locationRating">Location</label>
          <Slider v-model="locationRating" :min="0" :max="100" :step="1" />
          <span>{{ locationRating }}</span>
        </div>
        <div class="rating-row">
          <label for="conditionRating">Condition</label>
          <Slider v-model="conditionRating" :min="0" :max="100" :step="1" />
          <span>{{ conditionRating }}</span>
        </div>
        <div class="rating-row">
          <label for="quietnessRating">Quietness</label>
          <Slider v-model="quietnessRating" :min="0" :max="100" :step="1" />
          <span>{{ quietnessRating }}</span>
        </div>
      </Fieldset>

      <div class="field">
        <label for="review">Review</label>
        <Textarea
          id="review"
          v-model="reviewText"
          rows="5"
          placeholder="What should the next tenant know?"
        />
      </div>

      <div v-if="askedToSignIn && !user" class="field">
        <Message severity="info">
          Sign in to post. Your name is never shown with your review.
        </Message>
        <GoogleSignIn />
      </div>
      <Message v-if="error" severity="error">{{ error }}</Message>
    </div>

    <template #footer>
      <Button label="Cancel" severity="secondary" @click="closeModal" />
      <Button label="Post review" :loading="posting" @click="submitReview" />
    </template>
  </Dialog>
</template>

<script setup lang="ts">
import { ref, watch } from "vue";
import Dialog from "primevue/dialog";
import Fieldset from "primevue/fieldset";
import AutoComplete from "primevue/autocomplete";
import InputText from "primevue/inputtext";
import Textarea from "primevue/textarea";
import Slider from "primevue/slider";
import Button from "primevue/button";
import Message from "primevue/message";
import { useApartmentStore } from "@/stores/apartment";
import { useAuthStore } from "@/stores/auth";
import { postReview, type NewReview, type Place } from "@/stores/review";
import { storeToRefs } from "pinia";
import GoogleSignIn from "@/components/GoogleSignIn.vue";

const props = defineProps<{
  visible: boolean;
}>();

const emit = defineEmits<{
  (e: "update:visible", value: boolean): void;
  /** The review has been saved. */
  (e: "submit", data: NewReview): void;
}>();

const apartmentStore = useApartmentStore();
const { apartments } = storeToRefs(apartmentStore);
const { user } = storeToRefs(useAuthStore());

const isVisible = ref(props.visible);
// The picked search result, or plain text while the visitor is still typing.
const address = ref<Place | string>("");
const unitNumber = ref("");
const landlordRating = ref(50);
const locationRating = ref(50);
const conditionRating = ref(50);
const quietnessRating = ref(50);
const reviewText = ref("");
const filteredAddresses = ref<Place[]>([]);
const posting = ref(false);
const error = ref("");
// Set when "Post review" was pressed while signed out; the form keeps its values meanwhile.
const askedToSignIn = ref(false);

watch(
  () => props.visible,
  (newVal) => {
    isVisible.value = newVal;
  }
);

watch(isVisible, (newVal) => {
  emit("update:visible", newVal);
});

function closeModal() {
  isVisible.value = false;
  resetForm();
}

async function submitReview() {
  if (!user.value) {
    askedToSignIn.value = true;
    return;
  }
  if (typeof address.value === "string") {
    error.value = "Pick the address from the list.";
    return;
  }
  const data = {
    place: address.value,
    landlordRating: landlordRating.value,
    locationRating: locationRating.value,
    conditionRating: conditionRating.value,
    quietnessRating: quietnessRating.value,
    reviewText: reviewText.value,
    unitNumber: unitNumber.value.trim(),
  };

  posting.value = true;
  error.value = "";
  try {
    await postReview(data);
  } catch (e) {
    // The form stays open with what was typed, so the visitor can try again.
    error.value = e instanceof Error ? e.message : "Your review could not be saved.";
    return;
  } finally {
    posting.value = false;
  }
  emit("submit", data);
  closeModal();
}

function resetForm() {
  address.value = "";
  unitNumber.value = "";
  landlordRating.value = 50;
  locationRating.value = 50;
  conditionRating.value = 50;
  quietnessRating.value = 50;
  reviewText.value = "";
  filteredAddresses.value = [];
  askedToSignIn.value = false;
  error.value = "";
}

async function searchAddress(event: { query: string }) {
  const query = event.query;

  if (!query || query.length < 3) {
    filteredAddresses.value = [];
    return;
  }

  try {
    // Using Nominatim (OpenStreetMap) - Focused on Australian addresses
    // For Google Maps, replace with Google Places API
    const response = await fetch(
      `https://nominatim.openstreetmap.org/search?` +
        `format=json&q=${encodeURIComponent(query)}&` +
        `countrycodes=au&` +
        `addressdetails=1&limit=5`,
      {
        headers: {
          "User-Agent": "ApartmentReviewApp/1.0",
        },
      }
    );

    if (!response.ok) throw new Error("Failed to fetch addresses");

    filteredAddresses.value = await response.json();
  } catch (error) {
    console.error("Address search error:", error);
    filteredAddresses.value = [];
  }
}
</script>

<style scoped>
.report {
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
}

.field {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

label {
  font-weight: 600;
}

.rating-row {
  display: grid;
  grid-template-columns: 8rem 1fr 2rem;
  gap: 1rem;
  align-items: center;
  padding: 0.375rem 0;
}
</style>
