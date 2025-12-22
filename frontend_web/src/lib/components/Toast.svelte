<script lang="ts">
  import { toast, type Toast } from "$lib/stores/toast";
  import { fly } from "svelte/transition";

  const toasts = $derived($toast);

  function getIcon(type: Toast["type"]): string {
    switch (type) {
      case "success":
        return "✅";
      case "error":
        return "❌";
      case "warning":
        return "⚠️";
      case "info":
        return "ℹ️";
    }
  }
</script>

<div class="toast-container">
  {#each toasts as toastItem (toastItem.id)}
    <div
      class="toast toast-{toastItem.type}"
      transition:fly={{ y: 30, duration: 300 }}
    >
      <span class="toast-icon">{getIcon(toastItem.type)}</span>
      <span class="toast-message">{toastItem.message}</span>
      <button
        class="toast-close"
        onclick={() => toast.remove(toastItem.id)}
        aria-label="Close"
      >
        ✕
      </button>
    </div>
  {/each}
</div>

<style>
  .toast-container {
    position: fixed;
    bottom: 1rem;
    right: 1rem;
    z-index: 9999;
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
    pointer-events: none;
  }

  .toast {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    padding: 1rem 1.25rem;
    border-radius: 8px;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
    min-width: 300px;
    max-width: 500px;
    pointer-events: auto;
    backdrop-filter: blur(10px);
  }

  .toast-success {
    background: rgba(76, 175, 80, 0.95);
    color: white;
    border-left: 4px solid #2e7d32;
  }

  .toast-error {
    background: rgba(244, 67, 54, 0.95);
    color: white;
    border-left: 4px solid #c62828;
  }

  .toast-warning {
    background: rgba(255, 152, 0, 0.95);
    color: white;
    border-left: 4px solid #e65100;
  }

  .toast-info {
    background: rgba(33, 150, 243, 0.95);
    color: white;
    border-left: 4px solid #1565c0;
  }

  .toast-icon {
    font-size: 1.25rem;
    font-weight: bold;
    flex-shrink: 0;
  }

  .toast-message {
    flex: 1;
    font-size: 0.9375rem;
    line-height: 1.4;
  }

  .toast-close {
    background: none;
    border: none;
    color: inherit;
    cursor: pointer;
    font-size: 1.25rem;
    padding: 0;
    width: 1.5rem;
    height: 1.5rem;
    display: flex;
    align-items: center;
    justify-content: center;
    border-radius: 4px;
    transition: background 0.2s;
    flex-shrink: 0;
    opacity: 0.8;
  }

  .toast-close:hover {
    opacity: 1;
    background: rgba(0, 0, 0, 0.1);
  }
</style>
