"use client";

import Link from "next/link";

import { ResearchEvidence } from "@/components/compare/ResearchEvidence";
import { SiteHeader } from "@/components/shared/SiteHeader";
import { useLastAsk } from "@/hooks/use-last-ask";
import { useRequireAuth } from "@/hooks/use-require-auth";

export function ResearchEvidencePage() {
  const checkingAuth = useRequireAuth("/compare/research");
  const result = useLastAsk();

  if (checkingAuth) {
    return <main className="min-h-screen bg-[#f7f8fc]" aria-label="Checking sign-in" />;
  }

  return (
    <main className="min-h-screen bg-[#f7f8fc] text-gray-900">
      <SiteHeader brandHref="/dashboard">
        <Link href="/compare" className="text-sm font-medium text-gray-600 hover:text-[#172554]">
          Back to comparison
        </Link>
      </SiteHeader>
      <section className="mx-auto max-w-4xl px-6 py-12">
        <Link href="/compare" className="text-sm font-medium text-blue-600 hover:text-blue-700">
          ← Back to comparison
        </Link>
        <h1 className="mt-5 text-3xl font-bold tracking-tight text-gray-950">Research evidence</h1>
        <p className="mt-2 max-w-2xl text-sm leading-6 text-gray-600">
          Review the retrieved material and citations used as research evidence for this comparison.
          These sources do not replace verified catalogue data or financial calculations.
        </p>
        {result ? (
          <ResearchEvidence research={result.research} />
        ) : (
          <p className="mt-6 rounded-2xl border border-gray-200 bg-white p-6 text-gray-600">
            There is no saved comparison to show research evidence for. Start a comparison first.
          </p>
        )}
      </section>
    </main>
  );
}
