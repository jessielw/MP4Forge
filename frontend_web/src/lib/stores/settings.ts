import { writable } from "svelte/store";
import { browser } from "$app/environment";

const storedTheme = browser ? localStorage.getItem("theme") || "auto" : "auto";
const storedResetTabsOnAdd = browser
  ? localStorage.getItem("resetTabsOnAdd") === "true"
  : true;

export const theme = writable<string>(storedTheme);
export const resetTabsOnAdd = writable<boolean>(storedResetTabsOnAdd);

// persist theme changes
theme.subscribe((value) => {
  if (browser) {
    localStorage.setItem("theme", value);
  }
});

// persist resetTabsOnAdd setting
resetTabsOnAdd.subscribe((value) => {
  if (browser) {
    localStorage.setItem("resetTabsOnAdd", String(value));
  }
});

export const audioPresetTitles = writable<string[]>([]);
export const subtitlePresetTitles = writable<string[]>([]);
