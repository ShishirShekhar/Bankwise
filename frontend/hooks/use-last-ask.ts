"use client";

import type { AskResponse } from "@/lib/bankwise";
import { useSessionStorageValue } from "@/lib/session-storage";

export function useLastAsk(): AskResponse | null {
  const savedResult = useSessionStorageValue("bankwise:last-ask");
  if (!savedResult) return null;
  try {
    return JSON.parse(savedResult) as AskResponse;
  } catch {
    return null;
  }
}
