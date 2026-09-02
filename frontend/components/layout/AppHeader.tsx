"use client";

import { usePathname } from "next/navigation";
import { Suspense } from "react";

import { PortfolioHeader } from "@/components/portfolio/layout/PortfolioHeader";
import { SuiteHeader } from "@/components/layout/SuiteHeader";

function HeaderSwitch() {
  const pathname = usePathname() || "";
  const isPortfolio =
    pathname === "/" || pathname === "/about" || pathname.startsWith("/projects");

  if (isPortfolio) {
    return <PortfolioHeader />;
  }
  return <SuiteHeader />;
}

export function AppHeader() {
  return (
    <Suspense fallback={<div className="h-14 border-b border-[#2A2A2A] bg-[#0E0E0E]/95" />}>
      <HeaderSwitch />
    </Suspense>
  );
}
