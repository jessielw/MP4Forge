<script lang="ts">
	import FileBrowser from './FileBrowser.svelte';

	interface Props {
		isOpen: boolean;
		onClose: () => void;
		onFileSelect: (filePath: string) => void;
		fileFilter?: (fileName: string) => boolean;
		title?: string;
	}

	let { isOpen = $bindable(), onClose, onFileSelect, fileFilter, title = 'Browse Files' }: Props = $props();

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
		if (e.key === 'Escape') {
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
			<FileBrowser
				onFileSelect={handleFileSelect}
				{fileFilter}
				{title}
				onClose={() => { isOpen = false; onClose(); }}
			/>
		</div>
	</div>
{/if}

<style>
	.modal-backdrop {
		position: fixed;
		top: 0;
		left: 0;
		width: 100%;
		height: 100%;
		background: rgba(0, 0, 0, 0.5);
		display: flex;
		align-items: center;
		justify-content: center;
		z-index: 1000;
		padding: 20px;
	}

	.modal-content {
		background: var(--bg-primary);
		border-radius: 8px;
		box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
		max-width: 700px;
		width: 100%;
		max-height: 80vh;
		overflow: hidden;
	}
</style>
