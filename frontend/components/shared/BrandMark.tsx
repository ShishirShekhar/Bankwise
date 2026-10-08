import type { Route } from "next";
import Link from "next/link";

export function BrandMark({ href = "/", light = false }: { href?: Route; light?: boolean }) {
  return (
    <Link href={href} className="flex items-center gap-3">
      <span
        className={`flex h-10 w-10 items-center justify-center rounded-xl text-xl font-bold ${
          light ? "bg-white text-[#172554]" : "bg-[#172554] text-white"
        }`}
      >
        B
      </span>
      <span
        className={`text-xl font-semibold tracking-tight ${light ? "text-white" : "text-gray-900"}`}
      >
        BankWise
      </span>
    </Link>
  );
}
