import type { FormEvent } from "react";

export function LoginForm({
  onSubmit,
  loading,
  mode,
}: {
  onSubmit: (event: FormEvent<HTMLFormElement>) => void;
  loading: boolean;
  mode: "login" | "signup";
}) {
  return (
    <form onSubmit={onSubmit} className="space-y-5">
      <div>
        <label htmlFor="email" className="mb-2 block text-sm font-medium text-gray-700">
          Email address
        </label>
        <input
          id="email"
          name="email"
          type="email"
          autoComplete="email"
          placeholder="you@example.com"
          required
          className="w-full rounded-xl border border-gray-200 bg-white px-4 py-3.5 outline-none focus:border-blue-600 focus:ring-2 focus:ring-blue-100"
        />
      </div>
      <div>
        <label htmlFor="password" className="mb-2 block text-sm font-medium text-gray-700">
          Password
        </label>
        <input
          id="password"
          name="password"
          type="password"
          autoComplete={mode === "signup" ? "new-password" : "current-password"}
          minLength={mode === "signup" ? 6 : undefined}
          placeholder="Enter your password"
          required
          className="w-full rounded-xl border border-gray-200 bg-white px-4 py-3.5 outline-none focus:border-blue-600 focus:ring-2 focus:ring-blue-100"
        />
      </div>
      <button
        type="submit"
        disabled={loading}
        className="w-full rounded-xl bg-[#172554] px-4 py-3.5 font-medium text-white transition hover:bg-[#1e3a8a] disabled:opacity-60"
      >
        {loading ? "Please wait…" : mode === "signup" ? "Create account" : "Sign in"}
      </button>
    </form>
  );
}
