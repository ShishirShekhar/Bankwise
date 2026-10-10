"use client";

import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import type { FormEvent } from "react";
import { useState } from "react";

import { useAuth } from "@/components/auth/AuthProvider";
import { LoginBrandPanel } from "@/components/auth/LoginBrandPanel";
import { LoginForm } from "@/components/auth/LoginForm";
import { signInWithEmail, signInWithGoogle, signUpWithEmail } from "@/lib/auth";
import { askBankwise, redactSensitiveInput } from "@/lib/bankwise";
import { setSessionStorageValue } from "@/lib/session-storage";

export function LoginPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { refreshUser } = useAuth();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [mode, setMode] = useState<"login" | "signup">("login");

  async function continueToBankwise(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (loading) return;
    setLoading(true);
    setError(null);
    try {
      const form = new FormData(event.currentTarget);
      if (mode === "signup") {
        await signUpWithEmail(String(form.get("email")), String(form.get("password")));
      } else {
        await signInWithEmail(String(form.get("email")), String(form.get("password")));
      }
      if (!(await refreshUser())) {
        throw new Error("Sign-in completed, but your session could not be confirmed. Please retry.");
      }
      await finishLogin();
    } catch (reason) {
      setError(
        reason instanceof Error ? reason.message : "Something went wrong. Please try again.",
      );
    } finally {
      setLoading(false);
    }
  }

  async function finishLogin() {
    const pendingQuery = window.sessionStorage.getItem("bankwise:pending-query");
    if (pendingQuery) {
      const result = await askBankwise(redactSensitiveInput(pendingQuery));
      setSessionStorageValue("bankwise:last-ask", JSON.stringify(result));
      window.sessionStorage.removeItem("bankwise:pending-query");
      router.replace("/compare");
      return;
    }
    const redirect = searchParams.get("redirect");
    router.replace(redirect === "/compare" ? "/compare" : "/dashboard");
  }

  function startGoogleSignIn() {
    setLoading(true);
    setError(null);
    void signInWithGoogle()
      .then(async () => {
        if (!(await refreshUser())) {
          throw new Error("Sign-in completed, but your session could not be confirmed. Please retry.");
        }
        await finishLogin();
      })
      .catch((reason: unknown) => {
        setError(reason instanceof Error ? reason.message : "Google sign-in could not be completed.");
      })
      .finally(() => setLoading(false));
  }

  return (
    <main className="min-h-screen bg-[#f7f8fc] text-gray-900">
      <div className="flex min-h-screen flex-col lg:flex-row">
        <LoginBrandPanel />
        <section className="flex w-full items-center justify-center px-6 py-12 lg:w-1/2">
          <div className="w-full max-w-md">
            <p className="text-sm font-semibold text-blue-700">
              <Link href="/">← Back to BankWise</Link>
            </p>
            <div className="mt-8 mb-8">
              <h2 className="text-3xl font-semibold tracking-tight">
                {mode === "signup" ? "Create your account" : "Welcome back"}
              </h2>
              <p className="mt-2 text-gray-500">
                {mode === "signup" ? "Sign up to continue to BankWise." : "Sign in to continue to BankWise."}
              </p>
            </div>
            <LoginForm onSubmit={(event) => void continueToBankwise(event)} loading={loading} mode={mode} />
            <button
              type="button"
              onClick={() => setMode(mode === "login" ? "signup" : "login")}
              className="mt-3 w-full text-sm font-medium text-blue-700 hover:text-blue-800"
            >
              {mode === "login" ? "New to BankWise? Create an account" : "Already have an account? Sign in"}
            </button>
            <div className="my-5 flex items-center gap-4">
              <div className="h-px flex-1 bg-gray-200" />
              <span className="text-sm text-gray-400">or</span>
              <div className="h-px flex-1 bg-gray-200" />
            </div>
            <button
              type="button"
              onClick={startGoogleSignIn}
              disabled={loading}
              className="w-full rounded-xl border border-blue-200 bg-blue-50 px-4 py-3.5 font-semibold text-[#172554] transition hover:bg-blue-100 disabled:opacity-60"
            >
              Continue with Google
            </button>
            {error && (
              <p role="alert" className="mt-4 text-sm text-red-700">
                {error}
              </p>
            )}
            <p className="mt-8 text-center text-xs leading-5 text-gray-400">
              BankWise provides information and comparisons to help you understand financial
              products. Always review official product terms before deciding.
            </p>
          </div>
        </section>
      </div>
    </main>
  );
}
