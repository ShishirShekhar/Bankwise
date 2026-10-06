"use client";

import { useRouter } from "next/navigation";
import type { FormEvent } from "react";
import { useRef, useState } from "react";

import RequirementSummary from "@/app/requirement-summary";
import type { AskResponse } from "@/lib/bankwise";
import { askBankwise } from "@/lib/bankwise";
import { EXAMPLE_GOALS } from "@/lib/requirements";
import { setSessionStorageValue } from "@/lib/session-storage";

export default function Dashboard() {
  const router = useRouter();
  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [clarification, setClarification] = useState<AskResponse | null>(null);
  const goalInput = useRef<HTMLTextAreaElement>(null);

  function applyExample(example: string) {
    setQuery(example);
    setError(null);
    setClarification(null);
    goalInput.current?.focus();
  }

  async function submitQuery(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!query.trim() || loading) return;
    setLoading(true);
    setError(null);
    try {
      const result = await askBankwise(query.trim());
      if (result.status === "NEEDS_CLARIFICATION" || result.status === "UNSUPPORTED") {
        // Keep the user's text so they can add what is missing.
        setClarification(result);
        return;
      }
      setClarification(null);
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

  return (
    <main className="min-h-screen bg-[#f7f8fc] text-gray-900">
      {/* Navbar */}
      <header className="border-b border-gray-200 bg-white">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-5">
          {/* Logo */}
          <div className="flex items-center gap-3">
            <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-[#172554] text-lg font-bold text-white">
              B
            </div>

            <span className="text-xl font-semibold tracking-tight">BankWise</span>
          </div>

          {/* Navigation */}
          <nav className="hidden items-center gap-8 text-sm font-medium text-gray-600 md:flex">
            <a href="/dashboard" className="text-[#172554]">
              Compare
            </a>

            <a href="#" className="transition hover:text-[#172554]">
              My Comparisons
            </a>
          </nav>

          {/* User */}
          <div className="flex h-9 w-9 items-center justify-center rounded-full bg-blue-100 text-sm font-semibold text-[#172554]">
            U
          </div>
        </div>
      </header>

      {/* Main content */}
      <section className="mx-auto max-w-5xl px-6 py-16">
        {/* Heading */}
        <div className="text-center">
          <p className="mb-3 text-sm font-semibold tracking-[0.2em] text-blue-600 uppercase">
            Your financial decision companion
          </p>

          <h1 className="text-4xl font-semibold tracking-tight sm:text-5xl">
            What are you looking for?
          </h1>

          <p className="mx-auto mt-4 max-w-2xl text-lg leading-8 text-gray-500">
            Tell BankWise what you want to achieve, and we&apos;ll help you compare financial
            products based on what actually matters to you.
          </p>
        </div>

        {/* AI prompt box */}
        <form
          onSubmit={submitQuery}
          aria-busy={loading}
          className="mx-auto mt-12 max-w-4xl rounded-3xl border border-gray-200 bg-white p-5 shadow-sm"
        >
          <label htmlFor="financial-goal" className="mb-3 block text-sm font-medium text-gray-700">
            Describe your financial goal
          </label>

          <textarea
            id="financial-goal"
            ref={goalInput}
            rows={5}
            value={query}
            readOnly={loading}
            maxLength={4000}
            onChange={(event) => setQuery(event.target.value)}
            placeholder="For example: I have ₹5 lakh and want to invest for 2 years, but I may need the money early."
            className="w-full resize-none rounded-2xl border border-gray-200 bg-gray-50 px-5 py-4 text-base text-gray-900 transition outline-none placeholder:text-gray-400 focus:border-blue-500 focus:bg-white focus:ring-4 focus:ring-blue-50"
          />

          <div className="mt-3 flex flex-wrap items-center gap-2">
            <span className="text-xs font-medium text-gray-500">Try an example:</span>
            {EXAMPLE_GOALS.map((example) => (
              <button
                key={example}
                type="button"
                disabled={loading}
                onClick={() => applyExample(example)}
                className="rounded-full border border-blue-100 bg-blue-50 px-3 py-1.5 text-left text-xs text-blue-800 transition hover:border-blue-300 disabled:opacity-60"
              >
                {example}
              </button>
            ))}
          </div>

          {error && (
            <p
              role="alert"
              className="mt-4 rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-800"
            >
              {error}
            </p>
          )}

          <div className="mt-4 flex flex-col items-start justify-between gap-4 sm:flex-row sm:items-center">
            <p className="text-sm text-gray-500" role="status">
              {loading
                ? "Understanding your goal and checking verified FD rates…"
                : "BankWise will understand your goal and preferences. Never share account numbers, PAN, Aadhaar or passwords."}
            </p>

            <button
              type="submit"
              disabled={loading || !query.trim()}
              className="w-full rounded-xl bg-[#172554] px-7 py-3.5 text-center font-medium text-white transition hover:bg-[#1e3a8a] disabled:cursor-not-allowed disabled:opacity-60 sm:w-auto"
            >
              {loading ? "Finding options…" : "Find my options →"}
            </button>
          </div>
        </form>

        {clarification && (
          <div className="mx-auto mt-6 max-w-4xl space-y-3" role="status">
            {clarification.message && (
              <p className="font-medium text-amber-900">{clarification.message}</p>
            )}
            <RequirementSummary requirements={clarification.requirements} />
          </div>
        )}

        {/* Product categories */}
        <div className="mt-14">
          <div className="text-center">
            <h2 className="text-xl font-semibold">Or explore products</h2>

            <p className="mt-2 text-sm text-gray-500">
              Start with a financial product you&apos;re interested in.
            </p>
          </div>

          <div className="mt-7 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            {/* Fixed Deposit */}
            <button
              type="button"
              className="group rounded-2xl border border-gray-200 bg-white p-6 text-left shadow-sm transition hover:-translate-y-1 hover:border-blue-200 hover:shadow-md"
            >
              <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-blue-50 text-xl">
                ₹
              </div>

              <h3 className="mt-5 font-semibold">Fixed Deposits</h3>

              <p className="mt-2 text-sm leading-6 text-gray-500">
                Compare rates, maturity amounts and withdrawal conditions.
              </p>

              <span className="mt-4 block text-sm font-medium text-blue-600">Explore →</span>
            </button>

            {/* Savings */}
            <button
              type="button"
              className="group rounded-2xl border border-gray-200 bg-white p-6 text-left shadow-sm transition hover:-translate-y-1 hover:border-blue-200 hover:shadow-md"
            >
              <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-blue-50 text-xl">
                $
              </div>

              <h3 className="mt-5 font-semibold">Savings Accounts</h3>

              <p className="mt-2 text-sm leading-6 text-gray-500">
                Compare interest rates, balances and account conditions.
              </p>

              <span className="mt-4 block text-sm font-medium text-blue-600">Explore →</span>
            </button>

            {/* Loans */}
            <button
              type="button"
              className="group rounded-2xl border border-gray-200 bg-white p-6 text-left shadow-sm transition hover:-translate-y-1 hover:border-blue-200 hover:shadow-md"
            >
              <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-blue-50 text-xl">
                ↗
              </div>

              <h3 className="mt-5 font-semibold">Loans</h3>

              <p className="mt-2 text-sm leading-6 text-gray-500">
                Understand rates, fees, repayment terms and total cost.
              </p>

              <span className="mt-4 block text-sm font-medium text-blue-600">Explore →</span>
            </button>

            {/* Credit Cards */}
            <button
              type="button"
              className="group rounded-2xl border border-gray-200 bg-white p-6 text-left shadow-sm transition hover:-translate-y-1 hover:border-blue-200 hover:shadow-md"
            >
              <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-blue-50 text-xl">
                ◇
              </div>

              <h3 className="mt-5 font-semibold">Credit Cards</h3>

              <p className="mt-2 text-sm leading-6 text-gray-500">
                Compare fees, rewards, eligibility and key conditions.
              </p>

              <span className="mt-4 block text-sm font-medium text-blue-600">Explore →</span>
            </button>
          </div>
        </div>

        {/* Why BankWise */}
        <div className="mt-16 rounded-3xl bg-[#172554] px-8 py-10 text-white">
          <h2 className="text-2xl font-semibold">Why BankWise?</h2>

          <p className="mt-2 max-w-2xl text-blue-100">
            We don&apos;t just show you a headline interest rate. We help you understand the actual
            trade-offs behind a financial product.
          </p>

          <div className="mt-8 grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
            <div>
              <div className="text-xl">✓</div>
              <h3 className="mt-3 font-medium">Compare real outcomes</h3>
              <p className="mt-1 text-sm leading-6 text-blue-200">Look beyond headline rates.</p>
            </div>

            <div>
              <div className="text-xl">✓</div>
              <h3 className="mt-3 font-medium">Understand conditions</h3>
              <p className="mt-1 text-sm leading-6 text-blue-200">
                See fees, restrictions and penalties.
              </p>
            </div>

            <div>
              <div className="text-xl">✓</div>
              <h3 className="mt-3 font-medium">Verified information</h3>
              <p className="mt-1 text-sm leading-6 text-blue-200">
                Know where product data comes from.
              </p>
            </div>

            <div>
              <div className="text-xl">✦</div>
              <h3 className="mt-3 font-medium">AI-powered explanations</h3>
              <p className="mt-1 text-sm leading-6 text-blue-200">Understand why options differ.</p>
            </div>
          </div>
        </div>
      </section>
    </main>
  );
}
