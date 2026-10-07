import type { Requirements } from "@/lib/requirements";
import { describeRequirements, missingFieldPrompt } from "@/lib/requirements";

export default function RequirementSummary({
  requirements,
  title = "What BankWise understood",
}: {
  requirements: Requirements;
  title?: string;
}) {
  const items = describeRequirements(requirements);
  const missing = requirements.missing ?? [];

  return (
    <section
      aria-label={title}
      className="rounded-2xl border border-gray-200 bg-white px-6 py-5 shadow-sm"
    >
      <h2 className="text-xs font-semibold tracking-wider text-blue-600 uppercase">{title}</h2>
      <dl className="mt-4 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {items.map((item) => (
          <div key={item.label}>
            <dt className="text-xs font-medium text-gray-500">{item.label}</dt>
            <dd
              className={`mt-1 font-semibold ${item.missing ? "text-amber-700" : "text-gray-900"}`}
            >
              {item.value}
            </dd>
          </div>
        ))}
      </dl>
      {missing.length > 0 && (
        <p className="mt-4 rounded-xl bg-amber-50 px-4 py-3 text-sm text-amber-900">
          To compare fixed deposits, add {missing.map(missingFieldPrompt).join(" and ")}.
        </p>
      )}
    </section>
  );
}
