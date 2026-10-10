"use client";

import Link from "next/link";

import { LandingHero } from "@/components/landing/LandingHero";
import { BankwiseQueryForm } from "@/components/shared/BankwiseQueryForm";
import { SiteHeader } from "@/components/shared/SiteHeader";
import { TrustHighlights } from "@/components/shared/TrustHighlights";
import { useBankwiseQuery } from "@/hooks/use-bankwise-query";
import { redactSensitiveInput } from "@/lib/bankwise";

const exampleQueries = ["₹5 lakh for 2 years with early withdrawal", "₹2 lakh for 1 year"];

export function LandingPage() {
  const { runQuery, loading, error } = useBankwiseQuery();

  function submitQuery(query: string) {
    const safeQuery = redactSensitiveInput(query);
    return runQuery(safeQuery);
  }

  return (
    <main className="min-h-screen bg-[#f7f8fc] text-gray-900">
      <SiteHeader>
        <Link
          href="/login"
          className="rounded-xl border border-gray-200 px-5 py-2.5 text-sm font-semibold hover:bg-gray-50"
        >
          Sign in
        </Link>
      </SiteHeader>
      <section className="mx-auto max-w-6xl px-6 py-16 sm:py-24">
        <LandingHero />
        <BankwiseQueryForm
          onSubmit={submitQuery}
          loading={loading}
          error={error}
          examples={exampleQueries}
        />
        <TrustHighlights />
        <p className="mt-10 text-center text-xs leading-5 text-gray-500">
          BankWise provides decision support. Always review official product terms before investing.
        </p>
      </section>
    </main>
  );
}
