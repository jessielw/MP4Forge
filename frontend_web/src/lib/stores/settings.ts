import { writable } from 'svelte/store';
import { browser } from '$app/environment';

const storedTheme = browser ? localStorage.getItem('theme') || 'auto' : 'auto';

export const theme = writable<string>(storedTheme);

// Persist theme changes
theme.subscribe((value) => {
	if (browser) {
		localStorage.setItem('theme', value);
	}
});

export const audioPresetTitles = writable<string[]>([]);
export const subtitlePresetTitles = writable<string[]>([]);
