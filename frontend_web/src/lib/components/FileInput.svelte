<script lang="ts">
  import FileBrowserModal from "./FileBrowserModal.svelte";

  interface Props {
    value: string;
    onFileSelect: (filePath: string) => void;
    fileFilter?: (fileName: string) => boolean;
    placeholder?: string;
    browserTitle?: string;
    label?: string;
    id?: string;
  }

  let {
    value = $bindable(),
    onFileSelect,
    fileFilter,
    placeholder = "Click Browse to select a file...",
    browserTitle = "Select File",
    label,
    id,
  }: Props = $props();

  let showBrowserModal = $state(false);

  function handleFileSelect(filePath: string) {
    value = filePath;
    onFileSelect(filePath);
  }
</script>

{#if label && id}
  <label for={id}>{label}</label>
{/if}

<div class="file-input-group">
  <input {id} type="text" bind:value {placeholder} readonly />
  <button
    onclick={() => (showBrowserModal = true)}
    class="browse-button"
    type="button"
  >
    📁 Browse
  </button>
</div>

<FileBrowserModal
  bind:isOpen={showBrowserModal}
  onClose={() => (showBrowserModal = false)}
  onFileSelect={handleFileSelect}
  {fileFilter}
  title={browserTitle}
  initialPath={value}
/>

<style>
  .file-input-group {
    display: flex;
    gap: 8px;
    align-items: center;
  }

  .file-input-group input {
    flex: 1;
    cursor: default;
    background: var(--bg-secondary);
    padding: 0.5rem;
    border: 1px solid var(--border-color);
    border-radius: 4px;
    color: var(--text-primary);
  }

  .browse-button {
    padding: 0.5rem 1rem;
    background: var(--bg-primary);
    border: 1px solid var(--border-color);
    border-radius: 4px;
    cursor: pointer;
    color: var(--text-primary);
    white-space: nowrap;
  }

  .browse-button:hover {
    background: var(--bg-hover);
  }

  label {
    display: block;
    margin-bottom: 0.5rem;
    font-weight: 500;
    color: var(--text-primary);
  }
</style>
