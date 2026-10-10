"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";

import { useAuth } from "@/components/auth/AuthProvider";
import { SiteHeader } from "@/components/shared/SiteHeader";

export function DashboardHeader() {
  const router = useRouter();
  const { signOut } = useAuth();

  async function handleSignOut() {
    try {
      await signOut();
    } finally {
      router.replace("/");
    }
  }

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
      <button
        type="button"
        onClick={() => void handleSignOut()}
        className="rounded-xl border border-gray-200 px-4 py-2 text-sm font-semibold hover:bg-gray-50"
      >
        Sign out
      </button>
    </SiteHeader>
  );
}
