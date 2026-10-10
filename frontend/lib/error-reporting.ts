"use client";

import { logEvent } from "firebase/analytics";

import { getFirebaseAnalytics } from "@/lib/firebase";

export type ClientErrorCategory = "runtime" | "unhandled_rejection" | "api_server" | "network";
type SafePage = "home" | "login" | "compare" | "dashboard" | "product" | "other";

function safePage(): SafePage {
  const path = window.location.pathname;
  if (path === "/") return "home";
  if (["/login", "/compare", "/dashboard", "/product"].includes(path)) {
    return path.slice(1) as Exclude<SafePage, "home" | "other">;
  }
  return "other";
}

export function reportClientError(category: ClientErrorCategory, requestId?: string): void {
  if (
    process.env.NODE_ENV !== "production" ||
    typeof window === "undefined" ||
    !process.env.NEXT_PUBLIC_FIREBASE_MEASUREMENT_ID
  ) {
    return;
  }
  try {
    // Only fixed categories and allowlisted page names are sent. Never attach
    // exception messages, stacks, URLs, request contents, or identity.
    const safeRequestId = requestId && /^[a-f0-9]{32}$/i.test(requestId) ? requestId : undefined;
    logEvent(getFirebaseAnalytics(), "bankwise_client_error", {
      error_category: category,
      page: safePage(),
      ...(safeRequestId ? { request_id: safeRequestId } : {}),
    });
  } catch {
    // Telemetry must never interfere with the user journey.
  }
}
