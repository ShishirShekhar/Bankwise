import { ExplanationContent } from "@/components/compare/ExplanationContent";

type AIExplanationProps = {
  ai?: {
    provider: string;
    status: string;
    explanation?: string | null;
  };
};

export function AIExplanation({ ai }: AIExplanationProps) {
  if (!ai || ai.status === "not_used") return null;

  return (
    <section
      className="mt-6 rounded-3xl border border-violet-200 bg-white shadow-sm"
      aria-labelledby="ai-explanation-heading"
    >
      <div className="border-b border-violet-100 bg-violet-50 px-6 py-5 sm:px-8">
        <p className="text-xs font-semibold tracking-[0.16em] text-violet-700 uppercase">
          {ai.provider}
        </p>
        <h2 id="ai-explanation-heading" className="mt-2 text-xl font-semibold text-gray-950">
          Gemini explanation
        </h2>
      </div>
      {ai.status === "generated" && ai.explanation ? (
        <div className="space-y-4 p-6 sm:p-8">
          <p className="text-sm text-gray-600">
            This explanation uses the verified comparison context. Calculations, source status,
            and trade-off figures above come from Bankwise&apos;s deterministic rules.
          </p>
          <ExplanationContent content={ai.explanation} />
        </div>
      ) : (
        <p className="px-6 py-5 text-sm text-gray-600 sm:px-8">
          A Gemini explanation was not available for this request. The source-checked comparison
          and deterministic explanation above are still available.
        </p>
      )}
    </section>
  );
}
