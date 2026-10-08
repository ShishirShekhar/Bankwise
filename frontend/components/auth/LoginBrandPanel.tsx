import { BrandMark } from "@/components/shared/BrandMark";

export function LoginBrandPanel() {
  return (
    <section className="flex w-full flex-col justify-between bg-[#172554] px-8 py-10 text-white lg:w-1/2 lg:px-16 lg:py-14">
      <BrandMark light />
      <div className="my-16 max-w-xl lg:my-0">
        <p className="mb-4 text-sm font-medium tracking-[0.2em] text-blue-200 uppercase">
          Smarter financial decisions
        </p>
        <h1 className="text-4xl leading-tight font-semibold sm:text-5xl">
          Make your money decisions with confidence.
        </h1>
        <p className="mt-6 max-w-lg text-lg leading-8 text-blue-100">
          Compare financial products, understand the real returns, and discover the trade-offs
          before you decide.
        </p>
        <div className="mt-8 flex flex-wrap gap-3">
          <span className="rounded-full bg-white/10 px-4 py-2 text-sm">Source-grounded</span>
          <span className="rounded-full bg-white/10 px-4 py-2 text-sm">Deterministic math</span>
          <span className="rounded-full bg-white/10 px-4 py-2 text-sm">Clear trade-offs</span>
        </div>
      </div>
      <p className="text-sm text-blue-200">BankWise • Your financial decision companion</p>
    </section>
  );
}
