<script setup lang="ts">
import { onMounted } from "vue";
import { storeToRefs } from "pinia";
import Toolbar from "primevue/toolbar";
import Button from "primevue/button";
import GoogleSignIn from "@/components/GoogleSignIn.vue";
import { useAuthStore } from "@/stores/auth";

const auth = useAuthStore();
const { user } = storeToRefs(auth);

onMounted(auth.fetchMe);
</script>

<template>
  <header>
    <Toolbar>
      <template #start>Apartment reviews</template>
      <template #end>
        <template v-if="user">
          <span>Hi {{ user.name.split(" ")[0] }}</span>
          <Button label="Sign out" severity="secondary" text @click="auth.logout" />
        </template>
        <GoogleSignIn v-else />
      </template>
    </Toolbar>
  </header>
  <RouterView />
</template>

<style scoped>
header {
  margin-bottom: 2rem;
}

.p-toolbar-end {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}
</style>
