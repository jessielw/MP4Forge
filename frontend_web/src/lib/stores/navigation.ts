import { writable } from "svelte/store";

export const currentTab = writable<string>("video");
export const outputTabSetValue = writable<string>("");
