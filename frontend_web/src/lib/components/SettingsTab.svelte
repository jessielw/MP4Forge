<script lang="ts">
  import {
    theme,
    logLevel,
    audioPresetTitles,
    subtitlePresetTitles,
    saveSettingsToBackend,
  } from "$lib/stores/settings";
  import { toast } from "$lib/stores/toast";
  import PresetTitleEditor from "./PresetTitleEditor.svelte";
  import { LogLevel } from "$lib/api";
  import { titleCase } from "title-case";

  let audioTitles = $state([...$audioPresetTitles]);
  let subtitleTitles = $state([...$subtitlePresetTitles]);

  async function saveSettings() {
    // update stores
    audioPresetTitles.set(audioTitles);
    subtitlePresetTitles.set(subtitleTitles);

    // save to backend
    try {
      await saveSettingsToBackend();
      toast.success("Settings saved successfully!");
    } catch (err) {
      toast.error("Failed to save settings: " + (err as Error).message);
    }
  }
</script>

<div class="tab-container">
  <h2>Settings</h2>

  <div class="form-group">
    <label for="theme-select">Theme</label>
    <select id="theme-select" bind:value={$theme}>
      <option value="auto">Auto</option>
      <option value="light">Light</option>
      <option value="dark">Dark</option>
    </select>
  </div>

  <hr />

  <div class="form-group">
    <label for="loglevel-select">Log Level</label>
    <select id="loglevel-select" bind:value={$logLevel}>
      {#each Object.entries(LogLevel).filter( ([k, v]) => isNaN(Number(k)) ) as [name, value]}
        <option {value}>{titleCase(name.toLowerCase())}</option>
      {/each}
    </select>
  </div>

  <div class="form-group">
    <div class="section-header">Audio Preset Titles</div>
    <p class="description">Quick-access titles for audio tracks</p>
    <PresetTitleEditor
      titles={audioTitles}
      onTitlesChange={(newTitles) => (audioTitles = newTitles)}
    />
  </div>

  <div class="form-group">
    <div class="section-header">Subtitle Preset Titles</div>
    <p class="description">Quick-access titles for subtitle tracks</p>
    <PresetTitleEditor
      titles={subtitleTitles}
      onTitlesChange={(newTitles) => (subtitleTitles = newTitles)}
    />
  </div>

  <div class="actions">
    <button class="primary-button" onclick={saveSettings}>Save Settings</button>
  </div>
</div>

<style>
  .tab-container {
    max-width: 800px;
    margin: 0 auto;
  }

  h2 {
    margin-bottom: 1.5rem;
    color: var(--text-primary);
  }

  .form-group {
    margin-bottom: 1.5rem;
  }

  label,
  .section-header {
    display: block;
    margin-bottom: 0.5rem;
    font-weight: 500;
    color: var(--text-primary);
  }

  .description {
    font-size: 0.875rem;
    color: var(--text-secondary);
    margin-bottom: 0.5rem;
    font-style: italic;
  }

  select {
    width: 100%;
    padding: 0.5rem;
    border: 1px solid var(--border-color);
    border-radius: 4px;
    background-color: var(--bg-primary);
    color: var(--text-primary);
  }

  .primary-button {
    padding: 0.5rem 1rem;
    border: none;
    border-radius: 4px;
    font-weight: 500;
    cursor: pointer;
    transition: all 0.2s;
  }

  .primary-button {
    background-color: var(--accent-color);
    color: white;
  }

  .primary-button:hover {
    background-color: var(--accent-hover);
  }

  hr {
    margin: 2rem 0;
    border: none;
    border-top: 1px solid var(--border-color);
  }

  .actions {
    margin-top: 2rem;
  }
</style>
