<script lang="ts">
	import { audioPresetTitles } from '$lib/stores/settings';

	let audioFiles = $state<string[]>([]);
</script>

<div class="tab-container">
	<h2>Audio Tracks</h2>
	<p class="placeholder">Audio track management - Coming soon</p>

	<button class="add-button" onclick={() => console.log('Add audio track')}>
		+ Add Audio Track
	</button>

	{#if audioFiles.length === 0}
		<div class="empty-state">No audio tracks added</div>
	{/if}
</div>

<style>
	.tab-container {
		max-width: 800px;
		margin: 0 auto;
	}

	.placeholder {
		color: var(--text-secondary);
		margin-bottom: 1rem;
	}

	.add-button {
		padding: 0.75rem 1.5rem;
		background-color: var(--accent-color);
		color: white;
		border: none;
		border-radius: 4px;
		font-weight: 500;
		transition: background-color 0.2s;
	}

	.add-button:hover {
		background-color: var(--accent-hover);
	}

	.empty-state {
		margin-top: 2rem;
		padding: 2rem;
		text-align: center;
		color: var(--text-secondary);
		border: 1px dashed var(--border-color);
		border-radius: 8px;
	}
</style>
