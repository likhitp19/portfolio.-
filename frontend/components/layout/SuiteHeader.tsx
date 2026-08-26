"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

import { cn } from "@/lib/utils";

const DESKS = [
  { href: "/season/2024", match: "/season", label: "Commercial Desk", shortLabel: "Commercial" },
  { href: "/steward", match: "/steward", label: "Regulatory Desk", shortLabel: "Regulatory" },
  { href: "/about", match: "/about", label: "About Me / Profile", shortLabel: "About" },
] as const;

function deskContextLabel(pathname: string): string {
  if (pathname.startsWith("/about")) return "Profile";
  if (pathname.startsWith("/steward")) return "Regulatory";
  return "Commercial";
}

export function SuiteHeader() {
  const pathname = usePathname() || "";

  return (
    <header className="sticky top-0 z-[60] border-b border-[#2A2A2A] bg-[#0E0E0E]/95 backdrop-blur-md">
      <div className="mx-auto flex h-14 max-w-7xl items-center justify-between gap-4 px-6">
        <div className="flex min-w-0 items-center gap-8">
          <Link href="/season/2024" className="group shrink-0">
            <p className="text-[10px] font-semibold uppercase tracking-[0.28em] text-[#C8A24A]">Enterprise</p>
            <p className="font-[family-name:var(--font-geist-mono),ui-monospace,monospace] text-base font-bold tracking-tight text-[#FAFAFA] transition-colors group-hover:text-[#E10600]">
              Apex F1 Suite
            </p>
          </Link>

          <nav aria-label="Product desks" className="hidden items-center gap-1 sm:flex">
            {DESKS.map((desk) => {
              const active = pathname === desk.match || pathname.startsWith(`${desk.match}/`);
              return (
                <Link
                  key={desk.href}
                  href={desk.href}
                  className={cn(
                    "rounded-sm px-3 py-1.5 text-[11px] font-semibold uppercase tracking-[0.14em] transition-all duration-200 ease-out",
                    active
                      ? "bg-[#E10600]/15 text-[#E10600] ring-1 ring-[#E10600]/40 shadow-[0_0_12px_rgba(225,6,0,0.12)]"
                      : "text-muted-foreground hover:bg-[#1A1A1A] hover:text-foreground hover:ring-1 hover:ring-[#2A2A2A]",
                  )}
                >
                  {desk.label}
                </Link>
              );
            })}
          </nav>
        </div>

        <div className="flex items-center gap-2">
          <span className="hidden text-[10px] uppercase tracking-[0.16em] text-muted-foreground transition-colors duration-200 md:inline">
            {deskContextLabel(pathname)}
          </span>
          <span className="h-1.5 w-1.5 rounded-full bg-[#10B981]" aria-hidden />
        </div>
      </div>

      {/* Mobile desk switcher */}
      <nav aria-label="Product desks mobile" className="flex gap-1 border-t border-[#2A2A2A] px-4 py-2 sm:hidden">
        {DESKS.map((desk) => {
          const active = pathname === desk.match || pathname.startsWith(`${desk.match}/`);
          return (
            <Link
              key={desk.href}
              href={desk.href}
              className={cn(
                "flex-1 rounded-sm px-2 py-1.5 text-center text-[10px] font-semibold uppercase tracking-[0.12em] transition-all duration-200 ease-out",
                active
                  ? "bg-[#E10600]/15 text-[#E10600] ring-1 ring-[#E10600]/30"
                  : "text-muted-foreground hover:bg-[#1A1A1A]",
              )}
            >
              {desk.shortLabel}
            </Link>
          );
        })}
      </nav>
    </header>
  );
}
