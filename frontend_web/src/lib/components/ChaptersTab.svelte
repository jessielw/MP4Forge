<script lang="ts">
  import FileInput from "./FileInput.svelte";
  import { ApiClient, LogLevel } from "$lib/api";
  import { chaptersText, videoTrack } from "$lib/stores/tracks";

  let loading = $state(false);
  let error = $state("");
  let chapterFilePath = $state("");
  let lastExtractedVideoPath = $state<string>("");

  // when video file changes, auto-extract chapters if available
  $effect(() => {
    const videoPath = $videoTrack.filePath;
    if (videoPath && videoPath !== lastExtractedVideoPath && !loading) {
      lastExtractedVideoPath = videoPath;
      extractChaptersFromVideo(videoPath);
    }
  });

  async function extractChaptersFromVideo(filePath: string) {
    if (!filePath) return;

    loading = true;
    error = "";

    try {
      const response = await fetch(`/api/extract-chapters`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ file_path: filePath }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || "Failed to extract chapters");
      }

      const data = await response.json();
      if (data.chapters) {
        chaptersText.set(data.chapters);
        await ApiClient.logToBackend(
          `Extracted chapters from: ${filePath}`,
          LogLevel.INFO
        );
      }
    } catch (e) {
      const errorMsg =
        e instanceof Error ? e.message : "Unknown error occurred";
      error = errorMsg;
      await ApiClient.logToBackend(
        `Chapter extraction error: ${errorMsg}`,
        LogLevel.ERROR
      );
    } finally {
      loading = false;
    }
  }

  async function handleFileSelect(filePath: string) {
    chapterFilePath = filePath;

    // check if it's a text file
    if (filePath.toLowerCase().endsWith(".txt")) {
      await loadChaptersFromTextFile(filePath);
    } else {
      // try to extract chapters from video file
      await extractChaptersFromVideo(filePath);
    }
  }

  async function loadChaptersFromTextFile(filePath: string) {
    loading = true;
    error = "";

    try {
      const response = await fetch(`/api/read-file`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ file_path: filePath }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || "Failed to read file");
      }

      const data = await response.json();
      chaptersText.set(data.content);
      await ApiClient.logToBackend(
        `Loaded chapters from: ${filePath}`,
        LogLevel.INFO
      );
    } catch (e) {
      const errorMsg =
        e instanceof Error ? e.message : "Unknown error occurred";
      error = errorMsg;
      await ApiClient.logToBackend(
        `Failed to load chapter file: ${errorMsg}`,
        LogLevel.WARNING
      );
    } finally {
      loading = false;
    }
  }

  function isChapterOrVideoFile(filePath: string): boolean {
    const ext = filePath.toLowerCase();
    return ext.endsWith(".txt");
  }
</script>

<div class="tab-container">
  <h2>Chapters</h2>

  <div class="form-group">
    <FileInput
      value={chapterFilePath}
      onFileSelect={handleFileSelect}
      fileFilter={isChapterOrVideoFile}
      label="Chapter File or Video"
      id="chapter-file-path"
    />
  </div>

  {#if loading}
    <p class="loading">Extracting chapters...</p>
  {/if}

  {#if error}
    <p class="error">{error}</p>
  {/if}

  <div class="editor-section">
    <label for="chapter-editor" class="editor-label">Editor</label>
    <textarea
      id="chapter-editor"
      bind:value={$chaptersText}
      placeholder="CHAPTER01=00:00:00.000&#10;CHAPTER01NAME=Chapter 1&#10;CHAPTER02=00:05:00.000&#10;CHAPTER02NAME=Chapter 2"
      rows="20"
      spellcheck="false"
    ></textarea>
    <p class="hint">
      OGM chapter format. Paste chapters or load from a video/text file.
    </p>
  </div>
</div>

<style>
  .tab-container {
    max-width: 1000px;
    margin: 0 auto;
    padding: 1rem;
  }

  h2 {
    color: var(--text-primary);
    margin-bottom: 1.5rem;
  }

  .form-group {
    margin-bottom: 1.5rem;
  }

  .loading {
    color: var(--accent-color);
    margin-bottom: 1rem;
    font-style: italic;
  }

  .error {
    color: #ff4444;
    margin-bottom: 1rem;
    padding: 0.5rem;
    background-color: rgba(255, 68, 68, 0.1);
    border-radius: 4px;
  }

  .editor-section {
    margin-top: 1.5rem;
  }

  .editor-label {
    display: block;
    color: var(--text-primary);
    font-weight: 500;
    margin-bottom: 0.5rem;
  }

  textarea {
    width: 100%;
    padding: 0.75rem;
    border: 1px solid var(--border-color);
    border-radius: 4px;
    background-color: var(--bg-primary);
    color: var(--text-primary);
    font-family: "Fira Mono", "Courier New", monospace;
    font-size: 0.9rem;
    line-height: 1.5;
    resize: vertical;
    transition: border-color 0.2s;
  }

  textarea:focus {
    outline: none;
    border-color: var(--accent-color);
  }

  textarea::placeholder {
    color: var(--text-secondary);
    opacity: 0.6;
  }

  .hint {
    margin-top: 0.5rem;
    color: var(--text-secondary);
    font-size: 0.85rem;
  }
</style>
