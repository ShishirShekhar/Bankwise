export default function ProductDetails() {
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
      <section className="mx-auto max-w-5xl px-6 py-12">

        {/* Back */}
        <a
          href="/compare"
          className="text-sm font-medium text-blue-600 hover:text-blue-700"
        >
          ← Back to comparison
        </a>


        {/* Product header */}
        <div className="mt-7 rounded-3xl border border-gray-200 bg-white p-8 shadow-sm">

          <div className="flex flex-col justify-between gap-8 md:flex-row">

            <div className="flex gap-5">

              <div className="flex h-16 w-16 shrink-0 items-center justify-center rounded-2xl bg-[#172554] text-2xl font-bold text-white">
                A
              </div>

              <div>
                <p className="text-sm font-medium text-blue-600">
                  Fixed Deposit
                </p>

                <h1 className="mt-1 text-3xl font-semibold">
                  Bank A
                </h1>

                <p className="mt-2 text-gray-500">
                  2-Year Fixed Deposit
                </p>
              </div>

            </div>


            <div className="md:text-right">

              <p className="text-sm text-gray-500">
                Interest rate
              </p>

              <p className="mt-1 text-4xl font-semibold text-[#172554]">
                7.10%
              </p>

              <p className="mt-1 text-sm text-green-600">
                Competitive rate for this tenure
              </p>

            </div>

          </div>


          {/* Return summary */}
          <div className="mt-8 grid gap-4 border-t border-gray-100 pt-8 sm:grid-cols-3">

            <div className="rounded-2xl bg-gray-50 p-5">
              <p className="text-sm text-gray-500">
                Investment
              </p>

              <p className="mt-1 text-xl font-semibold">
                ₹5,00,000
              </p>
            </div>

            <div className="rounded-2xl bg-gray-50 p-5">
              <p className="text-sm text-gray-500">
                Estimated interest
              </p>

              <p className="mt-1 text-xl font-semibold text-green-600">
                ₹73,550
              </p>
            </div>

            <div className="rounded-2xl bg-gray-50 p-5">
              <p className="text-sm text-gray-500">
                Estimated maturity
              </p>

              <p className="mt-1 text-xl font-semibold">
                ₹5,73,550
              </p>
            </div>

          </div>

        </div>


        {/* Conditions */}
        <div className="mt-8 grid gap-8 lg:grid-cols-2">

          <div className="rounded-3xl border border-gray-200 bg-white p-7 shadow-sm">

            <h2 className="text-xl font-semibold">
              Product conditions
            </h2>

            <div className="mt-6 divide-y divide-gray-100">

              <div className="flex justify-between gap-4 py-4">
                <span className="text-gray-500">
                  Tenure
                </span>

                <span className="font-medium">
                  2 years
                </span>
              </div>

              <div className="flex justify-between gap-4 py-4">
                <span className="text-gray-500">
                  Interest rate
                </span>

                <span className="font-medium">
                  7.10% p.a.
                </span>
              </div>

              <div className="flex justify-between gap-4 py-4">
                <span className="text-gray-500">
                  Premature withdrawal
                </span>

                <span className="font-medium">
                  Available
                </span>
              </div>

              <div className="flex justify-between gap-4 py-4">
                <span className="text-gray-500">
                  Withdrawal penalty
                </span>

                <span className="font-medium">
                  1%
                </span>
              </div>

              <div className="flex justify-between gap-4 py-4">
                <span className="text-gray-500">
                  Minimum deposit
                </span>

                <span className="font-medium">
                  ₹1,000
                </span>
              </div>

            </div>

          </div>


          {/* Verification */}
          <div className="rounded-3xl border border-gray-200 bg-white p-7 shadow-sm">

            <h2 className="text-xl font-semibold">
              Data & verification
            </h2>

            <div className="mt-6 rounded-2xl bg-green-50 p-5">

              <div className="flex items-center gap-3">

                <div className="flex h-9 w-9 items-center justify-center rounded-full bg-green-100 text-green-700">
                  ✓
                </div>

                <div>
                  <p className="font-semibold text-green-800">
                    Verified information
                  </p>

                  <p className="text-sm text-green-700">
                    Last verified recently
                  </p>
                </div>

              </div>

            </div>


            <div className="mt-6 space-y-5">

              <div>
                <p className="text-xs font-semibold uppercase tracking-wider text-gray-400">
                  Source
                </p>

                <p className="mt-1 text-sm text-gray-700">
                  Official bank product information
                </p>
              </div>

              <div>
                <p className="text-xs font-semibold uppercase tracking-wider text-gray-400">
                  Last verified
                </p>

                <p className="mt-1 text-sm text-gray-700">
                  1 October 2026
                </p>
              </div>

              <div>
                <p className="text-xs font-semibold uppercase tracking-wider text-gray-400">
                  Verification status
                </p>

                <p className="mt-1 text-sm text-gray-700">
                  Rate and key conditions checked
                </p>
              </div>

            </div>


            <button
              type="button"
              className="mt-7 w-full rounded-xl border border-gray-200 px-4 py-3 text-sm font-medium text-gray-700 hover:bg-gray-50"
            >
              View source information →
            </button>

          </div>

        </div>


        {/* AI explanation */}
        <div className="mt-8 rounded-3xl bg-[#172554] p-8 text-white">

          <div className="flex items-center gap-2">
            <span className="text-xl">
              ✦
            </span>

            <p className="text-sm font-semibold uppercase tracking-[0.15em] text-blue-200">
              BankWise AI explanation
            </p>
          </div>

          <h2 className="mt-4 text-2xl font-semibold">
            What does this product mean for you?
          </h2>

          <p className="mt-4 max-w-3xl leading-7 text-blue-100">
            This product offers a 7.10% annual interest rate for a 2-year
            tenure. Based on the illustrative investment amount of ₹5 lakh,
            the estimated maturity value is ₹5,73,550. However, because you
            mentioned that you may need the money early, the 1% premature
            withdrawal penalty is an important condition to consider.
          </p>

          <button
            type="button"
            className="mt-6 rounded-xl bg-white px-5 py-3 text-sm font-semibold text-[#172554] hover:bg-blue-50"
          >
            Ask a follow-up question
          </button>

        </div>


        {/* Disclaimer */}
        <p className="mt-8 text-center text-xs leading-5 text-gray-400">
          This prototype uses illustrative product data. Final product
          information will be sourced and verified from official sources
          before being used for financial comparisons.
        </p>

      </section>

    </main>
  );
}