"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";

import type { AskOption, AskResponse } from "@/lib/bankwise";
import { formatDuration, formatINR } from "@/lib/bankwise";
import { setSessionStorageValue, useSessionStorageValue } from "@/lib/session-storage";

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
      className="font-medium text-blue-700 underline decoration-blue-200 underline-offset-2 hover:text-blue-900"
    >
      {text} ↗
    </a>
  ) : (
    <span>{text}</span>
  );
}

export default function Compare() {
  const router = useRouter();
  const savedResult = useSessionStorageValue("bankwise:last-ask");
  let result: AskResponse | null = null;
  if (savedResult) {
    try {
      result = JSON.parse(savedResult) as AskResponse;
    } catch {
      result = null;
    }
  }

  const requirements = result?.requirements;
  const duration = formatDuration(requirements?.duration_months ?? null);
  const liquidity = requirements?.liquidity_need
    ? `${requirements.liquidity_need.toLowerCase()} liquidity need`
    : "Liquidity preference not specified";

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

      <section className="mx-auto max-w-6xl px-6 py-12">
        <Link href="/dashboard" className="text-sm font-medium text-blue-600 hover:text-blue-700">
          ← Back to search
        </Link>
        {!result ? (
          <div className="mt-8 rounded-2xl border border-gray-200 bg-white p-8 text-center">
            <h1 className="text-2xl font-semibold">No comparison to show yet</h1>
            <p className="mt-2 text-gray-500">
              Describe what you are looking for and BankWise will request options from the API.
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
            <div className="mt-6 flex flex-col justify-between gap-5 md:flex-row md:items-end">
              <div>
                <p className="text-sm font-semibold tracking-[0.2em] text-blue-600 uppercase">
                  Comparison results
                </p>
                <h1 className="mt-2 text-3xl font-semibold tracking-tight sm:text-4xl">
                  {requirements?.amount !== null && requirements?.amount !== undefined
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
                {requirements?.missing?.length ? (
                  <p className="mt-1 text-sm text-amber-800">
                    Please provide: {requirements.missing.join(", ")}.
                  </p>
                ) : null}
              </div>
            )}

            <div className="mt-7 rounded-2xl border border-blue-100 bg-blue-50 px-6 py-5">
              <p className="text-xs font-semibold tracking-wider text-blue-600 uppercase">
                Your requirements
              </p>
              <p className="mt-2 text-gray-800">
                {requirements?.category || "FD"} ·{" "}
                {requirements?.amount !== null && requirements?.amount !== undefined
                  ? formatINR(requirements.amount)
                  : "Amount not provided"}{" "}
                · {duration} · {liquidity}
              </p>
            </div>

            {result.options.length > 0 ? (
              <div className="mt-10">
                <div className="mb-5 flex items-center justify-between">
                  <h2 className="text-xl font-semibold">
                    {result.options.length} verified{" "}
                    {result.options.length === 1 ? "option" : "options"}
                  </h2>
                  <span className="text-sm text-gray-500">Ordered by estimated maturity</span>
                </div>
                <div className="grid gap-6 lg:grid-cols-3">
                  {result.options.map((option, index) => (
                    <article
                      key={`${option.bank}-${option.product_name}`}
                      className="flex flex-col rounded-3xl border border-gray-200 bg-white p-6 shadow-sm"
                    >
                      <div className="flex items-start justify-between gap-3">
                        <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-[#172554] text-lg font-bold text-white">
                          {option.bank.slice(0, 1).toUpperCase()}
                        </div>
                        {index === 0 && (
                          <span className="rounded-full bg-blue-50 px-3 py-1 text-xs font-medium text-blue-700">
                            {option.tag}
                          </span>
                        )}
                      </div>
                      <h3 className="mt-5 text-xl font-semibold">{option.bank}</h3>
                      <p className="mt-1 text-sm text-gray-500">{option.product_name}</p>
                      <div className="mt-6">
                        <p className="text-sm text-gray-500">Annual interest rate</p>
                        <p className="mt-1 text-3xl font-semibold text-[#172554]">{option.rate}</p>
                      </div>
                      <div className="mt-5 rounded-2xl bg-gray-50 p-4">
                        <p className="text-sm text-gray-500">Estimated maturity</p>
                        <p className="mt-1 text-xl font-semibold">{option.maturity}</p>
                        <p className="mt-1 text-sm text-green-700">
                          {option.interest} estimated interest
                        </p>
                      </div>
                      <div className="mt-5 border-b border-gray-100 pb-4">
                        <p className="text-sm text-gray-500">Early withdrawal</p>
                        <p className="mt-1 text-sm leading-6 text-gray-700">
                          {option.early_exit_note || option.penalty}
                        </p>
                        {(option.early_exit_amount === null ||
                          option.early_exit_amount === undefined) && (
                          <p className="mt-2 text-xs text-gray-500">
                            No early-exit amount is shown because no withdrawal date was provided.
                          </p>
                        )}
                      </div>
                      <div className="mt-4 text-xs text-gray-500">
                        <p>{option.verified}</p>
                        <p className="mt-1">
                          Source: <SourceLink source={option.source} />
                        </p>
                        {option.calculation_source_url && (
                          <p className="mt-1">
                            <SourceLink
                              source={{ url: option.calculation_source_url }}
                              label="Calculation method"
                            />
                          </p>
                        )}
                        {option.calculation_note && (
                          <p className="mt-2 leading-5">{option.calculation_note}</p>
                        )}
                      </div>
                      <button
                        type="button"
                        onClick={() => {
                          setSessionStorageValue(
                            "bankwise:selected-option",
                            JSON.stringify(option satisfies AskOption),
                          );
                          router.push("/product");
                        }}
                        className="mt-5 w-full rounded-xl border border-gray-200 px-4 py-3 text-sm font-medium text-gray-700 hover:bg-gray-50"
                      >
                        View details →
                      </button>
                    </article>
                  ))}
                </div>
              </div>
            ) : result.status === "OK" ? (
              <div className="mt-8 rounded-2xl border border-gray-200 bg-white p-6 text-gray-600">
                No options were returned.
              </div>
            ) : null}

            {result.skipped.length > 0 && (
              <section className="mt-9 rounded-2xl border border-amber-200 bg-white p-6">
                <h2 className="text-lg font-semibold">Products excluded from this comparison</h2>
                <p className="mt-1 text-sm text-gray-500">
                  These products were not used for calculations because their available data did not
                  meet the request.
                </p>
                <ul className="mt-4 space-y-4">
                  {result.skipped.map((item) => (
                    <li key={item.bank} className="border-t border-gray-100 pt-4 text-sm">
                      <p>
                        <span className="font-semibold">{item.bank}:</span> {item.reason}
                      </p>
                      {item.conflicts?.length ? (
                        <p className="mt-1 font-medium text-amber-800">
                          A source conflict is recorded for this product.
                        </p>
                      ) : null}
                      {item.sources?.length ? (
                        <p className="mt-2 flex flex-wrap gap-x-3 gap-y-1 text-xs text-gray-500">
                          Sources:{" "}
                          {item.sources.map((source, index) => (
                            <span key={source.id || index}>
                              <SourceLink source={source} />
                            </span>
                          ))}
                        </p>
                      ) : null}
                    </li>
                  ))}
                </ul>
              </section>
            )}

            <section className="mt-10 rounded-3xl bg-[#172554] p-8 text-white">
              <p className="text-sm font-semibold tracking-[0.15em] text-blue-200 uppercase">
                BankWise explanation
              </p>
              <p className="mt-4 max-w-4xl leading-7 text-blue-100">{result.explanation}</p>
            </section>

            {result.warnings.length > 0 && (
              <section className="mt-6 rounded-2xl border border-amber-200 bg-amber-50 p-5">
                <h2 className="font-semibold text-amber-900">Notes about this result</h2>
                <ul className="mt-2 list-inside list-disc space-y-1 text-sm text-amber-900">
                  {result.warnings.map((warning, index) => (
                    <li key={index}>{warning}</li>
                  ))}
                </ul>
              </section>
            )}

            <p className="mt-7 text-center text-xs leading-5 text-gray-500">
              Financial rates and conditions are shown with their source where available. Maturity
              values are estimates based on the API calculation method; confirm current terms with
              the provider before investing.
            </p>
          </>
        )}
      </section>
    </main>
  );
}
