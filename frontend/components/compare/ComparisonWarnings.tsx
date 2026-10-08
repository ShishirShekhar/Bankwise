export function ComparisonWarnings({ warnings }: { warnings: string[] }) {
  if (!warnings.length) return null;
  return (
    <section className="mt-6 rounded-2xl border border-amber-200 bg-amber-50 p-5">
      <h2 className="font-semibold text-amber-900">Notes about this result</h2>
      <ul className="mt-2 list-inside list-disc space-y-1 text-sm text-amber-900">
        {warnings.map((warning, index) => (
          <li key={`${warning}-${index}`}>{warning}</li>
        ))}
      </ul>
    </section>
  );
}
