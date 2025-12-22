<script lang="ts">
  import FileInput from "./FileInput.svelte";
  import LanguageSelect from "./LanguageSelect.svelte";
  import MultiTrackWidget from "./MultiTrackWidget.svelte";
  import {
    subtitleTracks,
    setDefaultSubtitleTrack,
    type SubtitleTrack,
  } from "$lib/stores/tracks";

  let activeTrackId = $state("");

  // use store directly - no local copy to avoid loops
  const tracks = $derived($subtitleTracks);

  // set initial active track when tracks are added
  $effect(() => {
    if (tracks.length > 0 && !activeTrackId) {
      activeTrackId = tracks[0].id;
    }
  });

  const activeTrack = $derived(tracks.find((t) => t.id === activeTrackId));

  let tabs = $derived(
    tracks.map((track, idx) => ({
      id: track.id,
      label: `Track ${idx + 1}`,
    }))
  );

  // properties to display in MediaInfo table for subtitles
  const subtitleDisplayProperties: Record<string, string> = {
    format: "Format",
    codec_id: "Codec ID",
    other_duration: "Duration",
    count_of_elements: "Element Count",
    stream_size: "Stream Size",
  };

  let loading = $state(false);

  // compute mediaInfoRows directly from mediaInfoData
  const mediaInfoRows = $derived.by(() => {
    const data = activeTrack?.mediaInfoData;
    if (!data) return [];

    const rows: Array<{ property: string; value: string }> = [];

    for (const [key, displayName] of Object.entries(
      subtitleDisplayProperties
    )) {
      const value = data[key];

      if (value !== null && value !== undefined) {
        let displayValue = String(value);

        if (key === "other_duration" && Array.isArray(value)) {
          displayValue = value[0] || "";
        }

        rows.push({
          property: displayName,
          value: displayValue,
        });
      }
    }

    return rows;
  });

  function addTrack() {
    const newTrack: SubtitleTrack = {
      id: `subtitle-${Date.now()}`,
      filePath: "",
      language: "",
      title: "",
      isDefault: $subtitleTracks.length === 0, // first track is default
      isForced: false,
    };

    subtitleTracks.update((t) => [...t, newTrack]);
    activeTrackId = newTrack.id;
  }

  function removeTrack(id: string) {
    subtitleTracks.update((t) => {
      const filtered = t.filter((track) => track.id !== id);
      // if removed track was default, make first track default
      if (filtered.length > 0 && !filtered.some((t) => t.isDefault)) {
        filtered[0].isDefault = true;
      }
      return filtered;
    });

    if (activeTrackId === id && $subtitleTracks.length > 0) {
      activeTrackId = $subtitleTracks[0].id;
    }
  }

  function reorderTracks(newTabs: Array<{ id: string; label: string }>) {
    // create a map of current tracks by id for fast lookup
    const trackMap = new Map(tracks.map((t) => [t.id, t]));

    // reorder tracks based on new tab order
    const reordered = newTabs
      .map((tab) => trackMap.get(tab.id))
      .filter(Boolean) as SubtitleTrack[];

    subtitleTracks.set(reordered);
  }

  function updateTrack(updates: Partial<SubtitleTrack>) {
    if (!activeTrack) return;

    subtitleTracks.update((t) =>
      t.map((track) =>
        track.id === activeTrackId ? { ...track, ...updates } : track
      )
    );
  }

  function handleDefaultChange(checked: boolean) {
    if (checked && activeTrack) {
      setDefaultSubtitleTrack(activeTrack.id);
    }
  }

  async function loadMediaInfo() {
    if (!activeTrack?.filePath || loading) return;

    // don't reload if we already have MediaInfo for this file
    if (activeTrack.mediaInfoData) return;

    loading = true;
    try {
      const response = await fetch("/api/mediainfo", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ file_path: activeTrack.filePath }),
      });

      if (response.ok) {
        const data = await response.json();
        const parsed = JSON.parse(data.mediainfo);
        const subtitleTrackData = parsed.tracks?.find(
          (t: any) => t["track_type"] === "Text"
        );

        if (subtitleTrackData) {
          updateTrack({
            mediaInfo: data.mediainfo,
            mediaInfoData: subtitleTrackData,
            language:
              subtitleTrackData["language"]?.toLowerCase() ||
              activeTrack.language,
            title: subtitleTrackData["title"] || activeTrack.title,
          });
        }
      }
    } catch (e) {
      console.error("Failed to load MediaInfo:", e);
    } finally {
      loading = false;
    }
  }

  function handleFileSelect(filePath: string) {
    updateTrack({ filePath });
    loadMediaInfo();
  }

  function isSubtitleFile(fileName: string): boolean {
    const subtitleExtensions = [
      ".srt",
      ".ass",
      ".ssa",
      ".sub",
      ".idx",
      ".vtt",
      ".sup",
      ".mp4",
      ".m4v",
    ];
    return subtitleExtensions.some((ext) =>
      fileName.toLowerCase().endsWith(ext)
    );
  }
</script>

<div class="tab-container">
  <h2>Subtitle Tracks</h2>

  {#if tracks.length === 0}
    <div class="empty-state">
      <p>No subtitle tracks added</p>
      <button class="add-button" onclick={addTrack}>+ Add Subtitle Track</button
      >
    </div>
  {:else}
    <MultiTrackWidget
      {tabs}
      bind:activeTabId={activeTrackId}
      onAddTrack={addTrack}
      onRemoveTrack={removeTrack}
      onReorderTabs={reorderTracks}
    >
      {#if activeTrack}
        <div class="track-form">
          <div class="form-group">
            <FileInput
              value={activeTrack.filePath}
              onFileSelect={handleFileSelect}
              fileFilter={isSubtitleFile}
              label="Subtitle File"
              id="subtitle-file-path"
            />
          </div>

          <div class="form-group">
            <LanguageSelect
              bind:value={activeTrack.language}
              id="subtitle-language"
              label="Language"
            />
          </div>

          <div class="form-group">
            <label for="subtitle-title">Title</label>
            <input
              id="subtitle-title"
              type="text"
              value={activeTrack.title}
              oninput={(e) => updateTrack({ title: e.currentTarget.value })}
              placeholder="Enter title..."
            />
          </div>

          <div class="form-group checkboxes">
            <label class="checkbox-label">
              <input
                type="checkbox"
                checked={activeTrack.isDefault}
                onchange={(e) => handleDefaultChange(e.currentTarget.checked)}
              />
              Default
            </label>

            <label class="checkbox-label">
              <input
                type="checkbox"
                checked={activeTrack.isForced}
                onchange={(e) =>
                  updateTrack({ isForced: e.currentTarget.checked })}
              />
              Forced
            </label>
          </div>

          {#if mediaInfoRows.length > 0}
            <div class="form-group">
              <div class="section-label">MediaInfo</div>
              <div class="mediainfo-table">
                <table>
                  <thead>
                    <tr>
                      <th>Property</th>
                      <th>Value</th>
                    </tr>
                  </thead>
                  <tbody>
                    {#each mediaInfoRows as row}
                      <tr>
                        <td>{row.property}</td>
                        <td>{row.value}</td>
                      </tr>
                    {/each}
                  </tbody>
                </table>
              </div>
            </div>
          {/if}
        </div>
      {/if}
    </MultiTrackWidget>
  {/if}
</div>

<style>
  .tab-container {
    max-width: 900px;
    margin: 0 auto;
  }

  h2 {
    margin-bottom: 1.5rem;
    color: var(--text-primary);
  }

  .empty-state {
    margin-top: 2rem;
    padding: 3rem 2rem;
    text-align: center;
    border: 2px dashed var(--border-color);
    border-radius: 8px;
  }

  .empty-state p {
    color: var(--text-secondary);
    margin-bottom: 1rem;
  }

  .add-button {
    padding: 0.75rem 1.5rem;
    background: #0066cc;
    color: white;
    border: none;
    border-radius: 4px;
    font-weight: 500;
    cursor: pointer;
    transition: background 0.2s;
  }

  .add-button:hover {
    background: #0052a3;
  }

  .track-form {
    display: flex;
    flex-direction: column;
    gap: 1rem;
  }

  .form-group {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
  }

  .form-group.checkboxes {
    flex-direction: row;
    gap: 2rem;
  }

  label {
    font-weight: 500;
    color: var(--text-primary);
  }

  input[type="text"] {
    width: 100%;
    padding: 0.5rem;
    border: 1px solid var(--border-color);
    border-radius: 4px;
    background: var(--bg-primary);
    color: var(--text-primary);
  }

  .checkbox-label {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    cursor: pointer;
  }

  .checkbox-label input[type="checkbox"] {
    width: 18px;
    height: 18px;
    cursor: pointer;
  }

  .section-label {
    font-weight: 600;
    color: var(--text-primary);
    margin-top: 0.5rem;
  }

  .mediainfo-table {
    max-height: 300px;
    border: 1px solid var(--border-color);
    border-radius: 4px;
    overflow: auto;
  }

  table {
    width: 100%;
    border-collapse: collapse;
  }

  thead {
    background: var(--bg-secondary);
    position: sticky;
    top: 0;
  }

  th {
    text-align: left;
    padding: 0.75rem;
    font-weight: 600;
    color: var(--text-primary);
    border-bottom: 1px solid var(--border-color);
  }

  td {
    padding: 0.75rem;
    color: var(--text-primary);
    border-bottom: 1px solid var(--border-color);
  }

  tbody tr:last-child td {
    border-bottom: none;
  }

  tbody tr:nth-child(even) {
    background: var(--bg-secondary);
  }

  tbody tr:hover {
    background: var(--bg-hover);
  }
</style>
