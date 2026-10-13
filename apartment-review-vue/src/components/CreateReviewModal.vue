<template>
  <Dialog
    v-model:visible="isVisible"
    modal
    header="Add Your Contribution"
    :style="{ width: '50rem' }"
    :breakpoints="{ '1199px': '75vw', '575px': '90vw' }"
  >
    <div class="flex flex-column gap-3">
      <div class="flex flex-column gap-2">
        <label for="address">Apartment Address</label>
        <AutoComplete
          id="address"
          v-model="address"
          :suggestions="filteredAddresses"
          @complete="searchAddress"
          placeholder="Enter apartment address"
          dropdown
        />
      </div>

      <div class="flex flex-column gap-2">
        <label for="unitNumber"
          >Unit Number (Optional - leave blank to stay anonymous)</label
        >
        <InputText
          id="unitNumber"
          v-model="unitNumber"
          placeholder="e.g., 12A, 305"
        />
      </div>

      <div class="flex flex-column gap-2">
        <label for="landlordRating">Landlord Rating</label>
        <Rating v-model="landlordRating" :cancel="false" :stars="5" off-icon="pi pi-star" />
      </div>

      <div class="flex flex-column gap-2">
        <label for="locationRating">Location Rating</label>
        <Rating v-model="locationRating" :cancel="false" :stars="5" off-icon="pi pi-star" />
      </div>

      <div class="flex flex-column gap-2">
        <label for="conditionRating">Condition Rating</label>
        <Rating v-model="conditionRating" :cancel="false" :stars="5" off-icon="pi pi-star" />
      </div>

      <div class="flex flex-column gap-2">
        <label for="quietnessRating">Quietness Rating</label>
        <Rating v-model="quietnessRating" :cancel="false" :stars="5" off-icon="pi pi-star" />
      </div>

      <div class="flex flex-column gap-2">
        <label for="review">Review</label>
        <Textarea
          id="review"
          v-model="reviewText"
          rows="5"
          placeholder="Write your review..."
        />
      </div>
    </div>

    <template #footer>
      <Button label="Cancel" severity="secondary" @click="closeModal" />
      <Button label="Submit" @click="submitReview" />
    </template>
  </Dialog>
</template>

<script setup lang="ts">
import { ref, watch } from "vue";
import Dialog from "primevue/dialog";
import AutoComplete from "primevue/autocomplete";
import InputText from "primevue/inputtext";
import Textarea from "primevue/textarea";
import Rating from "primevue/rating";
import Button from "primevue/button";
import { useApartmentStore } from "@/stores/apartment";
import { storeToRefs } from "pinia";

const props = defineProps<{
  visible: boolean;
}>();

const emit = defineEmits<{
  (e: "update:visible", value: boolean): void;
  (
    e: "submit",
    data: { address: string; rating: number; reviewText: string }
  ): void;
}>();

const apartmentStore = useApartmentStore();
const { apartments } = storeToRefs(apartmentStore);

const isVisible = ref(props.visible);
const address = ref("");
const unitNumber = ref("");
const landlordRating = ref(0);
const locationRating = ref(0);
const conditionRating = ref(0);
const quietnessRating = ref(0);
const reviewText = ref("");
const filteredAddresses = ref<string[]>([]);

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

function submitReview() {
  const data: any = {
    address: address.value,
    landlordRating: landlordRating.value,
    locationRating: locationRating.value,
    conditionRating: conditionRating.value,
    quietnessRating: quietnessRating.value,
    reviewText: reviewText.value,
  };

  // Only include unit number if provided
  if (unitNumber.value.trim()) {
    data.unitNumber = unitNumber.value.trim();
  }

  emit("submit", data);
  closeModal();
}

function resetForm() {
  address.value = "";
  unitNumber.value = "";
  landlordRating.value = 0;
  locationRating.value = 0;
  conditionRating.value = 0;
  quietnessRating.value = 0;
  reviewText.value = "";
  filteredAddresses.value = [];
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

    const data = await response.json();
    filteredAddresses.value = data.map((item: any) => item.display_name);

    // If no results, allow manual entry
    if (filteredAddresses.value.length === 0) {
      filteredAddresses.value = [`No results found. Use: ${query}`];
    }
  } catch (error) {
    console.error("Address search error:", error);
    filteredAddresses.value = [`Error searching. Use: ${query}`];
  }
}
</script>

<style scoped>
.flex {
  display: flex;
}

.flex-column {
  flex-direction: column;
}

.gap-2 {
  gap: 0.5rem;
}

.gap-3 {
  gap: 0.75rem;
}

label {
  font-weight: 600;
}

/* Selected stars are solid yellow; hovering star 3 fills stars 1-3 solid yellow, 4-5 stay outlines. */
:deep(.p-rating) {
  --p-rating-icon-active-color: #fbbf24;
  --p-rating-icon-hover-color: #fbbf24;
}

:deep(.p-rating:hover .p-rating-icon) {
  color: #fbbf24;
}

:deep(.p-rating:hover .pi-star::before) {
  content: "\e936";
}

:deep(.p-rating-option:hover ~ .p-rating-option .p-rating-icon) {
  color: var(--p-rating-icon-color);
}

:deep(.p-rating-option:hover ~ .p-rating-option .pi-star::before) {
  content: "\e937";
}
</style>
