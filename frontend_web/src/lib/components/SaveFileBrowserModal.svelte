<script lang="ts">
  import SaveFileBrowser from "./SaveFileBrowser.svelte";

  interface Props {
    isOpen: boolean;
    onClose: () => void;
    onFileSelect: (filePath: string) => void;
    defaultExtension?: string;
    title?: string;
    defaultFilename?: string;
  }

  let {
    isOpen = $bindable(),
    onClose,
    onFileSelect,
    defaultExtension = ".mp4",
    title = "Save File",
    defaultFilename = "output.mp4",
  }: Props = $props();

  function handleFileSelect(filePath: string) {
    onFileSelect(filePath);
    isOpen = false;
    onClose();
  }

  function handleBackdropClick(e: MouseEvent) {
    if (e.target === e.currentTarget) {
      isOpen = false;
      onClose();
    }
  }

  function handleKeydown(e: KeyboardEvent) {
    if (e.key === "Escape") {
      isOpen = false;
      onClose();
    }
  }
</script>

{#if isOpen}
  <div
    class="modal-backdrop"
    onclick={handleBackdropClick}
    onkeydown={handleKeydown}
    role="button"
    tabindex="-1"
  >
    <div class="modal-content" role="dialog" aria-modal="true">
      <SaveFileBrowser
        onFileSelect={handleFileSelect}
        {defaultExtension}
        {title}
        {defaultFilename}
        onClose={() => {
          isOpen = false;
          onClose();
        }}
      />
    </div>
  </div>
{/if}

<style>
  .modal-backdrop {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background-color: rgba(0, 0, 0, 0.5);
    display: flex;
    justify-content: center;
    align-items: center;
    z-index: 1000;
    padding: 1rem;
  }

  .modal-content {
    width: 100%;
    max-width: 800px;
    max-height: 90vh;
    background-color: var(--bg-primary);
    border-radius: 8px;
    box-shadow:
      0 4px 6px rgba(0, 0, 0, 0.1),
      0 10px 20px rgba(0, 0, 0, 0.2);
    overflow: hidden;
  }
</style>
