import type { Route } from "next";
import type { ReactNode } from "react";

import { BrandMark } from "@/components/shared/BrandMark";

export function SiteHeader({
  children,
  brandHref = "/",
}: {
  children?: ReactNode;
  brandHref?: Route;
}) {
  return (
    <header className="border-b border-gray-200 bg-white">
      <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-5">
        <BrandMark href={brandHref} />
        {children}
      </div>
    </header>
  );
}
