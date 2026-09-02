import Link from "next/link";

import { PROFILE } from "@/lib/portfolio/profile";

export function PortfolioFooter() {
  return (
    <footer className="mt-20 border-t border-[#2A2A2A] bg-[#0A0A0A]">
      <div className="mx-auto flex max-w-6xl flex-col gap-4 px-6 py-10 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <p className="font-serif text-lg font-semibold text-[#FAFAFA]">{PROFILE.name}</p>
          <p className="text-sm text-muted-foreground">{PROFILE.title}</p>
        </div>
        <div className="flex flex-wrap gap-4 text-sm">
          <Link href="/" className="text-muted-foreground hover:text-foreground">
            Home
          </Link>
          <Link href={`mailto:${PROFILE.email}`} className="text-[#C8A24A] hover:underline">
            {PROFILE.email}
          </Link>
          <Link href="/projects" className="text-muted-foreground hover:text-foreground">
            Projects
          </Link>
          <Link href="/season/2026" className="text-muted-foreground hover:text-foreground">
            Apex F1 live
          </Link>
        </div>
      </div>
    </footer>
  );
}
