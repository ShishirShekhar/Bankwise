export default function Dashboard() {
  return (
    <main className="min-h-screen bg-[#f7f8fc] text-gray-900">

      {/* Navbar */}
      <header className="border-b border-gray-200 bg-white">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-5">

          {/* Logo */}
          <div className="flex items-center gap-3">
            <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-[#172554] text-lg font-bold text-white">
              B
            </div>

            <span className="text-xl font-semibold tracking-tight">
              BankWise
            </span>
          </div>

          {/* Navigation */}
          <nav className="hidden items-center gap-8 text-sm font-medium text-gray-600 md:flex">
            <a
              href="/dashboard"
              className="text-[#172554]"
            >
              Compare
            </a>

            <a
              href="#"
              className="transition hover:text-[#172554]"
            >
              My Comparisons
            </a>
          </nav>

          {/* User */}
          <div className="flex h-9 w-9 items-center justify-center rounded-full bg-blue-100 text-sm font-semibold text-[#172554]">
            U
          </div>

        </div>
      </header>


      {/* Main content */}
      <section className="mx-auto max-w-5xl px-6 py-16">

        {/* Heading */}
        <div className="text-center">

          <p className="mb-3 text-sm font-semibold uppercase tracking-[0.2em] text-blue-600">
            Your financial decision companion
          </p>

          <h1 className="text-4xl font-semibold tracking-tight sm:text-5xl">
            What are you looking for?
          </h1>

          <p className="mx-auto mt-4 max-w-2xl text-lg leading-8 text-gray-500">
            Tell BankWise what you want to achieve, and we'll help you
            compare financial products based on what actually matters to you.
          </p>

        </div>


        {/* AI prompt box */}
        <div className="mx-auto mt-12 max-w-4xl rounded-3xl border border-gray-200 bg-white p-5 shadow-sm">

          <label
            htmlFor="financial-goal"
            className="mb-3 block text-sm font-medium text-gray-700"
          >
            Describe your financial goal
          </label>

          <textarea
            id="financial-goal"
            rows={5}
            placeholder="For example: I have ₹5 lakh and want to invest for 2 years, but I may need the money early."
            className="w-full resize-none rounded-2xl border border-gray-200 bg-gray-50 px-5 py-4 text-base text-gray-900 outline-none transition placeholder:text-gray-400 focus:border-blue-500 focus:bg-white focus:ring-4 focus:ring-blue-50"
          />

          <div className="mt-4 flex flex-col items-start justify-between gap-4 sm:flex-row sm:items-center">

            <p className="text-sm text-gray-400">
              BankWise will understand your goal and preferences.
            </p>

            <a
  href="/compare"
  className="w-full rounded-xl bg-[#172554] px-7 py-3.5 text-center font-medium text-white transition hover:bg-[#1e3a8a] sm:w-auto"
>
  Find my options →
</a>

          </div>

        </div>


        {/* Product categories */}
        <div className="mt-14">

          <div className="text-center">
            <h2 className="text-xl font-semibold">
              Or explore products
            </h2>

            <p className="mt-2 text-sm text-gray-500">
              Start with a financial product you're interested in.
            </p>
          </div>


          <div className="mt-7 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">

            {/* Fixed Deposit */}
            <button
              type="button"
              className="group rounded-2xl border border-gray-200 bg-white p-6 text-left shadow-sm transition hover:-translate-y-1 hover:border-blue-200 hover:shadow-md"
            >
              <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-blue-50 text-xl">
                ₹
              </div>

              <h3 className="mt-5 font-semibold">
                Fixed Deposits
              </h3>

              <p className="mt-2 text-sm leading-6 text-gray-500">
                Compare rates, maturity amounts and withdrawal conditions.
              </p>

              <span className="mt-4 block text-sm font-medium text-blue-600">
                Explore →
              </span>
            </button>


            {/* Savings */}
            <button
              type="button"
              className="group rounded-2xl border border-gray-200 bg-white p-6 text-left shadow-sm transition hover:-translate-y-1 hover:border-blue-200 hover:shadow-md"
            >
              <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-blue-50 text-xl">
                $
              </div>

              <h3 className="mt-5 font-semibold">
                Savings Accounts
              </h3>

              <p className="mt-2 text-sm leading-6 text-gray-500">
                Compare interest rates, balances and account conditions.
              </p>

              <span className="mt-4 block text-sm font-medium text-blue-600">
                Explore →
              </span>
            </button>


            {/* Loans */}
            <button
              type="button"
              className="group rounded-2xl border border-gray-200 bg-white p-6 text-left shadow-sm transition hover:-translate-y-1 hover:border-blue-200 hover:shadow-md"
            >
              <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-blue-50 text-xl">
                ↗
              </div>

              <h3 className="mt-5 font-semibold">
                Loans
              </h3>

              <p className="mt-2 text-sm leading-6 text-gray-500">
                Understand rates, fees, repayment terms and total cost.
              </p>

              <span className="mt-4 block text-sm font-medium text-blue-600">
                Explore →
              </span>
            </button>


            {/* Credit Cards */}
            <button
              type="button"
              className="group rounded-2xl border border-gray-200 bg-white p-6 text-left shadow-sm transition hover:-translate-y-1 hover:border-blue-200 hover:shadow-md"
            >
              <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-blue-50 text-xl">
                ◇
              </div>

              <h3 className="mt-5 font-semibold">
                Credit Cards
              </h3>

              <p className="mt-2 text-sm leading-6 text-gray-500">
                Compare fees, rewards, eligibility and key conditions.
              </p>

              <span className="mt-4 block text-sm font-medium text-blue-600">
                Explore →
              </span>
            </button>

          </div>

        </div>


        {/* Why BankWise */}
        <div className="mt-16 rounded-3xl bg-[#172554] px-8 py-10 text-white">

          <h2 className="text-2xl font-semibold">
            Why BankWise?
          </h2>

          <p className="mt-2 max-w-2xl text-blue-100">
            We don't just show you a headline interest rate. We help you
            understand the actual trade-offs behind a financial product.
          </p>


          <div className="mt-8 grid gap-6 sm:grid-cols-2 lg:grid-cols-4">

            <div>
              <div className="text-xl">✓</div>
              <h3 className="mt-3 font-medium">
                Compare real outcomes
              </h3>
              <p className="mt-1 text-sm leading-6 text-blue-200">
                Look beyond headline rates.
              </p>
            </div>

            <div>
              <div className="text-xl">✓</div>
              <h3 className="mt-3 font-medium">
                Understand conditions
              </h3>
              <p className="mt-1 text-sm leading-6 text-blue-200">
                See fees, restrictions and penalties.
              </p>
            </div>

            <div>
              <div className="text-xl">✓</div>
              <h3 className="mt-3 font-medium">
                Verified information
              </h3>
              <p className="mt-1 text-sm leading-6 text-blue-200">
                Know where product data comes from.
              </p>
            </div>

            <div>
              <div className="text-xl">✦</div>
              <h3 className="mt-3 font-medium">
                AI-powered explanations
              </h3>
              <p className="mt-1 text-sm leading-6 text-blue-200">
                Understand why options differ.
              </p>
            </div>

          </div>

        </div>

      </section>

    </main>
  );
}