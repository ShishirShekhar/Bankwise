"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import type { FormEvent } from "react";
import { useState } from "react";

import { askBankwise, redactSensitiveInput } from "@/lib/bankwise";
import { setSessionStorageValue } from "@/lib/session-storage";

export default function Login() {
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
        const requestedRedirect = new URLSearchParams(window.location.search).get("redirect");
        router.replace(requestedRedirect === "/compare" ? "/compare" : "/dashboard");
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
        <section className="flex w-full flex-col justify-between bg-[#172554] px-8 py-10 text-white lg:w-1/2 lg:px-16 lg:py-14">
          <Link href="/" className="flex items-center gap-3">
            <span className="flex h-10 w-10 items-center justify-center rounded-xl bg-white text-xl font-bold text-[#172554]">
              B
            </span>
            <span className="text-2xl font-semibold tracking-tight">BankWise</span>
          </Link>
          <div className="my-16 max-w-xl lg:my-0">
            <p className="mb-4 text-sm font-medium tracking-[0.2em] text-blue-200 uppercase">
              Smarter financial decisions
            </p>
            <h1 className="text-4xl leading-tight font-semibold sm:text-5xl">
              Make your money decisions with confidence.
            </h1>
            <p className="mt-6 max-w-lg text-lg leading-8 text-blue-100">
              Compare financial products, understand the real returns, and discover the trade-offs
              before you decide.
            </p>
            <div className="mt-8 flex flex-wrap gap-3">
              <span className="rounded-full bg-white/10 px-4 py-2 text-sm">Source-grounded</span>
              <span className="rounded-full bg-white/10 px-4 py-2 text-sm">Deterministic math</span>
              <span className="rounded-full bg-white/10 px-4 py-2 text-sm">Clear trade-offs</span>
            </div>
          </div>
          <p className="text-sm text-blue-200">BankWise • Your financial decision companion</p>
        </section>

        <section className="flex w-full items-center justify-center px-6 py-12 lg:w-1/2">
          <div className="w-full max-w-md">
            <p className="text-sm font-semibold text-blue-700">
              <Link href="/">← Back to BankWise</Link>
            </p>
            <div className="mt-8 mb-8">
              <h2 className="text-3xl font-semibold tracking-tight">Welcome back</h2>
              <p className="mt-2 text-gray-500">Sign in to continue to BankWise.</p>
            </div>
            <form onSubmit={continueToBankwise} className="space-y-5">
              <div>
                <label htmlFor="email" className="mb-2 block text-sm font-medium text-gray-700">
                  Email address
                </label>
                <input
                  id="email"
                  type="email"
                  autoComplete="email"
                  placeholder="you@example.com"
                  required
                  className="w-full rounded-xl border border-gray-200 bg-white px-4 py-3.5 outline-none focus:border-blue-600 focus:ring-2 focus:ring-blue-100"
                />
              </div>
              <div>
                <label htmlFor="password" className="mb-2 block text-sm font-medium text-gray-700">
                  Password
                </label>
                <input
                  id="password"
                  type="password"
                  autoComplete="current-password"
                  placeholder="Enter your password"
                  required
                  className="w-full rounded-xl border border-gray-200 bg-white px-4 py-3.5 outline-none focus:border-blue-600 focus:ring-2 focus:ring-blue-100"
                />
              </div>
              <button
                type="submit"
                disabled={loading}
                className="w-full rounded-xl bg-[#172554] px-4 py-3.5 font-medium text-white transition hover:bg-[#1e3a8a] disabled:opacity-60"
              >
                {loading ? "Continuing…" : "Sign in"}
              </button>
            </form>
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
