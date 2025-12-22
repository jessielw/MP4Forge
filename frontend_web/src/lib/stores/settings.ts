import { writable } from "svelte/store";
import { browser } from "$app/environment";

const storedTheme = browser ? localStorage.getItem("theme") || "auto" : "auto";
const storedResetTabsOnAdd = browser
  ? localStorage.getItem("resetTabsOnAdd") === "true"
  : true;
const storedAudioPresets = browser
  ? JSON.parse(localStorage.getItem("audioPresetTitles") || "[]")
  : [];
const storedSubtitlePresets = browser
  ? JSON.parse(localStorage.getItem("subtitlePresetTitles") || "[]")
  : [];

export const theme = writable<string>(storedTheme);
export const resetTabsOnAdd = writable<boolean>(storedResetTabsOnAdd);
export const audioPresetTitles = writable<string[]>(storedAudioPresets);
export const subtitlePresetTitles = writable<string[]>(storedSubtitlePresets);

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

// persist audio preset titles
audioPresetTitles.subscribe((value) => {
  if (browser) {
    localStorage.setItem("audioPresetTitles", JSON.stringify(value));
  }
});

// persist subtitle preset titles
subtitlePresetTitles.subscribe((value) => {
  if (browser) {
    localStorage.setItem("subtitlePresetTitles", JSON.stringify(value));
  }
});
