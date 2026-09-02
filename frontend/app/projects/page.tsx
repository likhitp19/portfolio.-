import type { Metadata } from "next";

import { PortfolioShell } from "@/components/portfolio/layout/PortfolioShell";
import { ProjectCard } from "@/components/portfolio/ProjectCard";
import { PROJECTS } from "@/lib/portfolio/projects";

export const metadata: Metadata = {
  title: "Projects — Likhit P.",
  description: "AI product case studies with Business and Technical dual-lens narratives",
};

export default function ProjectsPage() {
  return (
    <PortfolioShell>
      <header className="mb-12 max-w-2xl space-y-4">
        <p className="text-[10px] font-semibold uppercase tracking-[0.28em] text-[#C8A24A]">Projects hub</p>
        <h1 className="font-serif text-4xl font-semibold tracking-tight text-[#FAFAFA]">Work that speaks to both rooms</h1>
        <p className="text-base leading-relaxed text-muted-foreground">
          Each case study includes a <strong className="font-medium text-[#10B981]">Business Lens</strong> (KPIs,
          decision velocity, commercial logic) and a <strong className="font-medium text-[#C8A24A]">Technical Lens</strong>{" "}
          (LangGraph orchestration, API contracts, RAG, streaming). The gallery scales — add a project entry, get a new
          card and detail route.
        </p>
      </header>

      <div className="grid gap-6 md:grid-cols-2">
        {PROJECTS.map((project) => (
          <ProjectCard key={project.slug} project={project} />
        ))}
      </div>

      <p className="mt-12 text-center text-sm text-muted-foreground">
        More case studies in Phase 4 — same dual-lens template, new slugs under{" "}
        <code className="rounded bg-[#1A1A1A] px-1.5 py-0.5 font-mono text-xs">/projects/[slug]</code>
      </p>
    </PortfolioShell>
  );
}
