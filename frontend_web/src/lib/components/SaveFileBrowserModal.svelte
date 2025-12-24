<script lang="ts">
  import SaveFileBrowser from "./SaveFileBrowser.svelte";
  import Modal from "./Modal.svelte";

  interface Props {
    isOpen: boolean;
    onClose: () => void;
    onFileSelect: (filePath: string) => void;
    defaultExtension?: string;
    title?: string;
    defaultFilename?: string;
    initialPath?: string;
  }

  let {
    isOpen = $bindable(),
    onClose,
    onFileSelect,
    defaultExtension = ".mp4",
    title = "Save File",
    defaultFilename = "output.mp4",
    initialPath,
  }: Props = $props();

  function handleFileSelect(filePath: string) {
    onFileSelect(filePath);
    isOpen = false;
    onClose();
  }
</script>

<Modal bind:isOpen {onClose}>
  <SaveFileBrowser
    onFileSelect={handleFileSelect}
    {defaultExtension}
    {title}
    {defaultFilename}
    {initialPath}
    onClose={() => {
      isOpen = false;
      onClose();
    }}
  />
</Modal>
