const categories = [
  {
    name: "Fixed Deposits",
    icon: "₹",
    description: "Compare rates, maturity amounts and withdrawal conditions.",
    active: true,
  },
  {
    name: "Savings Accounts",
    icon: "$",
    description: "Compare interest rates, balances and account conditions.",
    active: false,
  },
  {
    name: "Loans",
    icon: "↗",
    description: "Understand rates, fees, repayment terms and total cost.",
    active: false,
  },
  {
    name: "Credit Cards",
    icon: "◇",
    description: "Compare fees, rewards, eligibility and key conditions.",
    active: false,
  },
];

export function ProductCategories() {
  return (
    <section className="mt-14">
      <div className="text-center">
        <h2 className="text-xl font-semibold">Or explore products</h2>
        <p className="mt-2 text-sm text-gray-500">
          Start with a financial product you&apos;re interested in.
        </p>
      </div>
      <div className="mt-7 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {categories.map(({ name, icon, description, active }) => (
          <button
            key={name}
            type="button"
            disabled={!active}
            onClick={() => document.getElementById("financial-goal")?.focus()}
            className={`relative rounded-2xl border border-gray-200 bg-white p-6 text-left shadow-sm ${
              active
                ? "group transition hover:-translate-y-1 hover:border-blue-200 hover:shadow-md"
                : "cursor-not-allowed opacity-75"
            }`}
          >
            {!active && (
              <span className="absolute top-5 right-5 rounded-full bg-amber-100 px-2.5 py-1 text-[10px] font-bold tracking-wide text-amber-800 uppercase">
                Coming Soon
              </span>
            )}
            <span className="flex h-11 w-11 items-center justify-center rounded-xl bg-blue-50 text-xl">
              {icon}
            </span>
            <h3 className="mt-5 font-semibold">{name}</h3>
            <p className="mt-2 text-sm leading-6 text-gray-500">{description}</p>
            <span
              className={`mt-4 block text-sm font-medium ${active ? "text-blue-600" : "text-gray-400"}`}
            >
              {active ? "Explore →" : "Coming soon"}
            </span>
          </button>
        ))}
      </div>
    </section>
  );
}
