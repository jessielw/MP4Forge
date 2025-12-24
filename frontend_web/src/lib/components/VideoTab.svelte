<script lang="ts">
  import FileInput from "./FileInput.svelte";
  import LanguageSelect from "./LanguageSelect.svelte";
  import TrackImportDialog from "./TrackImportDialog.svelte";
  import { ApiClient, LogLevel } from "$lib/api";
  import { videoTrack, audioTracks, subtitleTracks } from "$lib/stores/tracks";
  import { outputTabSetValue } from "$lib/stores/navigation";
  import { parse, join } from "pathe";

  interface MediaInfoRow {
    property: string;
    value: string;
  }

  interface Track {
    type: "Video" | "Audio" | "Subtitle" | "Chapters";
    id: string;
    format: string;
    language?: string;
    flags?: string;
    title?: string;
    selected: boolean;
    data: any;
  }

  let error = $state("");

  // track import dialog state
  let showImportDialog = $state(false);
  let importTracks = $state<Track[]>([]);
  let importFilename = $state("");

  // compute mediaInfoRows directly from videoTrack.mediaInfoData
  const mediaInfoRows = $derived.by(() => {
    const data = $videoTrack.mediaInfoData;
    if (!data) return [];

    const rows: MediaInfoRow[] = [];

    // iterate through displayProperties to maintain order
    for (const [key, displayName] of Object.entries(displayProperties)) {
      const value = data[key];

      if (value !== null && value !== undefined) {
        let displayValue = String(value);

        // format specific values
        if (key === "other_duration") {
          // we'll inject resolution in here since we want resolution before this
          const width = data["width"];
          const height = data["height"];
          if (width && height) {
            rows.push({
              property: "Resolution",
              value: `${width} x ${height}`,
            });
          }
          // now continue getting the duration
          displayValue = "";
          if (Array.isArray(value) && value.length > 0) {
            displayValue = value[0];
          }
        } else if (key === "other_bit_rate" && Array.isArray(value)) {
          displayValue = "";
          if (value.length > 0) {
            displayValue = value[0];
          }
        }

        // push whitelisted property/value pair
        rows.push({
          property: displayName,
          value: displayValue,
        });
      }
    }

    return rows;
  });

  // properties to display and their display names (in order)
  const displayProperties: Record<string, string> = {
    format: "Format",
    format_profile: "Profile",
    codec_id: "Codec ID",
    other_duration: "Duration",
    other_bit_rate: "Bit Rate",
    frame_rate: "Frame Rate",
    frame_rate_mode: "Frame Rate Mode",
    bit_depth: "Bit Depth",
    color_space: "Color Space",
    chroma_subsampling: "Chroma Subsampling",
    scan_type: "Scan Type",
    hdr_format: "HDR Format",
    color_primaries: "Color Primaries",
    transfer_characteristics: "Transfer Characteristics",
    matrix_coefficients: "Matrix Coefficients",
  };

  async function loadMediaInfo() {
    if (!$videoTrack.filePath.trim()) {
      error = "Please select a file";
      return;
    }

    error = "";

    try {
      const response = await fetch("/api/mediainfo", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ file_path: $videoTrack.filePath }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || "Failed to load media info");
      }

      const data = await response.json();

      // store in videoTrack for persistence
      videoTrack.update((t) => ({ ...t, mediaInfo: data.mediainfo }));

      // parse MediaInfo and extract video track data
      const parsed = JSON.parse(data.mediainfo);
      const videoTrackData = parsed.tracks?.find(
        (t: any) => t["track_type"] === "Video"
      );

      if (videoTrackData) {
        // store raw data and auto-populate fields
        videoTrack.update((t) => ({
          ...t,
          mediaInfoData: videoTrackData,
          language: videoTrackData["language"]?.toLowerCase() || t.language,
          title: videoTrackData["title"] || t.title,
          delay:
            videoTrackData["source_delay"] ||
            videoTrackData["delay"] ||
            t.delay,
        }));
      }

      // check if file is MP4/M4V - show import dialog
      const ext = $videoTrack.filePath.toLowerCase();
      if (ext.endsWith(".mp4") || ext.endsWith(".m4v")) {
        showTrackImportDialog(data.mediainfo);
      }
    } catch (e) {
      error = e instanceof Error ? e.message : "Unknown error occurred";
    }
  }

  function showTrackImportDialog(jsonString: string) {
    try {
      const parsed = JSON.parse(jsonString);
      const tracks: Track[] = [];

      // extract all tracks from MediaInfo
      for (const track of parsed.tracks || []) {
        const trackType = track["track_type"];

        const trackIdFromMediaInfo = track["track_id"];

        if (trackType === "Video") {
          tracks.push({
            type: "Video",
            id: String(trackIdFromMediaInfo),
            format: `${track["format"] || "Unknown"} (${track["width"] || 0}x${track["height"] || 0})`,
            language: track["language"]?.toUpperCase(),
            flags: undefined,
            title: track["title"],
            selected: true, // video always selected
            data: track,
          });
        } else if (trackType === "Audio") {
          tracks.push({
            type: "Audio",
            id: String(trackIdFromMediaInfo),
            format: `${track["format"] || "Unknown"} (${track["channel_s"] || track["channels"] || "?"}ch)`,
            language: track["language"]?.toUpperCase(),
            flags: track["default"] === "Yes" ? "Default" : undefined,
            title: track["title"],
            selected: true,
            data: track,
          });
        } else if (trackType === "Text") {
          const isForced = track["forced"] === "Yes";
          tracks.push({
            type: "Subtitle",
            id: String(trackIdFromMediaInfo),
            format: track["format"] || "Timed Text",
            language: track["language"]?.toUpperCase(),
            flags: isForced ? "Forced" : undefined,
            title: track["title"],
            selected: true,
            data: track,
          });
        } else if (trackType === "Menu") {
          tracks.push({
            type: "Chapters",
            id: "-",
            format: "Numbered (01 - ...)",
            language: undefined,
            flags: undefined,
            title: undefined,
            selected: true,
            data: track,
          });
        }
      }

      importTracks = tracks;
      importFilename =
        $videoTrack.filePath.split(/[/\\]/).pop() || $videoTrack.filePath;
      showImportDialog = true;
    } catch (e) {
      console.error("Failed to parse tracks for import:", e);
    }
  }

  function handleImportConfirm(selectedTracks: Track[]) {
    const audioToImport = selectedTracks.filter(
      (t) => t.type === "Audio" && t.selected
    );
    const subtitlesToImport = selectedTracks.filter(
      (t) => t.type === "Subtitle" && t.selected
    );

    // reset existing tracks first (new video file = fresh start)
    audioTracks.set([]);
    subtitleTracks.set([]);

    // add audio tracks
    if (audioToImport.length > 0) {
      const newTracks = audioToImport.map((track, idx) => ({
        id: `audio-${Date.now()}-${idx}`,
        filePath: $videoTrack.filePath,
        language: track.language?.toLowerCase() || "",
        title: track.title || "",
        delay: 0,
        isDefault: idx === 0,
        trackId: parseInt(track.id), // track ID from MediaInfo
        mediaInfo: $videoTrack.mediaInfo,
        mediaInfoData: track.data,
      }));
      audioTracks.set(newTracks);
    }

    // add subtitle tracks
    if (subtitlesToImport.length > 0) {
      const newTracks = subtitlesToImport.map((track, idx) => ({
        id: `subtitle-${Date.now()}-${idx}`,
        filePath: $videoTrack.filePath,
        language: track.language?.toLowerCase() || "",
        title: track.title || "",
        isDefault: idx === 0,
        isForced: track.flags === "Forced",
        trackId: parseInt(track.id), // track ID from MediaInfo
        mediaInfo: $videoTrack.mediaInfo,
        mediaInfoData: track.data,
      }));
      subtitleTracks.set(newTracks);
    }
  }

  function handleFileSelect(filePath: string) {
    videoTrack.update((t) => ({ ...t, filePath }));
    ApiClient.logToBackend(`Video file selected: ${filePath}`, LogLevel.DEBUG);
    // auto load MediaInfo on file select
    loadMediaInfo();
    // update value of outputTabSetValue store
    if (filePath) {
      const parsedPath = parse(filePath);
      filePath = join(
        parsedPath.dir,
        `${parsedPath.name}_muxed${parsedPath.ext}`
      );
    }
    outputTabSetValue.set(filePath);
  }

  function isVideoFile(fileName: string): boolean {
    const videoExtensions = [
      ".avi",
      ".mp4",
      ".m1v",
      ".m2v",
      ".m4v",
      ".264",
      ".h264",
      ".hevc",
      ".h265",
      ".avc",
    ];
    return videoExtensions.some((ext) => fileName.toLowerCase().endsWith(ext));
  }
</script>

<div class="tab-container">
  <div class="form-group">
    <FileInput
      bind:value={$videoTrack.filePath}
      onFileSelect={handleFileSelect}
      fileFilter={isVideoFile}
      label="Video File"
      id="video-file-path"
    />
    {#if error}
      <div class="error-message">{error}</div>
    {/if}
  </div>

  <div class="form-group">
    <LanguageSelect
      bind:value={$videoTrack.language}
      id="video-language"
      label="Language"
    />
  </div>

  <div class="form-group">
    <label for="video-title">Title</label>
    <input
      id="video-title"
      type="text"
      bind:value={$videoTrack.title}
      placeholder="Enter title..."
    />
  </div>

  <div class="form-group">
    <label for="video-delay">Delay (ms)</label>
    <input id="video-delay" type="number" bind:value={$videoTrack.delay} />
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

<!-- track import dialog -->
<TrackImportDialog
  bind:isOpen={showImportDialog}
  filename={importFilename}
  tracks={importTracks}
  onConfirm={handleImportConfirm}
/>

<style>
  .error-message {
    color: var(--error-color, #ff4444);
    margin-top: 4px;
    font-size: 0.9em;
  }

  .tab-container {
    max-width: 800px;
    margin: 0 auto;
  }

  .form-group {
    margin-bottom: 1rem;
  }

  .section-label {
    display: block;
    margin-bottom: 0.5rem;
    font-weight: 500;
    color: var(--text-primary);
  }

  label {
    display: block;
    margin-bottom: 0.5rem;
    font-weight: 500;
    color: var(--text-primary);
  }

  input {
    width: 100%;
    padding: 0.5rem;
    border: 1px solid var(--border-color);
    border-radius: 4px;
    background-color: var(--bg-primary);
    color: var(--text-primary);
  }

  .mediainfo-table {
    max-height: 300px;
    border: 1px solid var(--border-color);
    border-radius: 4px;
    overflow-x: auto;
  }

  table {
    width: 100%;
    border-collapse: collapse;
  }

  thead {
    background: var(--bg-secondary);
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
