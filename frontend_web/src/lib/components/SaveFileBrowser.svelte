<script lang="ts">
  import { onMount } from "svelte";

  interface Props {
    onFileSelect: (filePath: string) => void;
    defaultExtension?: string;
    title?: string;
    onClose?: () => void;
    defaultFilename?: string;
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
    defaultExtension = ".mp4",
    title = "Save File",
    onClose,
    defaultFilename = "output.mp4",
  }: Props = $props();

  let currentPath = $state("");
  let parentPath = $state<string | null>(null);
  let items = $state<BrowseItem[]>([]);
  let loading = $state(false);
  let error = $state("");
  let filename = $state("");
  let pathSeparator = $state("\\"); // Will be set based on OS
  let showCreateFolder = $state(false);
  let newFolderName = $state("");

  // initialize filename from default
  onMount(() => {
    if (defaultFilename && !filename) {
      filename = defaultFilename;
    }
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

      // detect path separator from current path (backend always uses native separator)
      pathSeparator = currentPath.includes("\\") ? "\\" : "/";
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
      // if user clicks an existing file, use its name
      filename = item.name;
    }
  }

  function goUp() {
    if (parentPath) {
      browseDirectory(parentPath);
    }
  }

  function handleSave() {
    if (!filename.trim()) {
      error = "Please enter a filename";
      return;
    }

    let finalFilename = filename.trim();

    // auto-add extension if missing
    if (
      defaultExtension &&
      !finalFilename.toLowerCase().endsWith(defaultExtension.toLowerCase())
    ) {
      finalFilename += defaultExtension;
    }

    // construct full path
    const fullPath = currentPath + pathSeparator + finalFilename;
    onFileSelect(fullPath);
  }

  function handleCancel() {
    if (onClose) {
      onClose();
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

  function handleKeydown(e: KeyboardEvent) {
    if (e.key === "Enter") {
      handleSave();
    }
  }

  function toggleCreateFolder() {
    showCreateFolder = !showCreateFolder;
    newFolderName = "";
    error = "";
  }

  async function handleCreateFolder() {
    if (!newFolderName.trim()) {
      error = "Please enter a folder name";
      return;
    }

    const folderPath = currentPath + pathSeparator + newFolderName.trim();

    try {
      const response = await fetch("/api/create-folder", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ path: folderPath }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || "Failed to create folder");
      }

      // Refresh the directory listing
      await browseDirectory(currentPath);
      showCreateFolder = false;
      newFolderName = "";
      error = "";
    } catch (e) {
      error = e instanceof Error ? e.message : "Failed to create folder";
    }
  }
</script>

<div class="save-file-browser">
  <div class="header">
    <h3>{title}</h3>
    {#if onClose}
      <button class="close-button" onclick={handleCancel} aria-label="Close">
        ✕
      </button>
    {/if}
  </div>

  {#if error}
    <div class="error-message">{error}</div>
  {/if}

  <div class="current-path">
    <button
      onclick={goUp}
      disabled={!parentPath || loading}
      class="nav-button"
      title="Go up"
    >
      ⬆️ Up
    </button>
    <span class="path-text">{currentPath || "Loading..."}</span>
    <button
      onclick={toggleCreateFolder}
      class="create-folder-button"
      title="Create new folder"
      disabled={loading}
    >
      📁+ New Folder
    </button>
  </div>

  {#if showCreateFolder}
    <div class="create-folder-panel">
      <input
        type="text"
        bind:value={newFolderName}
        placeholder="Folder name..."
        onkeydown={(e) => e.key === "Enter" && handleCreateFolder()}
      />
      <button onclick={handleCreateFolder} class="confirm-button">Create</button
      >
      <button onclick={toggleCreateFolder} class="cancel-folder-button"
        >Cancel</button
      >
    </div>
  {/if}

  <div class="items-container">
    {#if loading}
      <div class="loading">Loading...</div>
    {:else if items.length === 0}
      <div class="empty">No items in this directory</div>
    {:else}
      {#each items as item (item.path)}
        <button
          class="item"
          class:directory={item.is_dir}
          onclick={() => handleItemClick(item)}
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

  <div class="filename-input">
    <label for="save-filename">Filename:</label>
    <input
      id="save-filename"
      type="text"
      bind:value={filename}
      onkeydown={handleKeydown}
      placeholder="output.mp4"
    />
    {#if defaultExtension}
      <span class="extension-hint">Extension: {defaultExtension}</span>
    {/if}
  </div>

  <div class="actions">
    <button class="cancel-button" onclick={handleCancel}>Cancel</button>
    <button class="save-button" onclick={handleSave}>Save</button>
  </div>
</div>

<style>
  .save-file-browser {
    display: flex;
    flex-direction: column;
    height: 600px;
    background-color: var(--bg-primary);
    border-radius: 8px;
    overflow: hidden;
  }

  .header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 1rem;
    background-color: var(--bg-secondary);
    border-bottom: 1px solid var(--border-color);
  }

  h3 {
    margin: 0;
    color: var(--text-primary);
    font-size: 1.25rem;
  }

  .close-button {
    background: none;
    border: none;
    font-size: 1.5rem;
    cursor: pointer;
    color: var(--text-secondary);
    padding: 0.25rem 0.5rem;
    transition: color 0.2s;
  }

  .close-button:hover {
    color: var(--text-primary);
  }

  .error-message {
    padding: 0.75rem;
    background-color: #fee;
    color: #c33;
    border-left: 3px solid #c33;
    margin: 0.5rem 1rem;
    border-radius: 4px;
  }

  .current-path {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.75rem 1rem;
    background-color: var(--bg-secondary);
    border-bottom: 1px solid var(--border-color);
  }

  .create-folder-panel {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.75rem 1rem;
    background-color: var(--bg-tertiary, var(--bg-secondary));
    border-bottom: 1px solid var(--border-color);
  }

  .create-folder-panel input {
    flex: 1;
    padding: 0.5rem;
    border: 1px solid var(--border-color);
    border-radius: 4px;
    background-color: var(--bg-primary);
    color: var(--text-primary);
  }

  .create-folder-button,
  .confirm-button,
  .cancel-folder-button {
    padding: 0.5rem 1rem;
    border: 1px solid var(--border-color);
    border-radius: 4px;
    cursor: pointer;
    font-weight: 500;
    transition: all 0.2s;
    white-space: nowrap;
  }

  .create-folder-button {
    background-color: var(--bg-primary);
    color: var(--text-primary);
    margin-left: auto;
  }

  .create-folder-button:hover:not(:disabled) {
    background-color: var(--bg-hover);
  }

  .create-folder-button:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }

  .confirm-button {
    background-color: #4caf50;
    color: white;
    border-color: #4caf50;
  }

  .confirm-button:hover {
    background-color: #45a049;
  }

  .cancel-folder-button {
    background-color: var(--bg-primary);
    color: var(--text-primary);
  }

  .cancel-folder-button:hover {
    background-color: var(--bg-hover);
  }

  .nav-button {
    padding: 0.5rem 1rem;
    background-color: var(--bg-primary);
    border: 1px solid var(--border-color);
    border-radius: 4px;
    cursor: pointer;
    color: var(--text-primary);
    font-weight: 500;
    transition: all 0.2s;
    white-space: nowrap;
  }

  .nav-button:hover:not(:disabled) {
    background-color: var(--bg-hover);
  }

  .nav-button:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }

  .path-text {
    font-family: monospace;
    font-size: 0.9rem;
    color: var(--text-secondary);
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .items-container {
    flex: 1;
    overflow-y: auto;
    padding: 0.5rem;
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
    gap: 0.75rem;
    padding: 0.75rem;
    width: 100%;
    background-color: var(--bg-primary);
    border: 1px solid transparent;
    border-radius: 4px;
    cursor: pointer;
    text-align: left;
    transition: all 0.2s;
    margin-bottom: 0.25rem;
  }

  .item:hover {
    background-color: var(--bg-hover);
    border-color: var(--border-color);
  }

  .item.directory {
    font-weight: 500;
  }

  .icon {
    font-size: 1.25rem;
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
    font-size: 0.875rem;
    color: var(--text-secondary);
    flex-shrink: 0;
  }

  .filename-input {
    padding: 1rem;
    background-color: var(--bg-secondary);
    border-top: 1px solid var(--border-color);
    border-bottom: 1px solid var(--border-color);
  }

  .filename-input label {
    display: block;
    margin-bottom: 0.5rem;
    font-weight: 500;
    color: var(--text-primary);
  }

  .filename-input input {
    width: 100%;
    padding: 0.5rem;
    border: 1px solid var(--border-color);
    border-radius: 4px;
    background-color: var(--bg-primary);
    color: var(--text-primary);
    font-size: 1rem;
  }

  .extension-hint {
    display: block;
    margin-top: 0.25rem;
    font-size: 0.875rem;
    color: var(--text-secondary);
  }

  .actions {
    display: flex;
    justify-content: flex-end;
    gap: 0.5rem;
    padding: 1rem;
    background-color: var(--bg-secondary);
  }

  .cancel-button,
  .save-button {
    padding: 0.5rem 1.5rem;
    border: none;
    border-radius: 4px;
    font-weight: 500;
    cursor: pointer;
    transition: all 0.2s;
  }

  .cancel-button {
    background-color: transparent;
    color: var(--text-secondary);
    border: 1px solid var(--border-color);
  }

  .cancel-button:hover {
    background-color: var(--bg-hover);
    color: var(--text-primary);
  }

  .save-button {
    background-color: #4caf50;
    color: white;
  }

  .save-button:hover {
    background-color: #45a049;
  }
</style>
