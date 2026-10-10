"use client";

import Link from "next/link";

import { useRequireAuth } from "@/hooks/use-require-auth";
import type { AskOption, AskResponse } from "@/lib/bankwise";
import { formatDuration, formatINR } from "@/lib/bankwise";
import { useSessionStorageValue } from "@/lib/session-storage";

function SourceLink({
  source,
  label,
}: {
  source: {
    url?: string | null;
    title?: string | null;
    reference?: string | null;
    type?: string | null;
  };
  label?: string;
}) {
  const text = label || source.title || source.reference || source.type || "Source";
  return source.url ? (
    <a
      href={source.url}
      target="_blank"
      rel="noreferrer"
      className="font-medium text-blue-700 underline underline-offset-2"
    >
      {text} ↗
    </a>
  ) : (
    <span>{text}</span>
  );
}

export default function ProductDetails() {
  const checkingAuth = useRequireAuth("/product");
  const selectedOption = useSessionStorageValue("bankwise:selected-option");
  const savedResult = useSessionStorageValue("bankwise:last-ask");
  let option: AskOption | null = null;
  let result: AskResponse | null = null;
  try {
    if (selectedOption) option = JSON.parse(selectedOption) as AskOption;
    if (savedResult) result = JSON.parse(savedResult) as AskResponse;
  } catch {
    option = null;
    result = null;
  }

  const requirements = result?.requirements;

  if (checkingAuth) {
    return <main className="min-h-screen bg-[#f7f8fc]" aria-label="Checking sign-in" />;
  }

  return (
    <main className="min-h-screen bg-[#f7f8fc] text-gray-900">
      <header className="border-b border-gray-200 bg-white">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-5">
          <Link href="/dashboard" className="flex items-center gap-3">
            <span className="flex h-9 w-9 items-center justify-center rounded-lg bg-[#172554] text-lg font-bold text-white">
              B
            </span>
            <span className="text-xl font-semibold">BankWise</span>
          </Link>
          <Link
            href="/dashboard"
            className="text-sm font-medium text-gray-600 hover:text-[#172554]"
          >
            New comparison
          </Link>
        </div>
      </header>
      <section className="mx-auto max-w-5xl px-6 py-12">
        <Link href="/compare" className="text-sm font-medium text-blue-600 hover:text-blue-700">
          ← Back to comparison
        </Link>
        {!option ? (
          <div className="mt-7 rounded-3xl border border-gray-200 bg-white p-8 text-center">
            <h1 className="text-2xl font-semibold">No product selected</h1>
            <p className="mt-2 text-gray-500">
              Run a comparison and choose an option to see its details.
            </p>
            <Link
              href="/dashboard"
              className="mt-5 inline-flex rounded-xl bg-[#172554] px-5 py-3 font-medium text-white"
            >
              Start a comparison
            </Link>
          </div>
        ) : (
          <>
            <div className="mt-7 rounded-3xl border border-gray-200 bg-white p-8 shadow-sm">
              <div className="flex flex-col justify-between gap-8 md:flex-row">
                <div className="flex gap-5">
                  <div className="flex h-16 w-16 shrink-0 items-center justify-center rounded-2xl bg-[#172554] text-2xl font-bold text-white">
                    {option.bank.slice(0, 1).toUpperCase()}
                  </div>
                  <div>
                    <p className="text-sm font-medium text-blue-600">Fixed Deposit</p>
                    <h1 className="mt-1 text-3xl font-semibold">{option.bank}</h1>
                    <p className="mt-2 text-gray-500">{option.product_name}</p>
                  </div>
                </div>
                <div className="md:text-right">
                  <p className="text-sm text-gray-500">Annual interest rate</p>
                  <p className="mt-1 text-4xl font-semibold text-[#172554]">{option.rate}</p>
                  <p className="mt-1 text-sm text-gray-500">
                    Source status: {option.source.freshness || "not provided"}
                  </p>
                </div>
              </div>
              <div className="mt-8 grid gap-4 border-t border-gray-100 pt-8 sm:grid-cols-3">
                <div className="rounded-2xl bg-gray-50 p-5">
                  <p className="text-sm text-gray-500">Investment</p>
                  <p className="mt-1 text-xl font-semibold">{formatINR(requirements?.amount)}</p>
                </div>
                <div className="rounded-2xl bg-gray-50 p-5">
                  <p className="text-sm text-gray-500">Estimated interest</p>
                  <p className="mt-1 text-xl font-semibold text-green-700">{option.interest}</p>
                </div>
                <div className="rounded-2xl bg-gray-50 p-5">
                  <p className="text-sm text-gray-500">Estimated maturity</p>
                  <p className="mt-1 text-xl font-semibold">{option.maturity}</p>
                </div>
              </div>
            </div>

            <div className="mt-8 grid gap-8 lg:grid-cols-2">
              <section className="rounded-3xl border border-gray-200 bg-white p-7 shadow-sm">
                <h2 className="text-xl font-semibold">Product information</h2>
                <dl className="mt-5 divide-y divide-gray-100">
                  <div className="flex justify-between gap-4 py-4">
                    <dt className="text-gray-500">Requested tenure</dt>
                    <dd className="text-right font-medium">
                      {formatDuration(requirements?.duration_months ?? null)}
                    </dd>
                  </div>
                  <div className="flex justify-between gap-4 py-4">
                    <dt className="text-gray-500">Early withdrawal</dt>
                    <dd className="text-right font-medium">{option.flexibility}</dd>
                  </div>
                  <div className="py-4">
                    <dt className="text-gray-500">Withdrawal terms</dt>
                    <dd className="mt-1 text-sm leading-6">
                      {option.early_exit_note || option.penalty}
                    </dd>
                  </div>
                  <div className="py-4">
                    <dt className="text-gray-500">Early-exit estimate</dt>
                    <dd className="mt-1 text-sm leading-6">
                      {option.early_exit_amount === null || option.early_exit_amount === undefined
                        ? "Unavailable without a withdrawal date."
                        : formatINR(option.early_exit_amount)}
                    </dd>
                  </div>
                </dl>
              </section>

              <section className="rounded-3xl border border-gray-200 bg-white p-7 shadow-sm">
                <h2 className="text-xl font-semibold">Source and calculation</h2>
                <div className="mt-5 rounded-2xl bg-blue-50 p-5">
                  <p className="font-semibold">{option.source.title || "Product rate source"}</p>
                  <p className="mt-1 text-sm text-gray-600">
                    {option.source.reference ||
                      option.source.type ||
                      "Source reference not provided"}
                  </p>
                  <p className="mt-3 text-sm">
                    {option.source.url ? (
                      <SourceLink source={option.source} label="Open source" />
                    ) : (
                      "Source URL not provided"
                    )}
                  </p>
                </div>
                <dl className="mt-5 space-y-4 text-sm">
                  <div>
                    <dt className="text-gray-500">Verified</dt>
                    <dd className="mt-1">
                      {option.source.verified_at || "Verification date not provided"}
                    </dd>
                  </div>
                  <div>
                    <dt className="text-gray-500">Effective from</dt>
                    <dd className="mt-1">
                      {option.source.effective_from || "Effective date not provided"}
                    </dd>
                  </div>
                  <div>
                    <dt className="text-gray-500">Calculation method</dt>
                    <dd className="mt-1">
                      {option.calculation_note || "No calculation note provided."}
                    </dd>
                  </div>
                  {option.calculation_source_url && (
                    <div>
                      <SourceLink
                        source={{ url: option.calculation_source_url }}
                        label="Calculation source"
                      />
                    </div>
                  )}
                  {option.penalty_source_url && (
                    <div>
                      <SourceLink
                        source={{ url: option.penalty_source_url }}
                        label="Withdrawal terms source"
                      />
                    </div>
                  )}
                </dl>
              </section>
            </div>

            <section className="mt-8 rounded-3xl bg-[#172554] p-8 text-white">
              <p className="text-sm font-semibold tracking-[0.15em] text-blue-200 uppercase">
                BankWise explanation
              </p>
              <p className="mt-4 max-w-3xl leading-7 text-blue-100">
                {result?.explanation || "No explanation was returned for this comparison."}
              </p>
            </section>
            <p className="mt-7 text-center text-xs leading-5 text-gray-500">
              Maturity is an estimate based on the API response. Confirm the source and current
              provider terms before investing.
            </p>
          </>
        )}
      </section>
    </main>
  );
}
