"use client";

import { useRouter } from "next/navigation";
import { useEffect } from "react";

import { useAuth } from "@/components/auth/AuthProvider";

export function useRequireAuth(redirectPath: string): boolean {
  const router = useRouter();
  const { authenticated, loading } = useAuth();

  useEffect(() => {
    if (!loading && !authenticated) {
      router.replace(`/login?redirect=${encodeURIComponent(redirectPath)}`);
    }
  }, [authenticated, loading, redirectPath, router]);

  return loading || !authenticated;
}
