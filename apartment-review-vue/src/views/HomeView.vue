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
    <Message v-if="posted" severity="success">
      Thanks. Your review is live.
    </Message>
    <Message v-if="error" severity="error">{{ error }}</Message>
    <section v-if="recentApartments.length" aria-labelledby="recent-heading">
      <h2 id="recent-heading">Recently reviewed</h2>
      <ul class="cards">
        <li v-for="apartment in recentApartments" :key="apartment.uid">
          <ApartmentCard :apartment="apartment" />
        </li>
      </ul>
    </section>

    <CreateReviewModal v-model:visible="showModal" @submit="showPostedReview" />
  </main>
</template>

<script setup lang="ts">
import { ref, onMounted } from "vue";
import { useApartmentStore } from "@/stores/apartment";
import { storeToRefs } from "pinia";
import Button from "primevue/button";
import Message from "primevue/message";
import ApartmentCard from "@/components/ApartmentCard.vue";
import CreateReviewModal from "@/components/CreateReviewModal.vue";

// One row of cards on a computer. Each card with a photo is one counted request
// to Google per visitor, so this number is also what the photo allowance is spent on.
const RECENT_CARDS = 4;

const store = useApartmentStore();
const { recentApartments, error } = storeToRefs(store);
const showModal = ref(false);
const posted = ref(false);

onMounted(() => {
  store.fetchRecentApartments(RECENT_CARDS);
});

function showPostedReview() {
  posted.value = true;
  store.fetchRecentApartments(RECENT_CARDS);
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
section {
  margin-top: 3rem;
}

h2 {
  margin-bottom: 1rem;
  font-size: 1.5rem;
  font-weight: 700;
  line-height: 1.2;
  letter-spacing: -0.01em;
  color: var(--p-primary-900);
}

/* Four across at full width, fewer as the window narrows, one per row on a phone. */
.cards {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(13rem, 1fr));
  gap: 1rem;
  padding: 0;
  list-style: none;
}
</style>
