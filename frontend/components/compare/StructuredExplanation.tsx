const sectionLabels = [
  "Executive Decision Summary",
  "The Key Trade-off",
  "Conditions & Transparency",
  "Critical Conditions & Transparency",
];

export function StructuredExplanation({ explanation }: { explanation: string }) {
  const sectionPattern = new RegExp(
    `^\\s*(?:\\*\\*)?(?:[1-3]\\.?\\s*)?(${sectionLabels.join("|")})(?:[^:\\n]*)(?:\\*\\*)?:\\s*([\\s\\S]*?)(?=^\\s*(?:\\*\\*)?(?:[1-3]\\.?\\s*)?(?:${sectionLabels.join("|")})[^:\\n]*(?:\\*\\*)?:|$)`,
    "gim",
  );
  const sections = Array.from(explanation.matchAll(sectionPattern), (match) => ({
    title: (match[1] ?? "").replace(/\s*\([^)]*\)$/, ""),
    content: (match[2] ?? "").trim(),
  }));

  return (
    <section className="mt-10 rounded-3xl bg-[#172554] p-8 text-white">
      <p className="text-sm font-semibold tracking-[0.15em] text-blue-200 uppercase">
        BankWise explanation
      </p>
      {sections.length === 3 ? (
        <div className="mt-5 grid gap-4 md:grid-cols-3">
          {sections.map(({ title, content }) => (
            <article key={title} className="rounded-2xl bg-white/10 p-5">
              <h2 className="font-semibold">{title}</h2>
              <p className="mt-3 text-sm leading-6 whitespace-pre-line text-blue-100">{content}</p>
            </article>
          ))}
        </div>
      ) : (
        <p className="mt-4 max-w-4xl leading-7 whitespace-pre-line text-blue-100">{explanation}</p>
      )}
    </section>
  );
}
