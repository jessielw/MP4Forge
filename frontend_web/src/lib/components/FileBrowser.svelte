<script lang="ts">
  import { onMount } from "svelte";

  interface Props {
    onFileSelect: (filePath: string) => void;
    fileFilter?: (fileName: string) => boolean;
    title?: string;
    onClose?: () => void;
  }

  interface BrowseItem {
    name: string;
    path: string;
    is_dir: boolean;
    size: number | null;
  }

  interface BrowseResponse {
    current_path: string;
    parent_path: string | null;
    items: BrowseItem[];
    base_path: string;
  }

  let {
    onFileSelect,
    fileFilter,
    title = "Browse Files",
    onClose,
  }: Props = $props();

  let currentPath = $state("");
  let parentPath = $state<string | null>(null);
  let items = $state<BrowseItem[]>([]);
  let loading = $state(false);
  let error = $state("");
  let basePath = $state("");

  // load initial directory on mount
  onMount(() => {
    browseDirectory();
  });

  async function browseDirectory(path?: string) {
    loading = true;
    error = "";

    try {
      const response = await fetch("/api/browse", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ path: path || null }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || "Failed to browse directory");
      }

      const data: BrowseResponse = await response.json();
      currentPath = data.current_path;
      parentPath = data.parent_path;
      items = data.items;
      basePath = data.base_path;
    } catch (e) {
      error = e instanceof Error ? e.message : "Unknown error occurred";
    } finally {
      loading = false;
    }
  }

  function handleItemClick(item: BrowseItem) {
    if (loading) return; // prevent clicks while loading

    if (item.is_dir) {
      browseDirectory(item.path);
    } else {
      // check file filter if provided
      if (!fileFilter || fileFilter(item.name)) {
        onFileSelect(item.path);
      }
    }
  }

  function goUp() {
    if (parentPath) {
      browseDirectory(parentPath);
    }
  }

  function formatSize(bytes: number | null): string {
    if (bytes === null) return "";
    const units = ["B", "KB", "MB", "GB"];
    let size = bytes;
    let unitIndex = 0;
    while (size >= 1024 && unitIndex < units.length - 1) {
      size /= 1024;
      unitIndex++;
    }
    return `${size.toFixed(1)} ${units[unitIndex]}`;
  }

  function getFileIcon(item: BrowseItem): string {
    if (item.is_dir) return "📁";

    const ext = item.name.split(".").pop()?.toLowerCase();
    if (["mp4", "mkv", "avi", "mov", "webm"].includes(ext || "")) return "🎬";
    if (["mp3", "aac", "flac", "wav", "opus"].includes(ext || "")) return "🎵";
    if (["srt", "ass", "ssa", "sub"].includes(ext || "")) return "📝";
    return "📄";
  }

  function isFileSelectable(item: BrowseItem): boolean {
    if (item.is_dir) return true;
    return !fileFilter || fileFilter(item.name);
  }
</script>

<div class="file-browser">
  <div class="header">
    <h3>{title}</h3>
    {#if onClose}
      <button class="close-button" onclick={onClose} aria-label="Close">
        ✕
      </button>
    {/if}
    {#if error}
      <div class="error-message">{error}</div>
    {/if}
  </div>

  <div class="current-path">
    <button
      onclick={goUp}
      disabled={!parentPath || loading}
      class="nav-button"
      title="Go up"
    >
      ⬆️
    </button>
    <span class="path-text">{currentPath || "Loading..."}</span>
  </div>

  <div class="items-container">
    {#if loading}
      <div class="loading">Loading...</div>
    {:else if items.length === 0}
      <div class="empty">No items in this directory</div>
    {:else}
      {#each items as item (item.path)}
        <button
          class="item"
          class:disabled={!isFileSelectable(item)}
          onclick={() => handleItemClick(item)}
          disabled={!isFileSelectable(item)}
        >
          <span class="icon">{getFileIcon(item)}</span>
          <span class="name">{item.name}</span>
          {#if !item.is_dir && item.size !== null}
            <span class="size">{formatSize(item.size)}</span>
          {/if}
        </button>
      {/each}
    {/if}
  </div>
</div>

<style>
  .file-browser {
    border: 1px solid var(--border-color);
    border-radius: 8px;
    background: var(--bg-primary);
    overflow: hidden;
    display: flex;
    flex-direction: column;
    flex: 1;
  }

  .header {
    padding: 12px;
    border-bottom: 1px solid var(--border-color);
    background: var(--bg-secondary);
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 12px;
  }

  .header h3 {
    margin: 0;
    font-size: 1rem;
    color: var(--text-primary);
    flex: 1;
  }

  .close-button {
    background: none;
    border: none;
    font-size: 1.5rem;
    cursor: pointer;
    color: var(--text-secondary);
    padding: 4px 8px;
    line-height: 1;
    border-radius: 4px;
    flex-shrink: 0;
  }

  .close-button:hover {
    background: var(--bg-hover);
    color: var(--text-primary);
  }

  .error-message {
    color: var(--error-color, #ff4444);
    margin-top: 8px;
    font-size: 0.9em;
  }

  .current-path {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 8px 12px;
    background: var(--bg-secondary);
    border-bottom: 1px solid var(--border-color);
  }

  .nav-button {
    padding: 4px 8px;
    background: var(--bg-primary);
    border: 1px solid var(--border-color);
    border-radius: 4px;
    cursor: pointer;
    font-size: 1rem;
  }

  .nav-button:hover:not(:disabled) {
    background: var(--bg-hover);
  }

  .nav-button:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }

  .path-text {
    flex: 1;
    font-family: monospace;
    font-size: 0.9em;
    color: var(--text-secondary);
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .items-container {
    flex: 1;
    overflow-y: auto;
    padding: 4px;
  }

  .loading,
  .empty {
    padding: 2rem;
    text-align: center;
    color: var(--text-secondary);
  }

  .item {
    display: flex;
    align-items: center;
    gap: 8px;
    width: 100%;
    padding: 8px 12px;
    background: var(--bg-primary);
    border: none;
    border-radius: 4px;
    cursor: pointer;
    text-align: left;
    transition: background 0.15s;
    margin-bottom: 2px;
  }

  .item:hover:not(:disabled) {
    background: var(--bg-hover);
  }

  .item.disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }

  .icon {
    font-size: 1.2rem;
    flex-shrink: 0;
  }

  .name {
    flex: 1;
    color: var(--text-primary);
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .size {
    color: var(--text-secondary);
    font-size: 0.85em;
    flex-shrink: 0;
  }
</style>
