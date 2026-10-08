import { SourceLink } from "@/components/compare/SourceLink";
import { TradeoffPoints } from "@/components/compare/TradeoffPoints";
import type { AskOption } from "@/lib/bankwise";
import { formatINR } from "@/lib/bankwise";

export function ProductCard({
  option,
  featured,
  onViewDetails,
}: {
  option: AskOption;
  featured: boolean;
  onViewDetails: () => void;
}) {
  return (
    <article className="flex flex-col rounded-3xl border border-gray-200 bg-white p-6 shadow-sm">
      <div className="flex items-start justify-between gap-3">
        <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-[#172554] text-lg font-bold text-white">
          {option.bank.slice(0, 1).toUpperCase()}
        </div>
        {featured && (
          <span className="rounded-full bg-blue-50 px-3 py-1 text-xs font-medium text-blue-700">
            {option.tag}
          </span>
        )}
      </div>
      <h3 className="mt-5 text-xl font-semibold">{option.bank}</h3>
      <p className="mt-1 text-sm text-gray-500">{option.product_name}</p>
      <Metric label="Annual interest rate" value={option.rate} prominent />
      <div className="mt-5 rounded-2xl bg-gray-50 p-4">
        <p className="text-sm text-gray-500">Estimated maturity</p>
        <p className="mt-1 text-xl font-semibold">{formatINR(option.maturity_amount)}</p>
        <p className="mt-1 text-sm text-green-700">
          {formatINR(option.interest_earned)} estimated interest
        </p>
      </div>
      <TradeoffPoints
        gains={option.tradeoff?.gains ?? []}
        giveUps={option.tradeoff?.give_ups ?? []}
      />
      <div className="mt-5 border-b border-gray-100 pb-4">
        <p className="text-sm text-gray-500">Early withdrawal</p>
        <p className="mt-1 text-sm leading-6 text-gray-700">
          {option.early_exit_note || option.penalty}
        </p>
        {(option.early_exit_amount === null || option.early_exit_amount === undefined) && (
          <p className="mt-2 text-xs text-gray-500">
            No early-exit amount is shown because no withdrawal date was provided.
          </p>
        )}
      </div>
      <ProductSources option={option} />
      <button
        type="button"
        onClick={onViewDetails}
        className="mt-5 w-full rounded-xl border border-gray-200 px-4 py-3 text-sm font-medium text-gray-700 hover:bg-gray-50"
      >
        View details →
      </button>
    </article>
  );
}

function Metric({
  label,
  value,
  prominent = false,
}: {
  label: string;
  value: string;
  prominent?: boolean;
}) {
  return (
    <div className="mt-6">
      <p className="text-sm text-gray-500">{label}</p>
      <p className={`mt-1 font-semibold text-[#172554] ${prominent ? "text-3xl" : "text-xl"}`}>
        {value}
      </p>
    </div>
  );
}

function ProductSources({ option }: { option: AskOption }) {
  return (
    <div className="mt-4 text-xs text-gray-500">
      <p>{option.verified}</p>
      <p className="mt-1">
        Source: <SourceLink source={option.source} />
      </p>
      {option.calculation_source_url && (
        <p className="mt-1">
          <SourceLink source={{ url: option.calculation_source_url }} label="Calculation method" />
        </p>
      )}
      {option.calculation_note && <p className="mt-2 leading-5">{option.calculation_note}</p>}
    </div>
  );
}
