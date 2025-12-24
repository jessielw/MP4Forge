import { writable } from "svelte/store";
import { browser } from "$app/environment";
import { parse } from "pathe";

const STORAGE_KEY = "lastBrowsePath";

/**
 * store for tracking the last used directory in file browsers
 */
function createLastPathStore() {
  const stored = browser ? localStorage.getItem(STORAGE_KEY) : null;
  const { subscribe, set } = writable<string | null>(stored);

  return {
    subscribe,
    set: (path: string | null) => {
      if (browser && path) {
        localStorage.setItem(STORAGE_KEY, path);
      }
      set(path);
    },
    clear: () => {
      if (browser) {
        localStorage.removeItem(STORAGE_KEY);
      }
      set(null);
    },
  };
}

export const lastBrowsePath = createLastPathStore();

/**
 * get the directory path from a file path
 */
export function getDirectoryFromPath(filePath: string): string | null {
  if (!filePath) return null;
  return parse(filePath).dir;
}
