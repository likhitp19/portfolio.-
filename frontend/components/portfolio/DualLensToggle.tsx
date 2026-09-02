"use client";

import { Briefcase, Cpu } from "lucide-react";

import { cn } from "@/lib/utils";
import type { LensId } from "@/lib/portfolio/types";

export type DualLensToggleProps = {
  value: LensId;
  onChange: (lens: LensId) => void;
  className?: string;
  businessLabel?: string;
  technicalLabel?: string;
};

const OPTIONS: { id: LensId; label: string; short: string; icon: typeof Briefcase }[] = [
  { id: "business", label: "Business Lens", short: "Business", icon: Briefcase },
  { id: "technical", label: "Technical Lens", short: "Technical", icon: Cpu },
];

/**
 * Segmented control for dual-audience case studies.
 * Mobile: full-width stack. Desktop: inline pill with icons.
 */
export function DualLensToggle({
  value,
  onChange,
  className,
  businessLabel = "Business Lens",
  technicalLabel = "Technical Lens",
}: DualLensToggleProps) {
  const labels: Record<LensId, string> = {
    business: businessLabel,
    technical: technicalLabel,
  };

  return (
    <div
      role="tablist"
      aria-label="Case study perspective"
      className={cn(
        "inline-flex w-full max-w-md rounded-sm border border-[#2A2A2A] bg-[#0E0E0E] p-1 sm:w-auto",
        className,
      )}
    >
      {OPTIONS.map((option) => {
        const active = value === option.id;
        const Icon = option.icon;
        return (
          <button
            key={option.id}
            type="button"
            role="tab"
            aria-selected={active}
            onClick={() => onChange(option.id)}
            className={cn(
              "flex flex-1 items-center justify-center gap-2 rounded-sm px-4 py-2.5 text-[11px] font-semibold uppercase tracking-[0.14em] transition-all sm:flex-initial sm:px-5",
              active
                ? "bg-[#E10600]/15 text-[#E10600] ring-1 ring-[#E10600]/40 shadow-[0_0_12px_rgba(225,6,0,0.1)]"
                : "text-muted-foreground hover:bg-[#1A1A1A] hover:text-foreground",
            )}
          >
            <Icon className="h-3.5 w-3.5 shrink-0" aria-hidden />
            <span className="hidden sm:inline">{labels[option.id]}</span>
            <span className="sm:hidden">{option.short}</span>
          </button>
        );
      })}
    </div>
  );
}
