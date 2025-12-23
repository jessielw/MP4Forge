import { writable } from "svelte/store";
import { browser } from "$app/environment";
import { ApiClient } from "$lib/api";

// load from localStorage as immediate defaults (before backend fetch)
const storedTheme = browser ? localStorage.getItem("theme") || "auto" : "auto";
const storedLogLevel = browser
  ? localStorage.getItem("logLevel")
    ? parseInt(localStorage.getItem("logLevel") || "20", 10)
    : 20
  : 20;
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
export const logLevel = writable<number>(storedLogLevel);
export const resetTabsOnAdd = writable<boolean>(storedResetTabsOnAdd);
export const audioPresetTitles = writable<string[]>(storedAudioPresets);
export const subtitlePresetTitles = writable<string[]>(storedSubtitlePresets);

// flag to track if we're loading from backend (prevent save loop)
let isLoadingFromBackend = false;

// load settings from backend on startup (only update if different from localStorage to prevent flash)
if (browser) {
  ApiClient.getSettings()
    .then((settings) => {
      isLoadingFromBackend = true;

      // only update theme if different from localStorage
      const backendTheme = settings.theme?.toLowerCase() || "auto";
      if (backendTheme !== storedTheme) {
        theme.set(backendTheme);
      }

      // parse log level string (e.g., "LogLevel.INFO" or "INFO") to number
      let logLevelValue = 20; // default to INFO
      if (settings.log_level) {
        const levelStr =
          settings.log_level.split(".").pop() || settings.log_level;
        const levelMap: Record<string, number> = {
          DEBUG: 10,
          INFO: 20,
          WARNING: 30,
          ERROR: 40,
          CRITICAL: 50,
        };
        logLevelValue = levelMap[levelStr.toUpperCase()] || 20;
      }

      // only update if different
      if (logLevelValue !== storedLogLevel) {
        logLevel.set(logLevelValue);
      }

      // compare arrays and only update if different
      const backendAudioPresets = settings.audio_preset_titles || [];
      const backendSubtitlePresets = settings.subtitle_preset_titles || [];

      if (
        JSON.stringify(backendAudioPresets) !==
        JSON.stringify(storedAudioPresets)
      ) {
        audioPresetTitles.set(backendAudioPresets);
      }

      if (
        JSON.stringify(backendSubtitlePresets) !==
        JSON.stringify(storedSubtitlePresets)
      ) {
        subtitlePresetTitles.set(backendSubtitlePresets);
      }

      isLoadingFromBackend = false;
    })
    .catch((err) => {
      console.warn(
        "Failed to load settings from backend, using localStorage:",
        err
      );
      isLoadingFromBackend = false;
    });
}

// persist theme changes (localStorage cache only, backend save on explicit action)
theme.subscribe((value) => {
  if (browser) {
    localStorage.setItem("theme", value);
  }
});

// persist log level changes (localStorage cache only, backend save on explicit action)
logLevel.subscribe((value) => {
  if (browser && value !== undefined) {
    localStorage.setItem("logLevel", String(value));
  }
});

// persist resetTabsOnAdd setting (localStorage only)
resetTabsOnAdd.subscribe((value) => {
  if (browser) {
    localStorage.setItem("resetTabsOnAdd", String(value));
  }
});

// persist audio preset titles (localStorage cache only, backend save on explicit action)
audioPresetTitles.subscribe((value) => {
  if (browser) {
    localStorage.setItem("audioPresetTitles", JSON.stringify(value));
  }
});

// persist subtitle preset titles (localStorage cache only, backend save on explicit action)
subtitlePresetTitles.subscribe((value) => {
  if (browser) {
    localStorage.setItem("subtitlePresetTitles", JSON.stringify(value));
  }
});

// helper function to save all settings to backend
export async function saveSettingsToBackend() {
  if (!browser) return;

  const currentTheme = await new Promise<string>((resolve) => {
    const unsubscribe = theme.subscribe((value) => {
      resolve(value);
      unsubscribe();
    });
  });

  const currentLogLevel = await new Promise<number>((resolve) => {
    const unsubscribe = logLevel.subscribe((value) => {
      resolve(value || 20);
      unsubscribe();
    });
  });

  const currentAudioPresets = await new Promise<string[]>((resolve) => {
    const unsubscribe = audioPresetTitles.subscribe((value) => {
      resolve(value);
      unsubscribe();
    });
  });

  const currentSubtitlePresets = await new Promise<string[]>((resolve) => {
    const unsubscribe = subtitlePresetTitles.subscribe((value) => {
      resolve(value);
      unsubscribe();
    });
  });

  // map log level number to string
  const levelMap: Record<number, string> = {
    10: "DEBUG",
    20: "INFO",
    30: "WARNING",
    40: "ERROR",
    50: "CRITICAL",
  };

  await ApiClient.saveSettings({
    theme: currentTheme.charAt(0).toUpperCase() + currentTheme.slice(1),
    log_level: levelMap[currentLogLevel] || "INFO",
    audio_preset_titles: currentAudioPresets,
    subtitle_preset_titles: currentSubtitlePresets,
  });
}
