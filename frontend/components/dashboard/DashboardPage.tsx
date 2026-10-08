"use client";

import { DashboardHeader } from "@/components/dashboard/DashboardHeader";
import { DashboardIntro } from "@/components/dashboard/DashboardIntro";
import { ProductCategories } from "@/components/dashboard/ProductCategories";
import { WhyBankwise } from "@/components/dashboard/WhyBankwise";
import { BankwiseQueryForm } from "@/components/shared/BankwiseQueryForm";
import { useBankwiseQuery } from "@/hooks/use-bankwise-query";

export function DashboardPage() {
  const { runQuery, loading, error } = useBankwiseQuery();

  return (
    <main className="min-h-screen bg-[#f7f8fc] text-gray-900">
      <DashboardHeader />
      <section className="mx-auto max-w-5xl px-6 py-16">
        <DashboardIntro />
        <BankwiseQueryForm
          onSubmit={runQuery}
          loading={loading}
          error={error}
          rows={5}
          placeholder="For example: I have ₹5 lakh and want to invest for 2 years, but may need the money early."
          helperText="BankWise will understand your goal and preferences."
          buttonLabel="Find my options →"
        />
        <ProductCategories />
        <WhyBankwise />
      </section>
    </main>
  );
}
