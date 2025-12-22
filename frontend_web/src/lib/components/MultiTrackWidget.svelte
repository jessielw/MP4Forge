<script lang="ts">
  interface Tab {
    id: string;
    label: string;
  }

  let {
    tabs = $bindable([]),
    activeTabId = $bindable(""),
    onAddTrack,
    onRemoveTrack,
    onReorderTabs,
    children,
  }: {
    tabs: Tab[];
    activeTabId: string;
    onAddTrack: () => void;
    onRemoveTrack: (id: string) => void;
    onReorderTabs?: (newOrder: Tab[]) => void;
    children: any;
  } = $props();

  let draggedTabId = $state<string | null>(null);
  let dragOverTabId = $state<string | null>(null);

  function handleAddClick() {
    onAddTrack();
  }

  function handleTabClick(tabId: string) {
    activeTabId = tabId;
  }

  function handleTabKeydown(tabId: string, event: KeyboardEvent) {
    if (event.key === "Enter" || event.key === " ") {
      event.preventDefault();
      handleTabClick(tabId);
    }
  }

  function handleRemoveClick(tabId: string, event: MouseEvent) {
    event.stopPropagation();
    onRemoveTrack(tabId);
  }

  function handleDragStart(tabId: string, event: DragEvent) {
    draggedTabId = tabId;
    if (event.dataTransfer) {
      event.dataTransfer.effectAllowed = "move";
      event.dataTransfer.setData("text/plain", tabId);
    }
  }

  function handleDragOver(tabId: string, event: DragEvent) {
    event.preventDefault();
    if (event.dataTransfer) {
      event.dataTransfer.dropEffect = "move";
    }
    dragOverTabId = tabId;
  }

  function handleDragLeave() {
    dragOverTabId = null;
  }

  function handleDrop(targetTabId: string, event: DragEvent) {
    event.preventDefault();

    if (!draggedTabId || draggedTabId === targetTabId || !onReorderTabs) {
      draggedTabId = null;
      dragOverTabId = null;
      return;
    }

    const draggedIndex = tabs.findIndex((t) => t.id === draggedTabId);
    const targetIndex = tabs.findIndex((t) => t.id === targetTabId);

    if (draggedIndex === -1 || targetIndex === -1) {
      draggedTabId = null;
      dragOverTabId = null;
      return;
    }

    const newTabs = [...tabs];
    const [removed] = newTabs.splice(draggedIndex, 1);
    newTabs.splice(targetIndex, 0, removed);

    onReorderTabs(newTabs);

    draggedTabId = null;
    dragOverTabId = null;
  }

  function handleDragEnd() {
    draggedTabId = null;
    dragOverTabId = null;
  }
</script>

<div class="multi-track-widget">
  <div class="tab-bar">
    <div class="tabs">
      {#each tabs as tab}
        <div
          class="tab"
          class:active={tab.id === activeTabId}
          class:dragging={draggedTabId === tab.id}
          class:drag-over={dragOverTabId === tab.id}
          draggable="true"
          ondragstart={(e) => handleDragStart(tab.id, e)}
          ondragover={(e) => handleDragOver(tab.id, e)}
          ondragleave={handleDragLeave}
          ondrop={(e) => handleDrop(tab.id, e)}
          ondragend={handleDragEnd}
          onclick={() => handleTabClick(tab.id)}
          onkeydown={(e) => handleTabKeydown(tab.id, e)}
          role="button"
          tabindex="0"
        >
          <span class="tab-label">{tab.label}</span>
          <button
            class="close-btn"
            onclick={(e) => handleRemoveClick(tab.id, e)}
            aria-label="Remove track"
          >
            ×
          </button>
        </div>
      {/each}
    </div>
    <button class="add-tab-btn" onclick={handleAddClick} aria-label="Add track">
      +
    </button>
  </div>

  <div class="tab-content">
    {@render children()}
  </div>
</div>

<style>
  .multi-track-widget {
    border: 1px solid var(--border-color);
    border-radius: 4px;
    overflow: hidden;
  }

  .tab-bar {
    display: flex;
    background: var(--bg-secondary);
    border-bottom: 1px solid var(--border-color);
  }

  .tabs {
    display: flex;
    flex: 1;
    overflow-x: auto;
  }

  .tab {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.75rem 1rem;
    background: var(--bg-secondary);
    border-right: 1px solid var(--border-color);
    cursor: move;
    transition:
      background 0.2s,
      opacity 0.2s;
    white-space: nowrap;
  }

  .tab:hover {
    background: var(--bg-hover);
  }

  .tab.active {
    background: var(--bg-primary);
    border-bottom: 2px solid var(--accent-color);
  }

  .tab.dragging {
    opacity: 0.4;
  }

  .tab.drag-over {
    border-left: 3px solid var(--accent-color);
  }

  .tab-label {
    color: var(--text-primary);
    font-weight: 500;
  }

  .close-btn {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 20px;
    height: 20px;
    border: none;
    background: transparent;
    color: var(--text-secondary);
    font-size: 1.5rem;
    line-height: 1;
    cursor: pointer;
    border-radius: 2px;
    transition: all 0.2s;
  }

  .close-btn:hover {
    background: rgba(255, 0, 0, 0.1);
    color: #ff4444;
  }

  .add-tab-btn {
    padding: 0.75rem 1.25rem;
    background: var(--bg-secondary);
    border: none;
    border-left: 1px solid var(--border-color);
    color: var(--text-primary);
    font-size: 1.25rem;
    font-weight: bold;
    cursor: pointer;
    transition: background 0.2s;
  }

  .add-tab-btn:hover {
    background: var(--bg-hover);
  }

  .tab-content {
    padding: 1.5rem;
    background: var(--bg-primary);
  }
</style>
