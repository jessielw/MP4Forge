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
</script>

<Modal bind:isOpen {onClose}>
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
</Modal>
