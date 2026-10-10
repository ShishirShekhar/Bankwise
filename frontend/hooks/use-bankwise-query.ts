"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

import { useAuth } from "@/components/auth/AuthProvider";
import { ApiError } from "@/lib/api-client";
import { askBankwise, redactSensitiveInput } from "@/lib/bankwise";
import { setSessionStorageValue } from "@/lib/session-storage";

export function useBankwiseQuery() {
  const router = useRouter();
  const { authenticated, loading: authLoading, refreshUser } = useAuth();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function runQuery(query: string) {
    if (!query.trim() || loading) return;
    setLoading(true);
    setError(null);
    try {
      const safeQuery = redactSensitiveInput(query.trim());
      const hasSession = authLoading ? await refreshUser() : authenticated;
      if (!hasSession) {
        setSessionStorageValue("bankwise:pending-query", safeQuery);
        router.push("/login?redirect=/compare");
        return;
      }
      const result = await askBankwise(safeQuery);
      setSessionStorageValue("bankwise:last-ask", JSON.stringify(result));
      router.push("/compare");
    } catch (reason) {
      if (reason instanceof ApiError && reason.status === 401) {
        setSessionStorageValue("bankwise:pending-query", redactSensitiveInput(query.trim()));
        router.push("/login?redirect=/compare");
        return;
      }
      setError(
        reason instanceof Error ? reason.message : "Something went wrong. Please try again.",
      );
    } finally {
      setLoading(false);
    }
  }

  return { runQuery, loading, error };
}
