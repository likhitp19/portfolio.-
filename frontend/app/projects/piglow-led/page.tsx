import type { Metadata } from "next";
import Link from "next/link";
import { ArrowLeft, Cpu } from "lucide-react";

import { PortfolioShell } from "@/components/portfolio/layout/PortfolioShell";
import { Button } from "@/components/ui/button";
import { getProject } from "@/lib/portfolio/projects";

const project = getProject("piglow-led");

export const metadata: Metadata = {
  title: project ? `${project.title} — Coming soon` : "PiGlow LED — Coming soon",
  description: project?.excerpt,
};

export default function PiGlowProjectPage() {
  if (!project) {
    return null;
  }

  return (
    <PortfolioShell>
      <div className="mb-8">
        <Button asChild variant="ghost" size="sm" className="rounded-sm text-muted-foreground">
          <Link href="/#projects">
            <ArrowLeft className="h-4 w-4" />
            Back to projects
          </Link>
        </Button>
      </div>

      <header className="max-w-2xl space-y-6">
        <p className="font-mono text-[10px] font-medium uppercase tracking-[0.28em] text-[#C8A24A]">Coming soon</p>
        <div className="flex h-14 w-14 items-center justify-center rounded-sm border border-[#262626] bg-[#121212] text-[#10B981]">
          <Cpu className="h-7 w-7" />
        </div>
        <h1 className="font-serif text-4xl font-semibold tracking-tight text-[#FAFAFA]">{project.title}</h1>
        <p className="text-sm uppercase tracking-[0.14em] text-muted-foreground">{project.subtitle}</p>
        <p className="text-base leading-relaxed text-muted-foreground">{project.excerpt}</p>
      </header>

      <section className="mt-16 grid gap-4 md:grid-cols-2">
        <article className="rounded-sm border border-[#262626] bg-[#121212] p-6">
          <h2 className="text-sm font-semibold uppercase tracking-[0.14em] text-[#10B981]">Planned scope</h2>
          <ul className="mt-4 space-y-2 text-sm text-muted-foreground">
            <li>PiGlow I2C modules on Raspberry Pi with Python orchestration</li>
            <li>Web dashboard for sequences, brightness, and reactive modes</li>
            <li>LAN WebSocket control plane for multi-device sync</li>
            <li>Case study with hardware photos and timing diagrams</li>
          </ul>
        </article>
        <article className="rounded-sm border border-[#262626] bg-[#121212] p-6">
          <h2 className="text-sm font-semibold uppercase tracking-[0.14em] text-[#C8A24A]">Workspace</h2>
          <p className="mt-4 text-sm leading-relaxed text-muted-foreground">
            Source will live in the <code className="rounded bg-[#0A0A0A] px-1.5 py-0.5 font-mono text-xs">iot/</code>{" "}
            folder at the repo root.
          </p>
          <Button asChild className="mt-6 rounded-sm bg-[#C8A24A] text-[#0A0A0A] hover:bg-[#eac166]">
            <Link href="/#projects">See all projects</Link>
          </Button>
        </article>
      </section>
    </PortfolioShell>
  );
}
