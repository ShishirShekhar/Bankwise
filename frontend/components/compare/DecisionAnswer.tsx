import { SourceLink } from "@/components/compare/SourceLink";
import type { AskOption } from "@/lib/bankwise";
import { formatINR } from "@/lib/bankwise";
import { selectTradeoffOptions } from "@/lib/tradeoff-view";

export function DecisionAnswer({ options }: { options: AskOption[] }) {
  const { highestMaturity, alternative } = selectTradeoffOptions(options);
  if (!highestMaturity) return null;

  const hasLowerPenalty = alternative?.tradeoff?.gains.some((gain) =>
    gain.toLowerCase().includes("lower exit penalty"),
  );
  const maturityGap = alternative?.tradeoff?.maturity_difference_vs_highest;

  return (
    <section
      className="mt-7 overflow-hidden rounded-3xl border border-blue-200 bg-white shadow-sm"
      aria-labelledby="decision-answer-heading"
    >
      <div className="bg-[#172554] px-6 py-5 text-white sm:px-8">
        <p className="text-xs font-semibold tracking-[0.16em] text-blue-200 uppercase">
          The direct answer
        </p>
        <h2 id="decision-answer-heading" className="mt-2 text-2xl font-semibold sm:text-3xl">
          Highest calculated maturity
        </h2>
      </div>

      <div className="grid gap-0 lg:grid-cols-[1.2fr_0.8fr]">
        <div className="p-6 sm:p-8">
          <p className="text-sm font-medium text-gray-500">For your comparison</p>
          <h3 className="mt-2 text-2xl font-bold tracking-tight text-gray-950">
            {highestMaturity.bank}
          </h3>
          <p className="mt-1 text-lg text-gray-700">{highestMaturity.product_name}</p>

          <div className="mt-6 grid grid-cols-2 gap-4">
            <AnswerMetric
              label="Estimated maturity"
              value={formatINR(highestMaturity.maturity_amount)}
              prominent
            />
            <AnswerMetric label="Annual rate" value={highestMaturity.rate} />
            <AnswerMetric
              label="Estimated interest"
              value={formatINR(highestMaturity.interest_earned)}
            />
          </div>

          <div className="mt-5 flex flex-wrap items-center gap-x-4 gap-y-2 text-xs text-gray-500">
            <span>{highestMaturity.verified}</span>
            <span>
              Source: <SourceLink source={highestMaturity.source} />
            </span>
          </div>
        </div>

        {alternative && (
          <aside className="border-t border-gray-100 bg-amber-50 p-6 sm:p-8 lg:border-t-0 lg:border-l">
            <p className="text-xs font-semibold tracking-wide text-amber-800 uppercase">
              {hasLowerPenalty ? "If early withdrawal matters more" : "Next highest maturity"}
            </p>
            <h3 className="mt-2 text-xl font-bold text-gray-950">{alternative.bank}</h3>
            <p className="mt-1 text-sm text-gray-700">{alternative.product_name}</p>
            <p className="mt-4 text-lg font-semibold text-gray-900">
              {formatINR(alternative.maturity_amount)} estimated maturity
            </p>
            {hasLowerPenalty ? (
              <p className="mt-3 text-sm leading-6 text-amber-950">
                {alternative.tradeoff?.gains.find((gain) =>
                  gain.toLowerCase().includes("lower exit penalty"),
                )}
              </p>
            ) : (
              <p className="mt-3 text-sm leading-6 text-amber-950">
                {alternative.early_exit_note || alternative.penalty}
              </p>
            )}
            {maturityGap !== undefined && maturityGap > 0 && (
              <p className="mt-2 text-sm text-gray-700">
                Estimated maturity is {formatINR(maturityGap)} lower than the highest option.
              </p>
            )}
          </aside>
        )}
      </div>
    </section>
  );
}

function AnswerMetric({
  label,
  value,
  prominent = false,
}: {
  label: string;
  value: string;
  prominent?: boolean;
}) {
  return (
    <div>
      <p className="text-xs font-medium text-gray-500">{label}</p>
      <p
        className={`mt-1 font-semibold text-gray-950 ${prominent ? "text-xl sm:text-2xl" : "text-base"}`}
      >
        {value}
      </p>
    </div>
  );
}
