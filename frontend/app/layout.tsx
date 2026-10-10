import "./globals.css";

import type { Metadata } from "next";

import { AuthProvider } from "@/components/auth/AuthProvider";

export const metadata: Metadata = {
  title: "BankWise | Compare fixed deposits with confidence",
  description: "Compare verified fixed deposit rates, maturity estimates, and withdrawal trade-offs.",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html lang="en" className="h-full antialiased">
      <body className="flex min-h-full flex-col">
        <AuthProvider>{children}</AuthProvider>
      </body>
    </html>
  );
}
