<template>
  <main>
    <h1>Tell the next tenant what it’s really like.</h1>
    <p class="lead">
      Rate the landlord, location, condition and noise of a place you’ve
      rented. Leave out your unit number to stay anonymous.
    </p>
    <Button
      icon="pi pi-pencil"
      label="Review an apartment"
      size="large"
      @click="showModal = true"
    />
    <Message v-if="error" severity="error">{{ error }}</Message>
    <Card v-if="loading || apartments.length">
      <template #content>
        <DataTable :value="apartments" :loading="loading" data-key="uid">
          <Column field="address" header="Address" />
        </DataTable>
      </template>
    </Card>

    <CreateReviewModal v-model:visible="showModal" @submit="handleSubmit" />
  </main>
</template>

<script setup lang="ts">
import { ref, onMounted } from "vue";
import { useApartmentStore } from "@/stores/apartment";
import { storeToRefs } from "pinia";
import Button from "primevue/button";
import Card from "primevue/card";
import Column from "primevue/column";
import DataTable from "primevue/datatable";
import Message from "primevue/message";
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

<style scoped>
h1 {
  max-width: 14em;
  font-size: clamp(2.25rem, 6vw, 3.75rem);
  font-weight: 700;
  line-height: 1.1;
  letter-spacing: -0.02em;
  color: var(--p-primary-900);
}

.lead {
  max-width: 34em;
  margin: 1.25rem 0 2rem;
  font-size: 1.125rem;
}

.p-message,
.p-card {
  margin-top: 3rem;
}
</style>
