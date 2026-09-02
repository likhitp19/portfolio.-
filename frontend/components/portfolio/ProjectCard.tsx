import Link from "next/link";
import { ArrowUpRight } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import type { ProjectSummary } from "@/lib/portfolio/types";
import { cn } from "@/lib/utils";

function StatusBadge({ status }: { status: ProjectSummary["status"] }) {
  if (status === "live") {
    return (
      <Badge className="rounded-full border border-[#10B981]/30 bg-[#10B981]/10 text-[10px] uppercase tracking-wider text-[#10B981]">
        Live
      </Badge>
    );
  }
  return (
    <Badge className="rounded-full border border-[#C8A24A]/30 bg-[#C8A24A]/10 text-[10px] uppercase tracking-wider text-[#C8A24A]">
      Coming soon
    </Badge>
  );
}

export function ProjectCard({ project }: { project: ProjectSummary }) {
  const isComingSoon = project.status === "coming-soon";

  return (
    <Card
      className={cn(
        "group flex h-full flex-col overflow-hidden border-[#262626] bg-[#121212] transition-all duration-300",
        isComingSoon
          ? "opacity-95 hover:border-[#C8A24A]/30"
          : "hover:border-[#C8A24A]/50 hover:shadow-[0_20px_40px_rgba(0,0,0,0.35)]",
      )}
    >
      <CardContent className="flex flex-1 flex-col p-6">
        <div className="mb-4 flex flex-wrap items-center gap-2">
          <StatusBadge status={project.status} />
          {project.tags.slice(0, 3).map((tag) => (
            <Badge
              key={tag}
              className="rounded-full border-[#262626] bg-[#0A0A0A] text-[10px] uppercase tracking-wider text-muted-foreground"
            >
              {tag}
            </Badge>
          ))}
        </div>
        <h2
          className={cn(
            "font-serif text-xl font-semibold tracking-tight",
            !isComingSoon && "group-hover:text-[#C8A24A]",
          )}
        >
          {project.title}
        </h2>
        <p className="mt-1 text-xs uppercase tracking-[0.14em] text-muted-foreground">{project.subtitle}</p>
        <p className="mt-4 flex-1 text-sm leading-relaxed text-muted-foreground">{project.excerpt}</p>

        <div className="mt-6 space-y-2 border-t border-[#262626] pt-4 text-xs text-muted-foreground">
          <p>
            <span className="font-semibold text-[#10B981]">Business · </span>
            {project.businessHook}
          </p>
          <p>
            <span className="font-semibold text-[#C8A24A]">Technical · </span>
            {project.technicalHook}
          </p>
        </div>

        <div className="mt-6 flex flex-wrap gap-2">
          {isComingSoon ? (
            <Button asChild variant="outline" size="sm" className="rounded-sm border-[#262626] text-muted-foreground">
              <Link href={`/projects/${project.slug}`}>Preview page</Link>
            </Button>
          ) : (
            <>
              <Button asChild size="sm" className="rounded-sm bg-[#C8A24A] text-[#0A0A0A] hover:bg-[#eac166]">
                <Link href={`/projects/${project.slug}`}>
                  Case study
                  <ArrowUpRight className="h-3.5 w-3.5" />
                </Link>
              </Button>
              {project.links[0] ? (
                <Button asChild variant="outline" size="sm" className="rounded-sm border-[#262626]">
                  <Link href={project.links[0].href}>Live demo</Link>
                </Button>
              ) : null}
            </>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
