import type { ReactNode } from "react";

import { PortfolioFooter } from "@/components/portfolio/layout/PortfolioFooter";

/** Portfolio page wrapper — header comes from AppHeader in root layout. */
export function PortfolioShell({ children }: { children: ReactNode }) {
  return (
    <>
      <main className="mx-auto min-h-[calc(100vh-3.5rem)] max-w-3xl px-6 py-8">{children}</main>
      <PortfolioFooter />
    </>
  );
}
