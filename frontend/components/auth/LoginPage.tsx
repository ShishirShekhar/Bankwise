"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import type { FormEvent } from "react";
import { useState } from "react";

import { LoginBrandPanel } from "@/components/auth/LoginBrandPanel";
import { LoginForm } from "@/components/auth/LoginForm";
import { askBankwise, redactSensitiveInput } from "@/lib/bankwise";
import { setSessionStorageValue } from "@/lib/session-storage";

export function LoginPage() {
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function continueToBankwise(event?: FormEvent<HTMLFormElement>) {
    event?.preventDefault();
    if (loading) return;
    setLoading(true);
    setError(null);
    setSessionStorageValue("bankwise:authenticated", "true");
    const pendingQuery = window.sessionStorage.getItem("bankwise:pending-query");
    try {
      if (pendingQuery) {
        const result = await askBankwise(redactSensitiveInput(pendingQuery));
        setSessionStorageValue("bankwise:last-ask", JSON.stringify(result));
        window.sessionStorage.removeItem("bankwise:pending-query");
        router.replace("/compare");
      } else {
        const redirect = new URLSearchParams(window.location.search).get("redirect");
        router.replace(redirect === "/compare" ? "/compare" : "/dashboard");
      }
    } catch (reason) {
      setError(
        reason instanceof Error ? reason.message : "Something went wrong. Please try again.",
      );
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="min-h-screen bg-[#f7f8fc] text-gray-900">
      <div className="flex min-h-screen flex-col lg:flex-row">
        <LoginBrandPanel />
        <section className="flex w-full items-center justify-center px-6 py-12 lg:w-1/2">
          <div className="w-full max-w-md">
            <p className="text-sm font-semibold text-blue-700">
              <Link href="/">← Back to BankWise</Link>
            </p>
            <div className="mt-8 mb-8">
              <h2 className="text-3xl font-semibold tracking-tight">Welcome back</h2>
              <p className="mt-2 text-gray-500">Sign in to continue to BankWise.</p>
            </div>
            <LoginForm onSubmit={(event) => void continueToBankwise(event)} loading={loading} />
            <div className="my-5 flex items-center gap-4">
              <div className="h-px flex-1 bg-gray-200" />
              <span className="text-sm text-gray-400">or</span>
              <div className="h-px flex-1 bg-gray-200" />
            </div>
            <button
              type="button"
              onClick={() => void continueToBankwise()}
              disabled={loading}
              className="w-full rounded-xl border border-blue-200 bg-blue-50 px-4 py-3.5 font-semibold text-[#172554] transition hover:bg-blue-100 disabled:opacity-60"
            >
              {loading ? "Continuing…" : "Continue as Demo User"}
            </button>
            {error && (
              <p role="alert" className="mt-4 text-sm text-red-700">
                {error}
              </p>
            )}
            <p className="mt-8 text-center text-xs leading-5 text-gray-400">
              BankWise provides information and comparisons to help you understand financial
              products. Always review official product terms before deciding.
            </p>
          </div>
        </section>
      </div>
    </main>
  );
}
