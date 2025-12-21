<script lang="ts">
	import { getAllLanguages, getCommonLanguages } from '$lib/utils/languages';
	import type { Language } from '$lib/utils/languages';

	interface Props {
		value: string;
		id?: string;
		label?: string;
		placeholder?: string;
	}

	let { value = $bindable(), id, label, placeholder = 'Select language...' }: Props = $props();

	// Cache languages on component creation
	const commonLanguages = getCommonLanguages();
	const allLanguages = getAllLanguages();
	const otherLanguages = allLanguages.filter(
		lang => !commonLanguages.find(common => common.code === lang.code)
	);
</script>

{#if label && id}
	<label for={id}>{label}</label>
{/if}

<select {id} bind:value>
	<option value="">{placeholder}</option>
	
	<!-- Common languages -->
	{#each commonLanguages as lang}
		<option value={lang.code}>{lang.name}</option>
	{/each}
	
	<!-- Separator -->
	<option disabled>──────────</option>
	
	<!-- All other languages -->
	{#each otherLanguages as lang}
		<option value={lang.code}>{lang.name}</option>
	{/each}
</select>

<style>
	select {
		width: 100%;
		padding: 0.5rem;
		border: 1px solid var(--border-color);
		border-radius: 4px;
		background-color: var(--bg-primary);
		color: var(--text-primary);
		cursor: pointer;
	}

	select option:disabled {
		color: var(--text-secondary);
		font-size: 0.8em;
	}

	label {
		display: block;
		margin-bottom: 0.5rem;
		font-weight: 500;
		color: var(--text-primary);
	}
</style>
