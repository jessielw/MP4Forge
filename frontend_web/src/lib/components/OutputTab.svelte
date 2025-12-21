<script lang="ts">
	import { jobs, addJob, clearCompletedJobs } from '$lib/stores/queue';

	let outputPath = $state('');

	function handleAddToQueue() {
		if (!outputPath) return;

		addJob({
			videoFile: 'video.mp4', // TODO: Get from video tab
			audioTracks: [],
			subtitleTracks: [],
			outputFile: outputPath
		});
	}
</script>

<div class="tab-container">
	<h2>Output & Queue</h2>

	<div class="form-group">
		<label for="output-path">Output File</label>
		<div class="input-group">
			<input
				id="output-path"
				type="text"
				bind:value={outputPath}
				placeholder="output.mp4"
			/>
			<button class="browse-button">Browse</button>
		</div>
	</div>

	<div class="actions">
		<button class="primary-button" onclick={handleAddToQueue}>Add to Queue</button>
		<button class="secondary-button" onclick={clearCompletedJobs}>Clear Completed</button>
	</div>

	<div class="queue-section">
		<h3>Queue</h3>
		{#if $jobs.length === 0}
			<div class="empty-state">No jobs in queue</div>
		{:else}
			<div class="jobs-list">
				{#each $jobs as job}
					<div class="job-item" class:processing={job.status === 'processing'}>
						<div class="job-header">
							<span class="job-output">{job.outputFile}</span>
							<span class="job-status" class:failed={job.status === 'failed'}>
								{job.status}
							</span>
						</div>
						{#if job.status === 'processing'}
							<div class="progress-bar">
								<div class="progress-fill" style="width: {job.progress}%"></div>
							</div>
						{/if}
						{#if job.error}
							<div class="job-error">{job.error}</div>
						{/if}
					</div>
				{/each}
			</div>
		{/if}
	</div>
</div>

<style>
	.tab-container {
		max-width: 800px;
		margin: 0 auto;
	}

	h2,
	h3 {
		color: var(--text-primary);
		margin-bottom: 1rem;
	}

	.form-group {
		margin-bottom: 1.5rem;
	}

	label {
		display: block;
		margin-bottom: 0.5rem;
		font-weight: 500;
		color: var(--text-primary);
	}

	.input-group {
		display: flex;
		gap: 0.5rem;
	}

	input {
		flex: 1;
		padding: 0.5rem;
		border: 1px solid var(--border-color);
		border-radius: 4px;
		background-color: var(--bg-primary);
		color: var(--text-primary);
	}

	.browse-button,
	.primary-button,
	.secondary-button {
		padding: 0.5rem 1rem;
		border: none;
		border-radius: 4px;
		font-weight: 500;
		cursor: pointer;
		transition: all 0.2s;
	}

	.browse-button {
		background-color: var(--bg-secondary);
		color: var(--text-primary);
		border: 1px solid var(--border-color);
	}

	.primary-button {
		background-color: var(--accent-color);
		color: white;
	}

	.primary-button:hover {
		background-color: var(--accent-hover);
	}

	.secondary-button {
		background-color: transparent;
		color: var(--text-secondary);
		border: 1px solid var(--border-color);
	}

	.actions {
		display: flex;
		gap: 0.5rem;
		margin-bottom: 2rem;
	}

	.queue-section {
		margin-top: 2rem;
	}

	.empty-state {
		padding: 2rem;
		text-align: center;
		color: var(--text-secondary);
		border: 1px dashed var(--border-color);
		border-radius: 8px;
	}

	.jobs-list {
		display: flex;
		flex-direction: column;
		gap: 0.75rem;
	}

	.job-item {
		padding: 1rem;
		background-color: var(--bg-secondary);
		border: 1px solid var(--border-color);
		border-radius: 8px;
	}

	.job-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: 0.5rem;
	}

	.job-output {
		font-weight: 500;
		color: var(--text-primary);
	}

	.job-status {
		font-size: 0.875rem;
		padding: 0.25rem 0.5rem;
		border-radius: 4px;
		background-color: var(--accent-color);
		color: white;
	}

	.job-status.failed {
		background-color: #dc3545;
	}

	.progress-bar {
		height: 8px;
		background-color: var(--bg-primary);
		border-radius: 4px;
		overflow: hidden;
	}

	.progress-fill {
		height: 100%;
		background-color: var(--accent-color);
		transition: width 0.3s;
	}

	.job-error {
		margin-top: 0.5rem;
		font-size: 0.875rem;
		color: #dc3545;
	}
</style>
