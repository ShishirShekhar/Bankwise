"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";

import { ComparisonOverview } from "@/components/compare/ComparisonOverview";
import { ComparisonWarnings } from "@/components/compare/ComparisonWarnings";
import { DecisionAnswer } from "@/components/compare/DecisionAnswer";
import { NoComparison } from "@/components/compare/NoComparison";
import { ProductResults } from "@/components/compare/ProductResults";
import { SkippedProducts } from "@/components/compare/SkippedProducts";
import { StructuredExplanation } from "@/components/compare/StructuredExplanation";
import { TradeoffBanner } from "@/components/compare/TradeoffBanner";
import { SiteHeader } from "@/components/shared/SiteHeader";
import { useLastAsk } from "@/hooks/use-last-ask";
import { setSessionStorageValue } from "@/lib/session-storage";
import { selectTradeoffOptions } from "@/lib/tradeoff-view";

export function ComparisonPage() {
  const router = useRouter();
  const result = useLastAsk();
  const { highestMaturity, alternative } = selectTradeoffOptions(result?.options ?? []);

  return (
    <main className="min-h-screen bg-[#f7f8fc] text-gray-900">
      <SiteHeader brandHref="/dashboard">
        <Link href="/dashboard" className="text-sm font-medium text-gray-600 hover:text-[#172554]">
          New comparison
        </Link>
      </SiteHeader>
      <section className="mx-auto max-w-6xl px-6 py-12">
        <Link href="/dashboard" className="text-sm font-medium text-blue-600 hover:text-blue-700">
          ← Back to search
        </Link>
        {!result ? (
          <NoComparison />
        ) : (
          <>
            <ComparisonOverview result={result} />
            <DecisionAnswer options={result.options} />
            {highestMaturity && alternative && (
              <TradeoffBanner topOption={highestMaturity} alternative={alternative} />
            )}
            {result.options.length ? (
              <ProductResults
                options={result.options}
                onSelect={(option) => {
                  setSessionStorageValue("bankwise:selected-option", JSON.stringify(option));
                  router.push("/product");
                }}
              />
            ) : result.status === "OK" ? (
              <p className="mt-8 rounded-2xl border border-gray-200 bg-white p-6 text-gray-600">
                No options were returned.
              </p>
            ) : null}
            <SkippedProducts products={result.skipped} />
            <StructuredExplanation explanation={result.explanation} />
            <ComparisonWarnings warnings={result.warnings} />
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
