export default function Home() {
  return (
    <main className="min-h-screen bg-[#f7f8fc]">
      <div className="flex min-h-screen flex-col lg:flex-row">

        {/* Left side - BankWise branding */}
        <section className="flex w-full flex-col justify-between bg-[#172554] px-8 py-10 text-white lg:w-1/2 lg:px-16 lg:py-14">

          {/* Logo */}
          <div>
            <div className="flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-white text-xl font-bold text-[#172554]">
                B
              </div>

              <span className="text-2xl font-semibold tracking-tight">
                BankWise
              </span>
            </div>
          </div>

          {/* Main message */}
          <div className="my-16 max-w-xl lg:my-0">
            <p className="mb-4 text-sm font-medium uppercase tracking-[0.2em] text-blue-200">
              Smarter financial decisions
            </p>

            <h1 className="text-4xl font-semibold leading-tight sm:text-5xl">
              Make your money decisions with confidence.
            </h1>

            <p className="mt-6 max-w-lg text-lg leading-8 text-blue-100">
              Compare financial products, understand the real returns,
              and discover the trade-offs before you decide.
            </p>

            <div className="mt-8 flex flex-wrap gap-3">
              <span className="rounded-full bg-white/10 px-4 py-2 text-sm">
                Compare products
              </span>

              <span className="rounded-full bg-white/10 px-4 py-2 text-sm">
                Understand returns
              </span>

              <span className="rounded-full bg-white/10 px-4 py-2 text-sm">
                AI-powered insights
              </span>
            </div>
          </div>

          {/* Footer */}
          <p className="text-sm text-blue-200">
            BankWise • Your financial decision companion
          </p>
        </section>


        {/* Right side - Login */}
        <section className="flex w-full items-center justify-center px-6 py-12 lg:w-1/2">

          <div className="w-full max-w-md">

            <div className="mb-8">
              <h2 className="text-3xl font-semibold tracking-tight text-gray-900">
                Welcome back
              </h2>

              <p className="mt-2 text-gray-500">
                Sign in to continue to BankWise.
              </p>
            </div>


            {/* Login form */}
            <div className="space-y-5">

              {/* Email */}
              <div>
                <label
                  htmlFor="email"
                  className="mb-2 block text-sm font-medium text-gray-700"
                >
                  Email address
                </label>

                <input
                  id="email"
                  type="email"
                  placeholder="you@example.com"
                  className="w-full rounded-xl border border-gray-200 bg-white px-4 py-3.5 text-gray-900 outline-none transition focus:border-blue-600 focus:ring-2 focus:ring-blue-100"
                />
              </div>


              {/* Password */}
              <div>
                <div className="mb-2 flex items-center justify-between">
                  <label
                    htmlFor="password"
                    className="block text-sm font-medium text-gray-700"
                  >
                    Password
                  </label>

                  <button
                    type="button"
                    className="text-sm font-medium text-blue-600 hover:text-blue-700"
                  >
                    Forgot password?
                  </button>
                </div>

                <input
                  id="password"
                  type="password"
                  placeholder="Enter your password"
                  className="w-full rounded-xl border border-gray-200 bg-white px-4 py-3.5 text-gray-900 outline-none transition focus:border-blue-600 focus:ring-2 focus:ring-blue-100"
                />
              </div>


              {/* Login button */}
              <button
                type="button"
                className="w-full rounded-xl bg-[#172554] px-4 py-3.5 font-medium text-white transition hover:bg-[#1e3a8a]"
              >
                Sign in
              </button>


              {/* Divider */}
              <div className="flex items-center gap-4 py-2">
                <div className="h-px flex-1 bg-gray-200" />
                <span className="text-sm text-gray-400">or</span>
                <div className="h-px flex-1 bg-gray-200" />
              </div>


              {/* Sign up */}
              <p className="text-center text-sm text-gray-500">
                Don't have an account?{" "}
                <button
                  type="button"
                  className="font-semibold text-blue-600 hover:text-blue-700"
                >
                  Create account
                </button>
              </p>

            </div>


            {/* Disclaimer */}
            <p className="mt-10 text-center text-xs leading-5 text-gray-400">
              BankWise provides information and comparisons to help you
              understand financial products. Always review the official
              product terms before making a financial decision.
            </p>

          </div>
        </section>

      </div>
    </main>
  );
}