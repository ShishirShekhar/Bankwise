"use client";

import type { FormEvent } from "react";
import { useState } from "react";

type BankwiseQueryFormProps = {
  onSubmit: (query: string) => void | Promise<void>;
  loading?: boolean;
  error?: string | null;
  examples?: string[];
  rows?: number;
  buttonLabel?: string;
  placeholder?: string;
  helperText?: string;
};

export function BankwiseQueryForm({
  onSubmit,
  loading = false,
  error,
  examples = [],
  rows = 3,
  buttonLabel = "Compare FD options →",
  placeholder = "For example: ₹5 lakh for 2 years, with the option to withdraw early",
  helperText = "Your query stays in this session while we prepare your comparison.",
}: BankwiseQueryFormProps) {
  const [query, setQuery] = useState("");

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (query.trim() && !loading) void onSubmit(query.trim());
  }

  return (
    <form
      onSubmit={handleSubmit}
      className="mx-auto mt-10 max-w-3xl rounded-3xl border border-gray-200 bg-white p-5 shadow-xl shadow-blue-950/5 sm:p-7"
    >
      <label htmlFor="financial-goal" className="mb-3 block text-sm font-semibold text-gray-800">
        What are you planning for?
      </label>
      <textarea
        id="financial-goal"
        rows={rows}
        value={query}
        onChange={(event) => setQuery(event.target.value)}
        placeholder={placeholder}
        className="w-full resize-none rounded-2xl border border-gray-200 bg-gray-50 px-5 py-4 text-base outline-none placeholder:text-gray-400 focus:border-blue-500 focus:bg-white focus:ring-4 focus:ring-blue-50"
      />
      {examples.length > 0 && (
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
      )}
      <div className="mt-5 flex flex-col items-start justify-between gap-4 sm:flex-row sm:items-center">
        <p role={error ? "alert" : "status"} className="text-sm text-gray-500">
          {error || helperText}
        </p>
        <button
          type="submit"
          disabled={loading || !query.trim()}
          className="w-full rounded-xl bg-[#172554] px-7 py-3.5 font-semibold text-white transition hover:bg-[#1e3a8a] disabled:cursor-not-allowed disabled:opacity-60 sm:w-auto"
        >
          {loading ? "Finding options…" : buttonLabel}
        </button>
      </div>
    </form>
  );
}
