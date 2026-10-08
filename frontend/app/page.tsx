"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import type { FormEvent } from "react";
import { useState } from "react";

import { askBankwise, redactSensitiveInput } from "@/lib/bankwise";
import { setSessionStorageValue } from "@/lib/session-storage";

const examples = ["₹5 lakh for 2 years with early withdrawal", "₹2 lakh for 1 year"];

export default function Home() {
  const router = useRouter();
  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function submitQuery(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const prompt = redactSensitiveInput(query.trim());
    if (!prompt || loading) return;
    setError(null);
    if (window.sessionStorage.getItem("bankwise:authenticated") !== "true") {
      setSessionStorageValue("bankwise:pending-query", prompt);
      router.push("/login?redirect=/compare");
      return;
    }
    setLoading(true);
    try {
      const result = await askBankwise(prompt);
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
      <header className="border-b border-gray-200 bg-white">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-5">
          <Link href="/" className="flex items-center gap-3">
            <span className="flex h-10 w-10 items-center justify-center rounded-xl bg-[#172554] text-xl font-bold text-white">
              B
            </span>
            <span className="text-xl font-semibold tracking-tight">BankWise</span>
          </Link>
          <Link
            href="/login"
            className="rounded-xl border border-gray-200 px-5 py-2.5 text-sm font-semibold hover:bg-gray-50"
          >
            Sign in
          </Link>
        </div>
      </header>

      <section className="mx-auto max-w-6xl px-6 py-16 sm:py-24">
        <div className="mx-auto max-w-3xl text-center">
          <p className="text-sm font-semibold tracking-[0.2em] text-blue-700 uppercase">
            Clear choices, grounded in facts
          </p>
          <h1 className="mt-5 text-4xl leading-tight font-semibold tracking-tight sm:text-6xl">
            Make your money decisions with confidence.
          </h1>
          <p className="mx-auto mt-6 max-w-2xl text-lg leading-8 text-gray-600">
            Compare fixed deposits by the returns you can expect and the flexibility you may need.
          </p>
        </div>

        <form
          onSubmit={submitQuery}
          className="mx-auto mt-10 max-w-3xl rounded-3xl border border-gray-200 bg-white p-5 shadow-xl shadow-blue-950/5 sm:p-7"
        >
          <label
            htmlFor="financial-goal"
            className="mb-3 block text-sm font-semibold text-gray-800"
          >
            What are you planning for?
          </label>
          <textarea
            id="financial-goal"
            rows={3}
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            placeholder="For example: ₹5 lakh for 2 years, with the option to withdraw early"
            className="w-full resize-none rounded-2xl border border-gray-200 bg-gray-50 px-5 py-4 text-base outline-none placeholder:text-gray-400 focus:border-blue-500 focus:bg-white focus:ring-4 focus:ring-blue-50"
          />
          <div className="mt-3 flex flex-wrap gap-2">
            {examples.map((example) => (
              <button
                key={example}
                type="button"
                onClick={() => setQuery(example)}
                className="rounded-full border border-gray-200 px-3 py-1.5 text-xs text-gray-600 hover:border-blue-300 hover:text-blue-800"
              >
                {example}
              </button>
            ))}
          </div>
          <div className="mt-5 flex flex-col items-start justify-between gap-4 sm:flex-row sm:items-center">
            <p role="status" className="text-sm text-gray-500">
              {error || "Your query stays in this session while we prepare your comparison."}
            </p>
            <button
              type="submit"
              disabled={loading || !query.trim()}
              className="w-full rounded-xl bg-[#172554] px-7 py-3.5 font-semibold text-white transition hover:bg-[#1e3a8a] disabled:cursor-not-allowed disabled:opacity-60 sm:w-auto"
            >
              {loading ? "Finding options…" : "Compare FD options →"}
            </button>
          </div>
        </form>

        <div className="mt-16 grid gap-5 md:grid-cols-3">
          {[
            ["Source-grounded", "See where rates and product conditions come from."],
            ["Deterministic math", "Maturity estimates use a transparent, consistent calculation."],
            ["Trade-off matrix", "Understand what each option gains and gives up."],
          ].map(([title, description]) => (
            <article key={title} className="rounded-2xl border border-gray-200 bg-white p-6">
              <span className="text-lg text-blue-700">✓</span>
              <h2 className="mt-3 font-semibold">{title}</h2>
              <p className="mt-2 text-sm leading-6 text-gray-600">{description}</p>
            </article>
          ))}
        </div>
        <p className="mt-10 text-center text-xs leading-5 text-gray-500">
          BankWise provides decision support. Always review official product terms before investing.
        </p>
      </section>
    </main>
  );
}
