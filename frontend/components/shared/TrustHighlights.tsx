const highlights = [
  { title: "Source-grounded", description: "See where rates and product conditions come from." },
  { title: "Deterministic math", description: "Maturity estimates use a transparent calculation." },
  { title: "Trade-off matrix", description: "Understand what each option gains and gives up." },
];

export function TrustHighlights() {
  return (
    <div className="mt-16 grid gap-5 md:grid-cols-3">
      {highlights.map(({ title, description }) => (
        <article key={title} className="rounded-2xl border border-gray-200 bg-white p-6">
          <span className="text-lg text-blue-700" aria-hidden="true">
            ✓
          </span>
          <h2 className="mt-3 font-semibold">{title}</h2>
          <p className="mt-2 text-sm leading-6 text-gray-600">{description}</p>
        </article>
      ))}
    </div>
  );
}
