const benefits = [
  { title: "Compare real outcomes", description: "Look beyond headline rates.", icon: "✓" },
  {
    title: "Understand conditions",
    description: "See fees, restrictions and penalties.",
    icon: "✓",
  },
  { title: "Verified information", description: "Know where product data comes from.", icon: "✓" },
  { title: "AI-powered explanations", description: "Understand why options differ.", icon: "✦" },
];

export function WhyBankwise() {
  return (
    <section className="mt-16 rounded-3xl bg-[#172554] px-8 py-10 text-white">
      <h2 className="text-2xl font-semibold">Why BankWise?</h2>
      <p className="mt-2 max-w-2xl text-blue-100">
        We don&apos;t just show you a headline interest rate. We help you understand the actual
        trade-offs behind a financial product.
      </p>
      <div className="mt-8 grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
        {benefits.map(({ title, description, icon }) => (
          <article key={title}>
            <span className="text-xl" aria-hidden="true">
              {icon}
            </span>
            <h3 className="mt-3 font-medium">{title}</h3>
            <p className="mt-1 text-sm leading-6 text-blue-200">{description}</p>
          </article>
        ))}
      </div>
    </section>
  );
}
