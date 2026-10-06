"use client";

import { useSyncExternalStore } from "react";

const changeEvent = "bankwise:session-storage-change";

function subscribe(callback: () => void) {
  window.addEventListener("storage", callback);
  window.addEventListener(changeEvent, callback);
  return () => {
    window.removeEventListener("storage", callback);
    window.removeEventListener(changeEvent, callback);
  };
}

function getSnapshot(key: string): string | null {
  return window.sessionStorage.getItem(key);
}

function getServerSnapshot(): null {
  return null;
}

export function useSessionStorageValue(key: string): string | null {
  return useSyncExternalStore(subscribe, () => getSnapshot(key), getServerSnapshot);
}

export function setSessionStorageValue(key: string, value: string): void {
  window.sessionStorage.setItem(key, value);
  window.dispatchEvent(new Event(changeEvent));
}
