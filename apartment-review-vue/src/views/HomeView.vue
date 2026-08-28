<template>
  <div>
    <h1>Apartments</h1>
    <Button
      icon="pi pi-plus"
      label="Add your contribution"
      @click="showModal = true"
    />
    <p v-if="loading">Loading...</p>
    <p v-if="error">{{ error }}</p>
    <ul v-if="!loading && apartments.length">
      <li v-for="apartment in apartments" :key="apartment.uid">
        {{ apartment.address }}
      </li>
    </ul>

    <CreateReviewModal v-model:visible="showModal" @submit="handleSubmit" />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from "vue";
import { useApartmentStore } from "@/stores/apartment";
import { storeToRefs } from "pinia";
import Button from "primevue/button";
import CreateReviewModal from "@/components/CreateReviewModal.vue";

const store = useApartmentStore();
const { apartments, loading, error } = storeToRefs(store);
const showModal = ref(false);

onMounted(() => {
  // TODO: Uncomment when backend API is ready
  // store.fetchApartments();
});

function handleSubmit(data: {
  address: string;
  rating: number;
  reviewText: string;
}) {
  console.log("Review submitted:", data);
  // TODO: Handle review submission
}
</script>
