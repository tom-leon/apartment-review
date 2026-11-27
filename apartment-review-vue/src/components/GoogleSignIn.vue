<template>
  <div v-if="googleLoaded" ref="button" class="google-button"></div>
  <p v-else>Google sign-in is not available right now.</p>
</template>

<script setup lang="ts">
import { onMounted, ref } from "vue";
import { useAuthStore } from "@/stores/auth";

const auth = useAuthStore();
const button = ref<HTMLElement>();
// Google's script is loaded by index.html; without it there is nothing to draw.
const googleLoaded = typeof google !== "undefined";

onMounted(() => {
  if (!googleLoaded || !button.value) return;
  google.accounts.id.initialize({
    client_id: import.meta.env.VITE_GOOGLE_CLIENT_ID ?? "",
    callback: ({ credential }) => auth.loginWithGoogle(credential),
  });
  google.accounts.id.renderButton(button.value, { theme: "outline", size: "large" });
});
</script>
