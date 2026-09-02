import type { Metadata } from "next";
import Link from "next/link";
import { ExternalLink } from "lucide-react";

import { DualLensLayout } from "@/components/portfolio/DualLensLayout";
import { EvalMetricsDashboard } from "@/components/portfolio/EvalMetricsDashboard";
import { Phase4Roadmap } from "@/components/portfolio/Phase4Roadmap";
import { PortfolioShell } from "@/components/portfolio/layout/PortfolioShell";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  APEX_F1_BUSINESS,
  APEX_F1_META,
  APEX_F1_TECHNICAL,
} from "@/lib/portfolio/apex-f1-content";
import { COMMERCIAL_EVAL_SUITE } from "@/lib/portfolio/eval-metrics";
import { PHASE4_ROADMAP } from "@/lib/portfolio/phase4-roadmap";

export const metadata: Metadata = {
  title: "Apex F1 Suite — Case Study",
  description: APEX_F1_META.oneLiner,
};

export default function ApexF1CaseStudyPage() {
  return (
    <PortfolioShell>
      {/* Hero */}
      <header className="mb-12 space-y-6 border-b border-[#2A2A2A] pb-10">
        <div className="flex flex-wrap gap-2">
          {APEX_F1_META.stack.map((item) => (
            <Badge key={item} className="rounded-sm border-[#2A2A2A] bg-[#0A0A0A] text-[10px] uppercase tracking-wider">
              {item}
            </Badge>
          ))}
        </div>
        <div>
          <p className="text-[10px] font-semibold uppercase tracking-[0.28em] text-[#C8A24A]">Case study · Project 1</p>
          <h1 className="mt-2 font-serif text-4xl font-semibold tracking-tight text-[#FAFAFA] sm:text-5xl">
            {APEX_F1_META.title}
          </h1>
          <p className="mt-2 text-sm uppercase tracking-[0.14em] text-[#E10600]">{APEX_F1_META.subtitle}</p>
        </div>
        <p className="max-w-3xl text-base leading-relaxed text-muted-foreground">{APEX_F1_META.oneLiner}</p>
        <p className="text-sm text-muted-foreground">
          <span className="font-semibold text-foreground">Role:</span> {APEX_F1_META.role}
        </p>
        <div className="flex flex-wrap gap-2">
          {APEX_F1_META.liveLinks.map((link) => (
            <Button key={link.href} asChild variant="outline" size="sm" className="rounded-sm border-[#2A2A2A]">
              <Link href={link.href}>
                {link.label}
                <ExternalLink className="h-3.5 w-3.5" />
              </Link>
            </Button>
          ))}
        </div>
      </header>

      {/* Dual lens deep dive */}
      <section className="mb-20 space-y-6">
        <div>
          <p className="text-[10px] font-semibold uppercase tracking-[0.24em] text-[#E10600]">Dual-lens narrative</p>
          <h2 className="mt-2 font-serif text-2xl font-semibold">One product, two proof points</h2>
          <p className="mt-2 max-w-2xl text-sm text-muted-foreground">
            Apex F1 Suite deliberately mirrors its own architecture: Apex Analytics for commercial stakeholders, Regulatory
            Desk for systems reviewers. Toggle below — or view side-by-side on large screens.
          </p>
        </div>
        <DualLensLayout business={APEX_F1_BUSINESS} technical={APEX_F1_TECHNICAL} sideBySideOnDesktop />
      </section>

      {/* Evals */}
      <div className="mb-20 border-t border-[#2A2A2A] pt-16">
        <EvalMetricsDashboard suite={COMMERCIAL_EVAL_SUITE} />
      </div>

      {/* Phase 4 roadmap */}
      <div className="mb-16 border-t border-[#2A2A2A] pt-16">
        <Phase4Roadmap items={PHASE4_ROADMAP} />
      </div>

      {/* Closing */}
      <section className="rounded-sm border border-[#2A2A2A] bg-[#111111] p-8 text-center">
        <h2 className="font-serif text-xl font-semibold">Same console. Two graphs. One trust model.</h2>
        <p className="mx-auto mt-3 max-w-xl text-sm text-muted-foreground">
          Shared sporting contract (<code className="font-mono text-xs">year</code>,{" "}
          <code className="font-mono text-xs">meeting_key</code>,{" "}
          <code className="font-mono text-xs">session_key</code>), separate LangGraph compilations, eval-gated agent
          behavior, and production split on Vercel + Railway.
        </p>
        <Button asChild className="mt-6 rounded-sm">
          <Link href="/season/2026?tab=manufacturer">Launch live demo</Link>
        </Button>
      </section>
    </PortfolioShell>
  );
}
