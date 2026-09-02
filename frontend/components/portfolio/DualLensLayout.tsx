"use client";

import { useState } from "react";

import { DualLensToggle } from "@/components/portfolio/DualLensToggle";
import { LensPanel } from "@/components/portfolio/LensPanel";
import type { LensId, ProjectLensContent } from "@/lib/portfolio/types";
import { cn } from "@/lib/utils";

export type DualLensLayoutProps = {
  business: ProjectLensContent;
  technical: ProjectLensContent;
  className?: string;
  /** lg+: show both columns side-by-side when true */
  sideBySideOnDesktop?: boolean;
};

export function DualLensLayout({
  business,
  technical,
  className,
  sideBySideOnDesktop = false,
}: DualLensLayoutProps) {
  const [lens, setLens] = useState<LensId>("business");
  const active = lens === "business" ? business : technical;

  if (sideBySideOnDesktop) {
    return (
      <div className={cn("space-y-8", className)}>
        <DualLensToggle value={lens} onChange={setLens} className="lg:hidden" />
        <div className="hidden gap-8 lg:grid lg:grid-cols-2">
          <LensPanel content={business} variant="business" />
          <LensPanel content={technical} variant="technical" />
        </div>
        <div className="lg:hidden">
          <LensPanel content={active} variant={lens} />
        </div>
      </div>
    );
  }

  return (
    <div className={cn("space-y-8", className)}>
      <DualLensToggle value={lens} onChange={setLens} />
      <LensPanel content={active} variant={lens} key={lens} />
    </div>
  );
}
