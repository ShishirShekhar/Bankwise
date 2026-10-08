"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

import { askBankwise, redactSensitiveInput } from "@/lib/bankwise";
import { setSessionStorageValue } from "@/lib/session-storage";

export function useBankwiseQuery() {
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function runQuery(query: string) {
    if (!query.trim() || loading) return;
    setLoading(true);
    setError(null);
    try {
      const result = await askBankwise(redactSensitiveInput(query.trim()));
      setSessionStorageValue("bankwise:last-ask", JSON.stringify(result));
      router.push("/compare");
    } catch (reason) {
      setError(
        reason instanceof Error ? reason.message : "Something went wrong. Please try again.",
      );
    } finally {
      setLoading(false);
    }
  }

  return { runQuery, loading, error };
}
