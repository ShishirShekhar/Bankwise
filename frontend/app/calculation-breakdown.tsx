import type { FDCalculation } from "@/lib/bankwise";
import { formatDuration, formatINR } from "@/lib/bankwise";

const COMPOUNDING_NAMES: Record<number, string> = {
  1: "Yearly",
  2: "Half-yearly",
  4: "Quarterly",
  12: "Monthly",
};

function compoundingLabel(timesPerYear: number): string {
  const name = COMPOUNDING_NAMES[timesPerYear];
  return name ? `${name} (${timesPerYear}× a year)` : `${timesPerYear}× a year`;
}

/**
 * Shows the inputs and result of the backend calculator. Every number comes from
 * the API response; nothing is recalculated in the browser.
 */
export default function CalculationBreakdown({
  calculation,
  unavailableReason,
}: {
  calculation: FDCalculation | null | undefined;
  unavailableReason?: string | null;
}) {
  if (!calculation) {
    return (
      <section className="rounded-3xl border border-gray-200 bg-white p-7 shadow-sm">
        <h2 className="text-xl font-semibold">How this was calculated</h2>
        <p className="mt-4 rounded-2xl bg-amber-50 px-5 py-4 text-sm text-amber-900">
          No maturity amount was calculated for this option.
          {unavailableReason ? ` ${unavailableReason}` : ""}
        </p>
      </section>
    );
  }

  const rows = [
    { label: "Principal", value: formatINR(calculation.principal) },
    { label: "Annual interest rate", value: `${calculation.annual_rate_percent}%` },
    {
      label: "Tenure",
      value: `${formatDuration(calculation.tenure_months)} (${calculation.tenure_months} months)`,
    },
    {
      label: "Compounding",
      value: compoundingLabel(calculation.compounding_frequency_per_year),
    },
  ];

  return (
    <section
      aria-labelledby="calculation-breakdown-heading"
      className="rounded-3xl border border-gray-200 bg-white p-7 shadow-sm"
    >
      <h2 id="calculation-breakdown-heading" className="text-xl font-semibold">
        How this was calculated
      </h2>

      <dl className="mt-5 grid gap-4 sm:grid-cols-2">
        {rows.map((row) => (
          <div key={row.label} className="rounded-2xl bg-gray-50 p-4">
            <dt className="text-sm text-gray-500">{row.label}</dt>
            <dd className="mt-1 font-semibold">{row.value}</dd>
          </div>
        ))}
      </dl>

      <div className="mt-5 rounded-2xl border border-blue-100 bg-blue-50 p-5">
        <p className="text-sm font-medium text-blue-900">Method: compound interest</p>
        <p className="mt-2 font-mono text-sm text-blue-900">
          Maturity = Principal × (1 + rate ÷ n)<sup>n × years</sup>
        </p>
        <p className="mt-1 font-mono text-sm break-words text-blue-800">
          = {formatINR(calculation.principal)} × (1 + {calculation.annual_rate_percent}% ÷{" "}
          {calculation.compounding_frequency_per_year})
          <sup>
            {calculation.compounding_frequency_per_year} × {calculation.tenure_months}/12
          </sup>
        </p>
        <p className="mt-2 text-xs text-blue-800">
          n is the number of times interest is compounded each year. The result is rounded to the
          nearest paisa.
        </p>
      </div>

      <dl className="mt-5 divide-y divide-gray-100">
        <div className="flex justify-between gap-4 py-3">
          <dt className="text-gray-500">Interest earned</dt>
          <dd className="font-semibold text-green-700">{formatINR(calculation.interest_earned)}</dd>
        </div>
        <div className="flex justify-between gap-4 py-3">
          <dt className="text-gray-500">Maturity amount</dt>
          <dd className="font-semibold">{formatINR(calculation.maturity_amount)}</dd>
        </div>
        <div className="flex justify-between gap-4 py-3">
          <dt className="text-gray-500">Calculation version</dt>
          <dd className="font-mono text-sm">{calculation.calculation_version}</dd>
        </div>
      </dl>

      {calculation.warnings.length > 0 && (
        <ul className="mt-4 space-y-1 text-xs leading-5 text-gray-500">
          {calculation.warnings.map((warning) => (
            <li key={warning}>⚠ {warning}</li>
          ))}
        </ul>
      )}
      <p className="mt-3 text-xs text-gray-500">
        Calculated by BankWise&apos;s deterministic calculator, not by AI.
      </p>
    </section>
  );
}
