<script lang="ts">
  import FileInput from "./FileInput.svelte";
  import LanguageSelect from "./LanguageSelect.svelte";
  import { ApiClient, LogLevel } from "$lib/api";

  interface MediaInfoRow {
    property: string;
    value: string;
  }

  let videoFilePath = $state("");
  let language = $state("");
  let title = $state("");
  let delay = $state(0);
  let mediaInfo = $state<string>("");
  let mediaInfoRows = $state<MediaInfoRow[]>([]);
  let loading = $state(false);
  let error = $state("");

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
    if (!videoFilePath.trim()) {
      error = "Please select a file";
      return;
    }

    loading = true;
    error = "";
    mediaInfo = "";

    try {
      const response = await fetch("/api/mediainfo", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ file_path: videoFilePath }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || "Failed to load media info");
      }

      const data = await response.json();
      mediaInfo = data.mediainfo;

      // parse MediaInfo JSON to extract video track info
      parseVideoTrack(mediaInfo);
    } catch (e) {
      error = e instanceof Error ? e.message : "Unknown error occurred";
    } finally {
      loading = false;
    }
  }

  function parseVideoTrack(jsonString: string) {
    try {
      const parsed = JSON.parse(jsonString);
      const videoTrackData = parsed.tracks?.find(
        (t: any) => t["track_type"] === "Video"
      );

      if (videoTrackData) {
        // build dynamic rows for table using whitelist
        mediaInfoRows = [];

        // iterate through displayProperties to maintain order
        for (const [key, displayName] of Object.entries(displayProperties)) {
          const value = videoTrackData[key];

          if (value !== null && value !== undefined) {
            let displayValue = String(value);

            // format specific values
            if (key === "other_duration") {
              // we'll inject resolution in here since we want resolution before this
              const width = videoTrackData["width"];
              const height = videoTrackData["height"];
              if (width && height) {
                mediaInfoRows.push({
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
            mediaInfoRows.push({
              property: displayName,
              value: displayValue,
            });
          }
        }

        // extract language for auto-selection
        const languageValue = videoTrackData["language"];
        if (languageValue) {
          language = String(languageValue).toLowerCase();
        }

        // set title if available
        const titleValue = videoTrackData["title"];
        if (titleValue) {
          title = String(titleValue);
        }

        // set delay if available
        const delayValue =
          videoTrackData["source_delay"] || videoTrackData["delay"] || 0;
        if (delayValue) {
          delay = Number(delayValue);
        }
      }
    } catch (e) {
      console.error("Failed to parse MediaInfo:", e);
    }
  }

  function handleFileSelect(_filePath: string) {
    ApiClient.logToBackend(
      `Video file selected: ${videoFilePath}`,
      LogLevel.DEBUG
    );
    // auto load MediaInfo on file select
    loadMediaInfo();
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
      bind:value={videoFilePath}
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
      bind:value={language}
      id="video-language"
      label="Language"
    />
  </div>

  <div class="form-group">
    <label for="video-title">Title</label>
    <input
      id="video-title"
      type="text"
      bind:value={title}
      placeholder="Enter title..."
    />
  </div>

  <div class="form-group">
    <label for="video-delay">Delay (ms)</label>
    <input id="video-delay" type="number" bind:value={delay} />
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
