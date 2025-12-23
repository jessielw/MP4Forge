<script lang="ts">
  import { onMount } from "svelte";
  import {
    jobs,
    addJob,
    clearCompletedJobs,
    cancelJob,
    removeJob,
    loadJobs,
    startQueueProcessing,
    stopQueueProcessing,
    getQueueStatus,
    type MuxJob,
  } from "$lib/stores/queue";
  import {
    videoTrack,
    audioTracks,
    subtitleTracks,
    chaptersText,
  } from "$lib/stores/tracks";
  import { resetTabsOnAdd } from "$lib/stores/settings";
  import { toast } from "$lib/stores/toast";
  import SaveFileBrowserModal from "./SaveFileBrowserModal.svelte";

  let outputPath = $state("");
  let showFileBrowser = $state(false);
  let cancelConfirmIds = $state<Set<string>>(new Set());
  let queueRunning = $state(false);

  // initialize WebSocket and load jobs on mount
  onMount(() => {
    loadJobs();
    checkQueueStatus();

    // poll queue status every 2 seconds
    const interval = setInterval(checkQueueStatus, 2000);
    return () => clearInterval(interval);
  });

  async function checkQueueStatus() {
    const status = await getQueueStatus();
    queueRunning = status.running;
  }

  // computed stats
  const queueStats = $derived.by(() => {
    const total = $jobs.length;
    const queued = $jobs.filter((j) => j.status === "pending").length;
    const processing = $jobs.filter((j) => j.status === "processing").length;
    const completed = $jobs.filter((j) => j.status === "completed").length;
    const failed = $jobs.filter((j) => j.status === "failed").length;

    // overall progress only considers pending + processing + completed (excludes failed)
    const progressTotal = queued + processing + completed;
    const progressPercent =
      progressTotal > 0 ? (completed / progressTotal) * 100 : 0;

    return {
      total,
      queued,
      processing,
      completed,
      failed,
      progressTotal,
      progressPercent,
    };
  });

  function handleBrowseOutput() {
    showFileBrowser = true;
  }

  function handleOutputFileSelect(filePath: string) {
    outputPath = filePath;
  }

  function getDefaultFilename(): string {
    // try to generate a smart default filename from the video file
    if ($videoTrack.filePath) {
      const videoFilename = $videoTrack.filePath.split(/[/\\]/).pop() || "";
      const nameWithoutExt = videoFilename.replace(/\.[^.]+$/, "");
      return nameWithoutExt ? `${nameWithoutExt}_muxed.mp4` : "output.mp4";
    }
    return "output.mp4";
  }

  async function handleAddToQueue() {
    if (!outputPath.trim()) {
      toast.warning("Please select an output file");
      return;
    }

    // validate video file is present
    if (!$videoTrack.filePath.trim()) {
      toast.warning("Video file is required");
      return;
    }

    try {
      // create job from current state - backend will generate ID
      await addJob({
        videoFile: $videoTrack.filePath,
        videoLanguage: $videoTrack.language,
        videoTitle: $videoTrack.title,
        videoDelay: $videoTrack.delay,
        audioTracks: $audioTracks.map((t) => ({
          filePath: t.filePath,
          language: t.language,
          title: t.title,
          delay: t.delay,
          isDefault: t.isDefault,
          trackId: t.trackId,
        })),
        subtitleTracks: $subtitleTracks.map((t) => ({
          filePath: t.filePath,
          language: t.language,
          title: t.title,
          isDefault: t.isDefault,
          isForced: t.isForced,
          trackId: t.trackId,
        })),
        chapters: $chaptersText,
        outputFile: outputPath,
      });

      // reset tabs if checkbox is enabled
      if ($resetTabsOnAdd) {
        videoTrack.set({
          filePath: "",
          language: "",
          title: "",
          delay: 0,
          mediaInfo: "",
          mediaInfoData: null,
        });
        audioTracks.set([]);
        subtitleTracks.set([]);
        chaptersText.set("");
        outputPath = "";
      }
    } catch (error) {
      toast.error(`Failed to add job: ${error}`);
    }
  }

  async function handleCancelClick(jobId: string) {
    if (cancelConfirmIds.has(jobId)) {
      // second click - actually cancel
      try {
        await cancelJob(jobId);
        cancelConfirmIds.delete(jobId);
        cancelConfirmIds = new Set(cancelConfirmIds);
      } catch (error) {
        toast.error(`Failed to cancel job: ${error}`);
      }
    } else {
      // first click - show confirmation
      cancelConfirmIds.add(jobId);
      cancelConfirmIds = new Set(cancelConfirmIds);
      // auto-revert after 3 seconds
      setTimeout(() => {
        if (cancelConfirmIds.has(jobId)) {
          cancelConfirmIds.delete(jobId);
          cancelConfirmIds = new Set(cancelConfirmIds);
        }
      }, 3000);
    }
  }

  async function handleRemoveJob(jobId: string) {
    try {
      await removeJob(jobId);
    } catch (error) {
      toast.error(`Failed to remove job: ${error}`);
    }
  }

  async function handleToggleQueue() {
    try {
      if (queueRunning) {
        await stopQueueProcessing();
        queueRunning = false;
      } else {
        // check if there are queued jobs
        const pendingJobs = $jobs.filter((j) => j.status === "pending");
        if (pendingJobs.length === 0) {
          toast.info("No pending jobs to process");
          return;
        }

        await startQueueProcessing();
        queueRunning = true;
      }
    } catch (error) {
      toast.error(
        `Failed to ${queueRunning ? "stop" : "start"} queue: ${error}`
      );
    }
  }

  function getStatusClass(status: MuxJob["status"]): string {
    switch (status) {
      case "pending":
        return "status-pending";
      case "processing":
        return "status-processing";
      case "completed":
        return "status-completed";
      case "failed":
        return "status-failed";
      default:
        return "";
    }
  }

  function getFilename(path: string): string {
    return path.split(/[/\\]/).pop() || path;
  }
</script>

<div class="tab-container">
  <div class="form-group">
    <label for="output-path">Output File</label>
    <div class="input-group">
      <input
        id="output-path"
        type="text"
        bind:value={outputPath}
        placeholder="Select output file..."
        readonly
      />
      <button class="browse-button" onclick={handleBrowseOutput}>
        📁 Browse
      </button>
    </div>
  </div>

  <div class="controls-section">
    <div class="button-row">
      <div class="vertical-flex">
        <div class="checkbox-group">
          <label>
            <input type="checkbox" bind:checked={$resetTabsOnAdd} />
            Reset Tabs on Add
          </label>
        </div>
        <button class="primary-button" onclick={handleAddToQueue}>
          Add to Queue
        </button>
      </div>
      <div class="vertical-flex">
        <button class="secondary-button" onclick={clearCompletedJobs}>
          Clear Completed
        </button>
        <button
          class="queue-button"
          class:running={queueRunning}
          onclick={handleToggleQueue}
        >
          {queueRunning ? "⏸️ Stop Queue" : "▶️ Start Queue"}
        </button>
      </div>
    </div>
  </div>

  <div class="queue-section">
    <div class="queue-header">
      <h3>Queue</h3>
    </div>

    {#if $jobs.length === 0}
      <div class="empty-state">No jobs in queue</div>
    {:else}
      <div class="queue-table">
        <table>
          <thead>
            <tr>
              <th>Status</th>
              <th>Output File</th>
              <th>Progress</th>
              <th>Details</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {#each $jobs as job}
              <tr>
                <td>
                  <span class="status-badge {getStatusClass(job.status)}">
                    {job.status.toUpperCase()}
                  </span>
                </td>
                <td class="output-cell" title={job.outputFile}>
                  {getFilename(job.outputFile)}
                </td>
                <td>{job.progress.toFixed(1)}%</td>
                <td>
                  {#if job.error}
                    <button
                      class="details-button"
                      onclick={() =>
                        toast.error(job.error || "Unknown error", 5000)}
                    >
                      View Details
                    </button>
                  {:else}
                    -
                  {/if}
                </td>
                <td>
                  {#if job.status === "pending" || job.status === "processing"}
                    <button
                      class="action-button cancel-button"
                      onclick={() => handleCancelClick(job.id)}
                    >
                      {cancelConfirmIds.has(job.id) ? "Confirm?" : "Cancel"}
                    </button>
                  {:else if job.status === "completed" || job.status === "failed"}
                    <button
                      class="action-button remove-button"
                      onclick={() => handleRemoveJob(job.id)}
                    >
                      Remove
                    </button>
                  {/if}
                </td>
              </tr>
            {/each}
          </tbody>
        </table>
      </div>
    {/if}
  </div>

  <div class="stats-bar">
    <div class="stats-text">
      Queue: {queueStats.total} jobs | {queueStats.queued} queued | {queueStats.processing}
      processing
    </div>
    <div class="progress-bar-container">
      <div class="progress-bar-label">
        Completed: {queueStats.completed}/{queueStats.progressTotal} ({queueStats.progressPercent.toFixed(
          0
        )}%)
      </div>
      <div class="progress-bar">
        <div
          class="progress-fill"
          style="width: {queueStats.progressPercent}%"
        ></div>
      </div>
    </div>
  </div>
</div>

<SaveFileBrowserModal
  bind:isOpen={showFileBrowser}
  onClose={() => (showFileBrowser = false)}
  onFileSelect={handleOutputFileSelect}
  defaultExtension=".mp4"
  title="Select Output File"
  defaultFilename={getDefaultFilename()}
/>

<style>
  .tab-container {
    max-width: 1200px;
    margin: 0 auto;
    padding: 1rem;
  }

  h3 {
    color: var(--text-primary);
    margin: 0 0 1rem 0;
    font-size: 1.1rem;
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

  input[type="text"] {
    flex: 1;
    padding: 0.5rem;
    border: 1px solid var(--border-color);
    border-radius: 4px;
    background-color: var(--bg-primary);
    color: var(--text-primary);
  }

  input[type="checkbox"] {
    margin-right: 0.5rem;
  }

  .browse-button,
  .primary-button,
  .secondary-button,
  .action-button,
  .details-button {
    padding: 0.5rem 1rem;
    border: none;
    border-radius: 4px;
    font-weight: 500;
    cursor: pointer;
    transition: all 0.2s;
    white-space: nowrap;
  }

  .browse-button {
    background-color: var(--bg-secondary);
    color: var(--text-primary);
    border: 1px solid var(--border-color);
  }

  .browse-button:hover {
    background-color: var(--bg-hover);
  }

  .primary-button {
    background-color: #4caf50;
    color: white;
  }

  .primary-button:hover {
    background-color: #45a049;
  }

  .secondary-button {
    background-color: transparent;
    color: var(--text-secondary);
    border: 1px solid var(--border-color);
  }

  .secondary-button:hover {
    background-color: var(--bg-hover);
    color: var(--text-primary);
  }

  .queue-button {
    padding: 0.5rem 1rem;
    border: none;
    border-radius: 4px;
    font-weight: 500;
    cursor: pointer;
    transition: all 0.2s;
    background-color: #2196f3;
    color: white;
  }

  .queue-button:hover {
    background-color: #1976d2;
  }

  .queue-button.running {
    background-color: #ff9800;
  }

  .queue-button.running:hover {
    background-color: #f57c00;
  }

  .controls-section {
    border-top: 1px solid var(--border-color);
    border-bottom: 1px solid var(--border-color);
    padding: 1rem 0;
    margin-bottom: 1.5rem;
  }

  .checkbox-group label {
    display: flex;
    align-items: center;
    cursor: pointer;
    font-weight: normal;
  }

  .button-row {
    display: flex;
    justify-content: space-between;
  }

  .queue-section {
    margin-bottom: 1.5rem;
  }

  .queue-header {
    margin-bottom: 0.5rem;
  }

  .empty-state {
    padding: 3rem;
    text-align: center;
    color: var(--text-secondary);
    border: 2px dashed var(--border-color);
    border-radius: 8px;
    background-color: var(--bg-secondary);
  }

  .queue-table {
    border: 1px solid var(--border-color);
    border-radius: 4px;
    overflow-x: auto;
  }

  table {
    width: 100%;
    border-collapse: collapse;
  }

  thead {
    background: var(--bg-secondary);
  }

  th {
    text-align: left;
    padding: 0.75rem;
    font-weight: 600;
    color: var(--text-primary);
    border-bottom: 2px solid var(--border-color);
  }

  td {
    padding: 0.75rem;
    color: var(--text-primary);
    border-bottom: 1px solid var(--border-color);
  }

  tbody tr:last-child td {
    border-bottom: none;
  }

  tbody tr:nth-child(even) {
    background: var(--bg-secondary);
  }

  tbody tr:hover {
    background: var(--bg-hover);
  }

  .output-cell {
    max-width: 300px;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .status-badge {
    display: inline-block;
    padding: 0.25rem 0.75rem;
    border-radius: 4px;
    font-size: 0.875rem;
    font-weight: 600;
    text-transform: uppercase;
  }

  .status-pending {
    background-color: #fff3cd;
    color: #856404;
  }

  .status-processing {
    background-color: #90ee90;
    color: #155724;
  }

  .status-completed {
    background-color: #add8e6;
    color: #004085;
  }

  .status-failed {
    background-color: #ff6347;
    color: white;
  }

  .action-button {
    padding: 0.25rem 0.75rem;
    font-size: 0.875rem;
  }

  .cancel-button {
    background-color: #ffc107;
    color: #000;
  }

  .cancel-button:hover {
    background-color: #e0a800;
  }

  .remove-button {
    background-color: #dc3545;
    color: white;
  }

  .remove-button:hover {
    background-color: #c82333;
  }

  .details-button {
    padding: 0.25rem 0.75rem;
    font-size: 0.875rem;
    background-color: #17a2b8;
    color: white;
  }

  .details-button:hover {
    background-color: #138496;
  }

  .stats-bar {
    display: flex;
    align-items: center;
    gap: 1rem;
    padding: 1rem;
    background-color: var(--bg-secondary);
    border: 1px solid var(--border-color);
    border-radius: 4px;
  }

  .stats-text {
    color: var(--text-primary);
    font-size: 0.9rem;
    white-space: nowrap;
  }

  .progress-bar-container {
    flex: 1;
    display: flex;
    align-items: center;
    gap: 0.5rem;
  }

  .progress-bar-label {
    color: var(--text-secondary);
    font-size: 0.875rem;
    white-space: nowrap;
  }

  .progress-bar {
    flex: 1;
    height: 20px;
    background-color: var(--bg-primary);
    border: 1px solid var(--border-color);
    border-radius: 4px;
    overflow: hidden;
  }

  .progress-fill {
    height: 100%;
    background-color: #4caf50;
    transition: width 0.3s ease;
  }

  .vertical-flex {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
  }
</style>
