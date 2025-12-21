<script lang="ts">
	import { currentTab } from '$lib/stores/navigation';

	interface Tab {
		id: string;
		icon: string;
		label: string;
	}

	let { tabs }: { tabs: Tab[] } = $props();
</script>

<nav class="navigation">
	<div class="nav-buttons">
		{#each tabs as tab}
			<button
				class="nav-button"
				class:active={$currentTab === tab.id}
				onclick={() => ($currentTab = tab.id)}
			>
				<span class="icon">{tab.icon}</span>
				<span class="label">{tab.label}</span>
			</button>
		{/each}
	</div>
</nav>

<style>
	.navigation {
		width: 120px;
		background-color: var(--bg-secondary);
		border-right: 1px solid var(--border-color);
		display: flex;
		flex-direction: column;
		padding: 0.5rem 0;
	}

	.nav-buttons {
		display: flex;
		flex-direction: column;
		gap: 0.25rem;
	}

	.nav-button {
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: 0.25rem;
		padding: 0.75rem 0.5rem;
		background: transparent;
		border: none;
		color: var(--text-secondary);
		transition: all 0.2s;
		cursor: pointer;
	}

	.nav-button:hover {
		background-color: var(--bg-primary);
		color: var(--text-primary);
	}

	.nav-button.active {
		background-color: var(--accent-color);
		color: white;
	}

	.icon {
		font-size: 1.5rem;
	}

	.label {
		font-size: 0.75rem;
		font-weight: 500;
	}
</style>
