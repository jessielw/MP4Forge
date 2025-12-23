<script lang="ts">
  import { onMount } from "svelte";
  import "@fontsource/open-sans";
  import "@fontsource/fira-mono";
  import "../app.css";
  import { theme } from "$lib/stores/settings";
  import { initializeWebSocket, closeWebSocket } from "$lib/stores/queue";
  import Toast from "$lib/components/Toast.svelte";
  import type { Snippet } from "svelte";

  let { children }: { children: Snippet } = $props();

  $effect(() => {
    if (typeof document !== "undefined") {
      document.documentElement.setAttribute("data-theme", $theme);
    }
  });

  // initialize WebSocket once at app level
  onMount(() => {
    initializeWebSocket();

    return () => {
      closeWebSocket();
    };
  });
</script>

{@render children()}
<Toast />
