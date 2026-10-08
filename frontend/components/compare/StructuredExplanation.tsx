import { ExplanationContent } from "@/components/compare/ExplanationContent";
import { parseDecisionExplanation } from "@/lib/decision-explanation";

const sectionStyles: Record<string, string> = {
  "Executive Decision Summary": "border-blue-200 bg-blue-50",
  "The Key Trade-off": "border-amber-200 bg-amber-50",
  "Conditions & Transparency": "border-gray-200 bg-white",
  Overview: "border-gray-200 bg-white",
  Explanation: "border-gray-200 bg-white",
};

const sectionDescriptions: Record<string, string> = {
  "Executive Decision Summary": "The result for your amount, duration, and liquidity preference.",
  "The Key Trade-off": "The return difference alongside the flexibility you gain or give up.",
  "Conditions & Transparency":
    "Product terms, compounding details, and source verification context.",
};

export function StructuredExplanation({ explanation }: { explanation: string }) {
  const sections = parseDecisionExplanation(explanation);

  return (
    <section className="mt-10 overflow-hidden rounded-3xl border border-gray-200 bg-white shadow-sm">
      <header className="bg-[#172554] px-6 py-5 text-white sm:px-8">
        <p className="text-xs font-semibold tracking-[0.16em] text-blue-200 uppercase">
          BankWise explanation
        </p>
        <h2 className="mt-2 text-xl font-semibold sm:text-2xl">Your decision, in context</h2>
        <p className="mt-1 text-sm text-blue-100">
          Summary, trade-off, then the conditions behind the comparison.
        </p>
      </header>

      <div className="space-y-4 p-4 sm:p-6">
        {sections.map(({ title, content }, index) => (
          <article
            key={`${title}-${index}`}
            className={`rounded-2xl border p-5 sm:p-6 ${sectionStyles[title] ?? "border-gray-200 bg-white"}`}
          >
            <div className="mb-4 flex items-start gap-3">
              <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-white/80 text-xs font-bold text-[#172554] ring-1 ring-gray-200">
                {String(index + 1).padStart(2, "0")}
              </span>
              <div>
                <h3 className="text-base font-semibold text-gray-900 sm:text-lg">{title}</h3>
                {sectionDescriptions[title] && (
                  <p className="mt-1 text-xs leading-5 text-gray-500">
                    {sectionDescriptions[title]}
                  </p>
                )}
              </div>
            </div>
            <ExplanationContent content={content} />
          </article>
        ))}
      </div>

      <footer className="border-t border-gray-100 px-6 py-4 text-xs leading-5 text-gray-500 sm:px-8">
        Check the sourced product cards above for rate details, verification dates, and
        deterministic maturity estimates.
      </footer>
    </section>
  );
}
