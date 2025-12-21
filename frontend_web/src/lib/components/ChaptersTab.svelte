<script lang="ts">
	let chaptersText = $state('');
</script>

<div class="tab-container">
	<h2>Chapters</h2>
	<p class="placeholder">Chapter editor - Coming soon</p>

	<textarea
		bind:value={chaptersText}
		placeholder="CHAPTER01=00:00:00.000&#10;CHAPTER01NAME=Chapter 1"
		rows="15"
	></textarea>
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

	textarea {
		width: 100%;
		padding: 0.75rem;
		border: 1px solid var(--border-color);
		border-radius: 4px;
		background-color: var(--bg-primary);
		color: var(--text-primary);
		font-family: 'Courier New', monospace;
		font-size: 0.9rem;
		resize: vertical;
	}
</style>
