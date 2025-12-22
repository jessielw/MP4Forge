<script lang="ts">
  import {
    theme,
    audioPresetTitles,
    subtitlePresetTitles,
  } from "$lib/stores/settings";
  import PresetTitleEditor from "./PresetTitleEditor.svelte";

  let audioTitles = $state([...$audioPresetTitles]);
  let subtitleTitles = $state([...$subtitlePresetTitles]);

  function saveSettings() {
    audioPresetTitles.set(audioTitles);
    subtitlePresetTitles.set(subtitleTitles);
    alert("Settings saved successfully!");
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

  <div class="form-group">
    <label for="mp4box-path">Mp4Box Path</label>
    <div class="input-group">
      <input
        id="mp4box-path"
        type="text"
        readonly
        value="/usr/local/bin/mp4box"
      />
      <button class="browse-button">📁 Browse</button>
    </div>
  </div>

  <hr />

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

  .input-group {
    display: flex;
    gap: 0.5rem;
  }

  input,
  select {
    width: 100%;
    padding: 0.5rem;
    border: 1px solid var(--border-color);
    border-radius: 4px;
    background-color: var(--bg-primary);
    color: var(--text-primary);
  }

  .input-group input {
    flex: 1;
  }

  .browse-button,
  .primary-button {
    padding: 0.5rem 1rem;
    border: none;
    border-radius: 4px;
    font-weight: 500;
    cursor: pointer;
    transition: all 0.2s;
  }

  .browse-button {
    background-color: var(--bg-secondary);
    color: var(--text-primary);
    border: 1px solid var(--border-color);
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
