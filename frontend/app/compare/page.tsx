const products = [
  {
    bank: "Bank A",
    rate: "7.10%",
    maturity: "₹5,73,550",
    interest: "₹73,550",
    flexibility: "Medium",
    penalty: "1% premature withdrawal penalty",
    verified: "Verified 2 days ago",
    tag: "Balanced option",
  },
  {
    bank: "Bank B",
    rate: "6.85%",
    maturity: "₹5,70,450",
    interest: "₹70,450",
    flexibility: "High",
    penalty: "Lower premature withdrawal impact",
    verified: "Verified 3 days ago",
    tag: "More flexible",
  },
  {
    bank: "Bank C",
    rate: "7.40%",
    maturity: "₹5,76,900",
    interest: "₹76,900",
    flexibility: "Low",
    penalty: "Higher restrictions on early withdrawal",
    verified: "Verified 1 day ago",
    tag: "Highest return",
  },
];

export default function Compare() {
  return (
    <main className="min-h-screen bg-[#f7f8fc] text-gray-900">

      {/* Navbar */}
      <header className="border-b border-gray-200 bg-white">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-5">

          <div className="flex items-center gap-3">
            <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-[#172554] text-lg font-bold text-white">
              B
            </div>

            <span className="text-xl font-semibold">
              BankWise
            </span>
          </div>

          <nav className="hidden items-center gap-8 text-sm font-medium text-gray-600 md:flex">
            <a
              href="/Dashboard"
              className="hover:text-[#172554]"
            >
              Compare
            </a>

            <a
              href="#"
              className="hover:text-[#172554]"
            >
              My Comparisons
            </a>
          </nav>

          <div className="flex h-9 w-9 items-center justify-center rounded-full bg-blue-100 text-sm font-semibold text-[#172554]">
            U
          </div>

        </div>
      </header>


      {/* Main */}
      <section className="mx-auto max-w-6xl px-6 py-12">

        {/* Page heading */}
        <div>

          <a
            href="/Dashboard"
            className="text-sm font-medium text-blue-600 hover:text-blue-700"
          >
            ← Back to search
          </a>

          <div className="mt-6 flex flex-col justify-between gap-6 md:flex-row md:items-end">

            <div>
              <p className="text-sm font-semibold uppercase tracking-[0.2em] text-blue-600">
                Comparison results
              </p>

              <h1 className="mt-2 text-3xl font-semibold tracking-tight sm:text-4xl">
                Options for your ₹5 lakh investment
              </h1>

              <p className="mt-3 max-w-2xl text-gray-500">
                2-year investment period • Early withdrawal may be required
              </p>
            </div>

            <button
              type="button"
              className="rounded-xl border border-gray-200 bg-white px-5 py-3 text-sm font-medium text-gray-700 shadow-sm hover:bg-gray-50"
            >
              Modify search
            </button>

          </div>
        </div>


        {/* User requirement */}
        <div className="mt-8 rounded-2xl border border-blue-100 bg-blue-50 px-6 py-5">

          <p className="text-xs font-semibold uppercase tracking-wider text-blue-600">
            Your requirement
          </p>

          <p className="mt-2 text-gray-800">
            “I have ₹5 lakh and want to invest for 2 years, but I may need
            the money early.”
          </p>

        </div>


        {/* Results */}
        <div className="mt-10">

          <div className="mb-5 flex items-center justify-between">
            <h2 className="text-xl font-semibold">
              3 products found
            </h2>

            <button
              type="button"
              className="text-sm font-medium text-blue-600"
            >
              Sort by: Recommended
            </button>
          </div>


          <div className="grid gap-6 lg:grid-cols-3">

            {products.map((product) => (
              <div
                key={product.bank}
                className="relative flex flex-col rounded-3xl border border-gray-200 bg-white p-6 shadow-sm transition hover:-translate-y-1 hover:shadow-md"
              >

                {/* Tag */}
                <div className="absolute right-5 top-5 rounded-full bg-blue-50 px-3 py-1 text-xs font-medium text-blue-700">
                  {product.tag}
                </div>


                {/* Bank */}
                <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-[#172554] text-lg font-bold text-white">
                  {product.bank.charAt(product.bank.length - 1)}
                </div>

                <h3 className="mt-5 text-xl font-semibold">
                  {product.bank}
                </h3>

                <p className="mt-1 text-sm text-gray-500">
                  2-Year Fixed Deposit
                </p>


                {/* Rate */}
                <div className="mt-7">
                  <p className="text-sm text-gray-500">
                    Interest rate
                  </p>

                  <p className="mt-1 text-3xl font-semibold text-[#172554]">
                    {product.rate}
                  </p>
                </div>


                {/* Maturity */}
                <div className="mt-6 rounded-2xl bg-gray-50 p-4">

                  <p className="text-sm text-gray-500">
                    Estimated maturity
                  </p>

                  <p className="mt-1 text-xl font-semibold">
                    {product.maturity}
                  </p>

                  <p className="mt-1 text-sm text-green-600">
                    +{product.interest} interest
                  </p>

                </div>


                {/* Flexibility */}
                <div className="mt-5 flex items-center justify-between border-b border-gray-100 pb-4">

                  <span className="text-sm text-gray-500">
                    Flexibility
                  </span>

                  <span className="text-sm font-semibold">
                    {product.flexibility}
                  </span>

                </div>


                {/* Penalty */}
                <div className="mt-4">

                  <p className="text-sm text-gray-500">
                    Early withdrawal
                  </p>

                  <p className="mt-1 text-sm leading-6 text-gray-700">
                    {product.penalty}
                  </p>

                </div>


                {/* Verification */}
                <div className="mt-5 flex items-center gap-2 text-xs text-gray-400">
                  <span className="text-green-600">✓</span>
                  {product.verified}
                </div>


                {/* Button */}
                
                <a
  href="/product"
  className="mt-6 block w-full rounded-xl bg-[#172554] px-4 py-3 text-center font-medium text-white transition hover:bg-[#1e3a8a]"
>
  View details →
</a>

              </div>
            ))}

          </div>

        </div>


        {/* AI explanation */}
        <div className="mt-12 rounded-3xl bg-[#172554] p-8 text-white">

          <div className="flex flex-col gap-6 md:flex-row md:items-start md:justify-between">

            <div className="max-w-3xl">

              <div className="flex items-center gap-2">
                <span className="text-xl">✦</span>

                <p className="text-sm font-semibold uppercase tracking-[0.15em] text-blue-200">
                  BankWise insight
                </p>
              </div>

              <h2 className="mt-3 text-2xl font-semibold">
                The highest rate isn't necessarily the best fit for your goal.
              </h2>

              <p className="mt-4 leading-7 text-blue-100">
                Bank C offers the highest estimated maturity amount, but it
                also has stricter early-withdrawal conditions. Since you
                mentioned that you may need the money early, flexibility is
                an important factor alongside the interest rate.
              </p>

            </div>

            <button
              type="button"
              className="whitespace-nowrap rounded-xl bg-white px-5 py-3 text-sm font-semibold text-[#172554] hover:bg-blue-50"
            >
              Ask BankWise →
            </button>

          </div>

        </div>


        {/* Data note */}
        <div className="mt-8 text-center">

          <p className="text-xs leading-5 text-gray-400">
            Rates and product conditions shown here are illustrative demo
            data for the prototype. Final implementation will use verified
            product information with source and last-verified timestamps.
          </p>

        </div>

      </section>

    </main>
  );
}