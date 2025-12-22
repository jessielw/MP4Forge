<script lang="ts">
  interface Props {
    titles: string[];
    onTitlesChange: (titles: string[]) => void;
  }

  let { titles, onTitlesChange }: Props = $props();

  let newTitle = $state("");
  let editingIndex = $state<number | null>(null);
  let editingValue = $state("");

  function addTitle() {
    const trimmed = newTitle.trim();
    if (!trimmed) return;

    // check for duplicates
    if (titles.includes(trimmed)) {
      alert(`Title "${trimmed}" already exists.`);
      return;
    }

    onTitlesChange([...titles, trimmed]);
    newTitle = "";
  }

  function startEdit(index: number) {
    editingIndex = index;
    editingValue = titles[index];
  }

  function saveEdit() {
    if (editingIndex === null) return;

    const trimmed = editingValue.trim();
    if (!trimmed) {
      cancelEdit();
      return;
    }

    // check for duplicates (excluding current)
    if (titles.some((t, i) => i !== editingIndex && t === trimmed)) {
      alert(`Title "${trimmed}" already exists.`);
      return;
    }

    const newTitles = [...titles];
    newTitles[editingIndex] = trimmed;
    onTitlesChange(newTitles);
    editingIndex = null;
  }

  function cancelEdit() {
    editingIndex = null;
    editingValue = "";
  }

  function removeTitle(index: number) {
    onTitlesChange(titles.filter((_, i) => i !== index));
  }

  function moveUp(index: number) {
    if (index === 0) return;
    const newTitles = [...titles];
    [newTitles[index - 1], newTitles[index]] = [
      newTitles[index],
      newTitles[index - 1],
    ];
    onTitlesChange(newTitles);
  }

  function moveDown(index: number) {
    if (index === titles.length - 1) return;
    const newTitles = [...titles];
    [newTitles[index], newTitles[index + 1]] = [
      newTitles[index + 1],
      newTitles[index],
    ];
    onTitlesChange(newTitles);
  }

  function clearAll() {
    if (titles.length === 0) return;

    if (confirm("Are you sure you want to remove all preset titles?")) {
      onTitlesChange([]);
    }
  }

  function handleKeydown(e: KeyboardEvent) {
    if (e.key === "Enter") {
      addTitle();
    }
  }

  function handleEditKeydown(e: KeyboardEvent) {
    if (e.key === "Enter") {
      saveEdit();
    } else if (e.key === "Escape") {
      cancelEdit();
    }
  }
</script>

<div class="preset-editor">
  <div class="add-section">
    <input
      type="text"
      bind:value={newTitle}
      onkeydown={handleKeydown}
      placeholder="Enter new preset title..."
    />
    <button class="add-button" onclick={addTitle}>Add</button>
  </div>

  <div class="list-container">
    {#if titles.length === 0}
      <div class="empty-message">No preset titles yet. Add one above!</div>
    {:else}
      <ul class="title-list">
        {#each titles as title, index (index)}
          <li class="title-item">
            {#if editingIndex === index}
              <input
                type="text"
                bind:value={editingValue}
                onkeydown={handleEditKeydown}
                class="edit-input"
              />
              <button class="icon-button save" onclick={saveEdit} title="Save"
                >✓</button
              >
              <button
                class="icon-button cancel"
                onclick={cancelEdit}
                title="Cancel">✕</button
              >
            {:else}
              <span
                class="title-text"
                ondblclick={() => startEdit(index)}
                role="button"
                tabindex="0">{title}</span
              >
              <div class="button-group">
                <button
                  class="icon-button"
                  onclick={() => startEdit(index)}
                  title="Edit">✏️</button
                >
                <button
                  class="icon-button"
                  onclick={() => moveUp(index)}
                  disabled={index === 0}
                  title="Move up">↑</button
                >
                <button
                  class="icon-button"
                  onclick={() => moveDown(index)}
                  disabled={index === titles.length - 1}
                  title="Move down">↓</button
                >
                <button
                  class="icon-button remove"
                  onclick={() => removeTitle(index)}
                  title="Remove">🗑️</button
                >
              </div>
            {/if}
          </li>
        {/each}
      </ul>
    {/if}
  </div>

  {#if titles.length > 0}
    <div class="actions">
      <button class="clear-button" onclick={clearAll}>Clear All</button>
    </div>
  {/if}
</div>

<style>
  .preset-editor {
    display: flex;
    flex-direction: column;
    gap: 1rem;
    border: 1px solid var(--border-color);
    border-radius: 4px;
    padding: 1rem;
    background-color: var(--bg-secondary);
    min-height: 250px;
  }

  .add-section {
    display: flex;
    gap: 0.5rem;
  }

  .add-section input {
    flex: 1;
    padding: 0.5rem;
    border: 1px solid var(--border-color);
    border-radius: 4px;
    background-color: var(--bg-primary);
    color: var(--text-primary);
  }

  .add-button {
    padding: 0.5rem 1.5rem;
    background-color: #4caf50;
    color: white;
    border: none;
    border-radius: 4px;
    cursor: pointer;
    font-weight: 500;
    transition: background-color 0.2s;
  }

  .add-button:hover {
    background-color: #45a049;
  }

  .list-container {
    flex: 1;
    overflow-y: auto;
    min-height: 150px;
  }

  .empty-message {
    text-align: center;
    color: var(--text-secondary);
    padding: 2rem;
    font-style: italic;
  }

  .title-list {
    list-style: none;
    padding: 0;
    margin: 0;
  }

  .title-item {
    display: flex;
    align-items: center;
    padding: 0.5rem;
    background-color: var(--bg-primary);
    border: 1px solid var(--border-color);
    border-radius: 4px;
    margin-bottom: 0.5rem;
    gap: 0.5rem;
  }

  .title-text {
    flex: 1;
    color: var(--text-primary);
    cursor: default;
  }

  .edit-input {
    flex: 1;
    padding: 0.25rem 0.5rem;
    border: 1px solid var(--border-color);
    border-radius: 4px;
    background-color: var(--bg-secondary);
    color: var(--text-primary);
  }

  .button-group {
    display: flex;
    gap: 0.25rem;
  }

  .icon-button {
    padding: 0.25rem 0.5rem;
    background-color: transparent;
    border: 1px solid var(--border-color);
    border-radius: 4px;
    cursor: pointer;
    font-size: 0.875rem;
    transition: all 0.2s;
  }

  .icon-button:hover:not(:disabled) {
    background-color: var(--bg-hover);
  }

  .icon-button:disabled {
    opacity: 0.3;
    cursor: not-allowed;
  }

  .icon-button.save {
    background-color: #4caf50;
    color: white;
    border-color: #4caf50;
  }

  .icon-button.save:hover {
    background-color: #45a049;
  }

  .icon-button.cancel {
    background-color: #f44336;
    color: white;
    border-color: #f44336;
  }

  .icon-button.cancel:hover {
    background-color: #da190b;
  }

  .icon-button.remove {
    border-color: #f44336;
  }

  .icon-button.remove:hover {
    background-color: #f44336;
    color: white;
  }

  .actions {
    display: flex;
    justify-content: flex-end;
  }

  .clear-button {
    padding: 0.5rem 1rem;
    background-color: transparent;
    color: var(--text-secondary);
    border: 1px solid var(--border-color);
    border-radius: 4px;
    cursor: pointer;
    transition: all 0.2s;
  }

  .clear-button:hover {
    background-color: #f44336;
    color: white;
    border-color: #f44336;
  }
</style>
