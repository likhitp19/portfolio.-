"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

import { cn } from "@/lib/utils";
import { PROFILE } from "@/lib/portfolio/profile";

const NAV = [
  { href: "/", label: "Home", match: (pathname: string) => pathname === "/" },
  { href: "/#education", label: "Education", match: () => false },
  { href: "/#experience", label: "Experience", match: () => false },
  { href: "/#projects", label: "Projects", match: (pathname: string) => pathname.startsWith("/projects") },
] as const;

export function PortfolioHeader() {
  const pathname = usePathname() || "";

  return (
    <header className="sticky top-0 z-[60] border-b border-[#262626] bg-[#0A0A0A]/95 backdrop-blur-md">
      <div className="mx-auto flex h-14 max-w-3xl items-center justify-between gap-4 px-6">
        <Link href="/" className="font-serif text-lg font-semibold text-[#FAFAFA] hover:text-[#C8A24A]">
          {PROFILE.name}
        </Link>

        <nav aria-label="Portfolio" className="flex items-center gap-1">
          {NAV.map((item) => {
            const active = item.match(pathname);
            return (
              <Link
                key={item.href}
                href={item.href}
                className={cn(
                  "rounded-sm px-2.5 py-1.5 text-xs font-medium text-muted-foreground transition-colors hover:text-foreground sm:px-3 sm:text-sm",
                  active && "text-[#C8A24A]",
                )}
              >
                {item.label}
              </Link>
            );
          })}
        </nav>
      </div>
    </header>
  );
}
