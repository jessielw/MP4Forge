<script lang="ts">
  import "../app.css";
  import { theme } from "$lib/stores/settings";
  import type { Snippet } from "svelte";

  let { children }: { children: Snippet } = $props();

  $effect(() => {
    if (typeof document !== "undefined") {
      document.documentElement.setAttribute("data-theme", $theme);
    }
  });
</script>

{@render children()}
