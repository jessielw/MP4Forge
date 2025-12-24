<script lang="ts">
  interface Track {
    type: "Video" | "Audio" | "Subtitle" | "Chapters";
    id: string;
    format: string;
    language?: string;
    flags?: string;
    title?: string;
    selected: boolean;
    data: any; // full track data from MediaInfo
  }

  let {
    isOpen = $bindable(false),
    filename,
    tracks = [],
    onConfirm,
  }: {
    isOpen: boolean;
    filename: string;
    tracks: Track[];
    onConfirm: (selectedTracks: Track[]) => void;
  } = $props();

  function handleConfirm() {
    const selected = tracks.filter((t) => t.selected);
    onConfirm(selected);
    isOpen = false;
  }

  function handleCancel() {
    isOpen = false;
  }

  function handleBackdropClick(e: MouseEvent) {
    if (e.target === e.currentTarget) {
      handleCancel();
    }
  }
</script>

{#if isOpen}
  <div class="modal-backdrop" onclick={handleBackdropClick} role="presentation">
    <div class="modal-dialog">
      <div class="modal-header">
        <div class="modal-title">
          <span class="icon">📁</span>
          Import Tracks
        </div>
      </div>

      <div class="modal-body">
        <p class="filename-info">
          Select which tracks to import from <strong>{filename}</strong>:
        </p>

        <div class="table-container">
          <table>
            <thead>
              <tr>
                <th>Import</th>
                <th>Type</th>
                <th>ID</th>
                <th>Format</th>
                <th>Language</th>
                <th>Flags</th>
                <th>Title</th>
              </tr>
            </thead>
            <tbody>
              {#each tracks as track}
                <tr>
                  <td class="checkbox-cell">
                    <input
                      type="checkbox"
                      bind:checked={track.selected}
                      disabled={track.type === "Video"}
                    />
                  </td>
                  <td>{track.type}</td>
                  <td>{track.id}</td>
                  <td>{track.format}</td>
                  <td>{track.language || ""}</td>
                  <td>{track.flags || ""}</td>
                  <td>{track.title || ""}</td>
                </tr>
              {/each}
            </tbody>
          </table>
        </div>
      </div>

      <div class="modal-footer">
        <button class="btn btn-cancel" onclick={handleCancel}>Cancel</button>
        <button class="btn btn-primary" onclick={handleConfirm}>OK</button>
      </div>
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
    background: rgba(0, 0, 0, 0.5);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 1000;
  }

  .modal-dialog {
    background: var(--bg-primary);
    border-radius: 8px;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
    width: 90%;
    max-width: 900px;
    max-height: 80vh;
    display: flex;
    flex-direction: column;
  }

  .modal-header {
    padding: 1rem 1.5rem;
    border-bottom: 1px solid var(--border-color);
  }

  .modal-title {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    font-size: 1.25rem;
    font-weight: 600;
    color: var(--text-primary);
  }

  .icon {
    font-size: 1.5rem;
  }

  .modal-body {
    padding: 1.5rem;
    overflow-y: auto;
    flex: 1;
  }

  .filename-info {
    margin-bottom: 1rem;
    color: var(--text-secondary);
  }

  .filename-info strong {
    color: var(--text-primary);
    word-break: break-all;
  }

  .table-container {
    border: 1px solid var(--border-color);
    border-radius: 4px;
    overflow: auto;
    max-height: 400px;
  }

  table {
    width: 100%;
    border-collapse: collapse;
  }

  thead {
    background: var(--bg-secondary);
    position: sticky;
    top: 0;
    z-index: 1;
  }

  th {
    text-align: left;
    padding: 0.75rem;
    font-weight: 600;
    color: var(--text-primary);
    border-bottom: 2px solid var(--border-color);
    white-space: nowrap;
  }

  td {
    padding: 0.75rem;
    color: var(--text-primary);
    border-bottom: 1px solid var(--border-color);
  }

  tbody tr:last-child td {
    border-bottom: none;
  }

  tbody tr:hover {
    background: var(--bg-hover);
  }

  .checkbox-cell {
    text-align: center;
    width: 60px;
  }

  .checkbox-cell input[type="checkbox"] {
    cursor: pointer;
    width: 18px;
    height: 18px;
  }

  .modal-footer {
    padding: 1rem 1.5rem;
    border-top: 1px solid var(--border-color);
    display: flex;
    justify-content: flex-end;
    gap: 0.75rem;
  }

  .btn {
    padding: 0.5rem 1.5rem;
    border: none;
    border-radius: 4px;
    font-weight: 500;
    cursor: pointer;
    transition: all 0.2s;
  }

  .btn-cancel {
    background: var(--bg-secondary);
    color: var(--text-primary);
  }

  .btn-cancel:hover {
    background: var(--bg-hover);
  }

  .btn-primary {
    background: #0066cc;
    color: white;
  }

  .btn-primary:hover {
    background: #0052a3;
  }
</style>
