<template>
  <Card class="apartment-card">
    <template #header>
      <div class="photo">
        <template v-if="showPhoto">
          <img
            :src="apartment.photo_url ?? undefined"
            :alt="`Street view of ${address}`"
            loading="lazy"
            @error="photoFailed = true"
          />
          <span class="photo-credit">Google Maps</span>
        </template>
        <div v-else class="photo-placeholder" aria-hidden="true">
          <i class="pi pi-building" />
        </div>
      </div>
    </template>
    <template #title>
      <h3 class="address">{{ address }}</h3>
    </template>
    <template v-if="suburb" #subtitle>
      <span class="suburb">{{ suburb }}</span>
    </template>
    <template #content>
      <p class="rating">
        <span
          v-if="apartment.average_score !== null"
          class="score"
          :aria-label="`Average score ${apartment.average_score} out of 100`"
        >
          <strong>{{ apartment.average_score }}</strong> / 100
        </span>
        <span class="review-count">{{ reviewCount }}</span>
      </p>
      <p v-if="apartment.latest_review_text" class="quote">
        “{{ apartment.latest_review_text }}”
      </p>
    </template>
  </Card>
</template>

<script setup lang="ts">
import { computed, ref } from "vue";
import Card from "primevue/card";
import type { RecentApartment } from "@/stores/apartment";

const props = defineProps<{
  apartment: RecentApartment;
}>();

// Google answers 404 where it has no street photo; the image then fails to load.
const photoFailed = ref(false);
const showPhoto = computed(
  () => props.apartment.photo_url !== null && !photoFailed.value
);

const address = computed(() => {
  const { house_number, street, display_name } = props.apartment;
  if (!street) return display_name;
  return house_number ? `${house_number} ${street}` : street;
});

const suburb = computed(() => {
  const { street, city, state, postcode } = props.apartment;
  if (!street) return "";
  return [city, state, postcode].filter(Boolean).join(" ");
});

const reviewCount = computed(() =>
  props.apartment.review_count === 1
    ? "1 review"
    : `${props.apartment.review_count} reviews`
);
</script>

<style scoped>
.apartment-card {
  height: 100%;
  overflow: hidden;
}

.apartment-card :deep(.p-card-body) {
  padding: 1rem;
}

.photo {
  position: relative;
  aspect-ratio: 16 / 10;
  background: var(--p-primary-200);
}

.photo img {
  display: block;
  width: 100%;
  height: 100%;
  object-fit: cover;
}

/* Top corner, so it never covers the mark Google prints along the photo's bottom edge. */
.photo-credit {
  position: absolute;
  top: 0.5rem;
  right: 0.5rem;
  padding: 0.125rem 0.375rem;
  border-radius: 4px;
  background: rgb(255 255 255 / 0.85);
  font-size: 0.6875rem;
  line-height: 1.4;
}

.photo-placeholder {
  display: grid;
  place-items: center;
  height: 100%;
  color: var(--p-primary-700);
}

.photo-placeholder .pi {
  font-size: 2.5rem;
}

.address {
  font-size: 1rem;
  font-weight: 600;
  line-height: 1.3;
  color: var(--p-primary-900);
  overflow-wrap: anywhere;
}

.suburb {
  font-size: 0.875rem;
}

.rating {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 0.5rem;
  font-size: 0.875rem;
  color: var(--p-text-muted-color);
}

.score strong {
  font-size: 1.5rem;
  font-weight: 700;
  font-variant-numeric: tabular-nums;
  color: var(--p-primary-900);
}

.quote {
  display: -webkit-box;
  margin-top: 0.75rem;
  overflow: hidden;
  font-size: 0.9375rem;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 3;
  line-clamp: 3;
}
</style>
