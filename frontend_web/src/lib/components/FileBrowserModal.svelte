<script lang="ts">
  import FileBrowser from "./FileBrowser.svelte";
  import Modal from "./Modal.svelte";

  interface Props {
    isOpen: boolean;
    onClose: () => void;
    onFileSelect: (filePath: string) => void;
    fileFilter?: (fileName: string) => boolean;
    title?: string;
    initialPath?: string;
  }

  let {
    isOpen = $bindable(),
    onClose,
    onFileSelect,
    fileFilter,
    title = "Browse Files",
    initialPath,
  }: Props = $props();

  function handleFileSelect(filePath: string) {
    onFileSelect(filePath);
    isOpen = false;
    onClose();
  }
</script>

<Modal bind:isOpen {onClose}>
  <FileBrowser
    onFileSelect={handleFileSelect}
    {fileFilter}
    {title}
    {initialPath}
    onClose={() => {
      isOpen = false;
      onClose();
    }}
  />
</Modal>
