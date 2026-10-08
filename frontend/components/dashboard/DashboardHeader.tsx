import Link from "next/link";

import { SiteHeader } from "@/components/shared/SiteHeader";

export function DashboardHeader() {
  return (
    <SiteHeader>
      <nav
        className="hidden items-center gap-8 text-sm font-medium text-gray-600 md:flex"
        aria-label="Main navigation"
      >
        <Link href="/dashboard" className="text-[#172554]">
          Compare
        </Link>
        <span aria-disabled="true" className="text-gray-400">
          My Comparisons
        </span>
      </nav>
      <span
        className="flex h-9 w-9 items-center justify-center rounded-full bg-blue-100 text-sm font-semibold text-[#172554]"
        aria-label="Demo user"
      >
        U
      </span>
    </SiteHeader>
  );
}
