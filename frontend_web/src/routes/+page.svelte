<script lang="ts">
  import VideoTab from "$lib/components/VideoTab.svelte";
  import AudioTab from "$lib/components/AudioTab.svelte";
  import SubtitlesTab from "$lib/components/SubtitlesTab.svelte";
  import ChaptersTab from "$lib/components/ChaptersTab.svelte";
  import OutputTab from "$lib/components/OutputTab.svelte";
  import SettingsTab from "$lib/components/SettingsTab.svelte";
  import Navigation from "$lib/components/Navigation.svelte";
  import { currentTab } from "$lib/stores/navigation";

  const tabs = [
    { id: "video", component: VideoTab, icon: "🎬", label: "Video" },
    { id: "audio", component: AudioTab, icon: "🎵", label: "Audio" },
    {
      id: "subtitles",
      component: SubtitlesTab,
      icon: "💬",
      label: "Subtitles",
    },
    { id: "chapters", component: ChaptersTab, icon: "📑", label: "Chapters" },
    { id: "output", component: OutputTab, icon: "📤", label: "Output" },
    { id: "settings", component: SettingsTab, icon: "⚙️", label: "Settings" },
  ];

  const activeTab = $derived(tabs.find((t) => t.id === $currentTab) || tabs[0]);
</script>

<div class="app-container">
  <Navigation {tabs} />
  <main class="content">
    {#if activeTab}
      {@const Component = activeTab.component}
      <Component />
    {/if}
  </main>
</div>

<style>
  .app-container {
    display: flex;
    height: 100vh;
    overflow: hidden;
  }

  .content {
    flex: 1;
    overflow-y: auto;
    padding: 1rem;
    background-color: var(--bg-primary);
  }
</style>
