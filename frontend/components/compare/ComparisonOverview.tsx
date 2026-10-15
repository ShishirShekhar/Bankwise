import Link from "next/link";

import type { AskResponse } from "@/lib/bankwise";
import { formatDuration, formatINR } from "@/lib/bankwise";

export function ComparisonOverview({ result }: { result: AskResponse }) {
  const requirements = result.requirements;
  const duration = formatDuration(requirements.duration_months);
  const liquidity = requirements.liquidity_need
    ? `${requirements.liquidity_need.toLowerCase()} liquidity need`
    : "Liquidity preference not specified";

  return (
    <>
      <div className="mt-6 flex flex-col justify-between gap-5 md:flex-row md:items-end">
        <div>
          <p className="text-sm font-semibold tracking-[0.2em] text-blue-600 uppercase">
            Comparison results
          </p>
          <h1 className="mt-2 text-3xl font-semibold tracking-tight sm:text-4xl">
            {requirements.amount !== null && requirements.amount !== undefined
              ? `Options for ${formatINR(requirements.amount)}`
              : "Your FD options"}
          </h1>
          <p className="mt-3 text-gray-500">
            {duration} · {liquidity}
          </p>
        </div>
        <Link
          href="/dashboard"
          className="rounded-xl border border-gray-200 bg-white px-5 py-3 text-center text-sm font-medium text-gray-700 shadow-sm hover:bg-gray-50"
        >
          Modify search
        </Link>
      </div>
      {result.message && result.status !== "OK" && (
        <div
          className="mt-7 rounded-2xl border border-amber-200 bg-amber-50 px-6 py-5"
          role="status"
        >
          <p className="font-semibold text-amber-900">{result.message}</p>
          {requirements.missing.length > 0 && (
            <p className="mt-1 text-sm text-amber-800">
              Please provide: {requirements.missing.join(", ")}.
            </p>
          )}
        </div>
      )}
      <div className="mt-7 rounded-2xl border border-blue-100 bg-blue-50 px-6 py-5">
        <p className="text-xs font-semibold tracking-wider text-blue-600 uppercase">
          Your requirements
        </p>
        <p className="mt-2 text-gray-800">
          {requirements.category || "FD"} ·{" "}
          {requirements.amount !== null && requirements.amount !== undefined
            ? formatINR(requirements.amount)
            : "Amount not provided"}{" "}
          · {duration} · {liquidity}
        </p>
      </div>
      {result.best_if_withdrawn_early && (
        <section
          className="mt-5 rounded-2xl border border-amber-200 bg-amber-50 px-6 py-5"
          aria-labelledby="early-withdrawal-heading"
          role="status"
        >
          <h2 id="early-withdrawal-heading" className="font-semibold text-amber-950">
            Early-withdrawal comparison
          </h2>
          {result.best_if_withdrawn_early.status === "RANKED" ? (
            <>
              <p className="mt-2 text-sm text-amber-950">
                {result.best_if_withdrawn_early.bank} has the lowest verified premature-withdrawal
                penalty among the compared products: {result.best_if_withdrawn_early.penalty_pp.toFixed(2)}
                percentage points.
              </p>
              <p className="mt-1 text-sm text-amber-900">
                {result.best_if_withdrawn_early.payout_note} Terms: {" "}
                <a
                  className="font-medium underline underline-offset-2"
                  href={result.best_if_withdrawn_early.source_url}
                  target="_blank"
                  rel="noreferrer"
                >
                  view verified source
                </a>
              </p>
            </>
          ) : result.best_if_withdrawn_early.status === "TIE" ? (
            <p className="mt-2 text-sm text-amber-950">
              {result.best_if_withdrawn_early.banks.join(", ")} tie for the lowest verified
              premature-withdrawal penalty at {result.best_if_withdrawn_early.penalty_pp.toFixed(2)}
              percentage points.
            </p>
          ) : (
            <>
              <p className="mt-2 text-sm text-amber-950">
                {result.best_if_withdrawn_early.reason}
              </p>
              {result.best_if_withdrawn_early.unranked_banks.length > 0 && (
                <p className="mt-1 text-sm text-amber-900">
                  Terms needing verification: {result.best_if_withdrawn_early.unranked_banks.join(", ")}.
                </p>
              )}
            </>
          )}
        </section>
      )}
    </>
  );
}
