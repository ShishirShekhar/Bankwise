"use client";

import { useEffect } from "react";

import { reportClientError } from "@/lib/error-reporting";

export function ClientErrorReporter() {
  useEffect(() => {
    const onError = () => reportClientError("runtime");
    const onUnhandledRejection = () => reportClientError("unhandled_rejection");
    window.addEventListener("error", onError);
    window.addEventListener("unhandledrejection", onUnhandledRejection);
    return () => {
      window.removeEventListener("error", onError);
      window.removeEventListener("unhandledrejection", onUnhandledRejection);
    };
  }, []);

  return null;
}
