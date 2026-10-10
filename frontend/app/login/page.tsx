import { Suspense } from "react";

import { LoginPage } from "@/components/auth/LoginPage";

export default function LoginRoute() {
  return (
    <Suspense fallback={<main className="min-h-screen bg-[#f7f8fc]" />}>
      <LoginPage />
    </Suspense>
  );
}
