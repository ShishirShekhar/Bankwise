import Link from "next/link";

export function NoComparison() {
  return (
    <div className="mt-8 rounded-2xl border border-gray-200 bg-white p-8 text-center">
      <h1 className="text-2xl font-semibold">No comparison to show yet</h1>
      <p className="mt-2 text-gray-500">
        Describe what you are looking for and BankWise will request options from the API.
      </p>
      <Link
        href="/dashboard"
        className="mt-5 inline-flex rounded-xl bg-[#172554] px-5 py-3 font-medium text-white"
      >
        Start a comparison
      </Link>
    </div>
  );
}
