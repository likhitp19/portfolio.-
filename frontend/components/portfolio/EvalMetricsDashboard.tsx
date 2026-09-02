"use client";

import { Progress } from "@/components/ui/progress";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import type { EvalSuite } from "@/lib/portfolio/types";
import { cn } from "@/lib/utils";

const STATUS_STYLES = {
  pass: "border-[#10B981]/40 text-[#10B981]",
  partial: "border-[#C8A24A]/40 text-[#C8A24A]",
  roadmap: "border-[#2A2A2A] text-muted-foreground",
} as const;

export type EvalMetricsDashboardProps = {
  suite: EvalSuite;
  className?: string;
};

/**
 * Portfolio eval summary — golden catalog, dimension scores, and case matrix.
 * Scores reflect shipped pytest + rubric coverage, not live production telemetry.
 */
export function EvalMetricsDashboard({ suite, className }: EvalMetricsDashboardProps) {
  const implemented = suite.cases.filter((c) => c.status === "pass").length;
  const partial = suite.cases.filter((c) => c.status === "partial").length;
  const roadmap = suite.cases.filter((c) => c.status === "roadmap").length;

  return (
    <section className={cn("space-y-8", className)} aria-labelledby="eval-heading">
      <div>
        <p className="text-[10px] font-semibold uppercase tracking-[0.24em] text-[#C8A24A]">System evaluation</p>
        <h2 id="eval-heading" className="mt-2 font-serif text-2xl font-semibold text-[#FAFAFA]">
          {suite.name}
        </h2>
        <p className="mt-2 max-w-2xl text-sm text-muted-foreground">
          Rigorous benchmarking via{" "}
          <code className="rounded bg-[#1A1A1A] px-1.5 py-0.5 font-mono text-xs">{suite.catalogPath}</code> — deterministic
          routing checks, forbidden-tool guards, offline RAG validation, and LLM-as-judge rubrics on server traces.
        </p>
      </div>

      <div className="grid gap-4 sm:grid-cols-3">
        <StatCard label="Passing cases" value={String(implemented)} hint="Pytest-gated routing + transforms" />
        <StatCard label="Partial coverage" value={String(partial)} hint="Routing yes; prose inference labeled" />
        <StatCard label="Phase 4 eval targets" value={String(roadmap)} hint="Catalog entries awaiting roadmap features" />
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        {suite.dimensions.map((dim) => (
          <Card key={dim.id} className="border-[#2A2A2A] bg-[#111111] shadow-none">
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-semibold">{dim.label}</CardTitle>
              <p className="text-xs text-muted-foreground">{dim.description}</p>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="flex items-end justify-between gap-2">
                <span className="font-mono text-2xl font-bold tabular-nums text-[#FAFAFA]">
                  {dim.score}%
                </span>
                <span className="text-[10px] uppercase tracking-[0.14em] text-muted-foreground">{dim.method}</span>
              </div>
              <Progress value={dim.score} className="h-1.5 bg-[#2A2A2A]" />
            </CardContent>
          </Card>
        ))}
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        {suite.methods.map((method) => (
          <Card key={method.title} className="border-[#2A2A2A] bg-[#0A0A0A] shadow-none">
            <CardContent className="p-5">
              <p className="text-xs font-semibold uppercase tracking-[0.16em] text-[#E10600]">{method.title}</p>
              <p className="mt-2 text-sm leading-relaxed text-muted-foreground">{method.body}</p>
            </CardContent>
          </Card>
        ))}
      </div>

      <div className="overflow-hidden rounded-sm border border-[#2A2A2A]">
        <div className="border-b border-[#2A2A2A] bg-[#1A1A1A] px-5 py-3">
          <p className="text-[10px] font-medium uppercase tracking-[0.2em] text-muted-foreground">Golden catalog matrix</p>
        </div>
        <Table>
          <TableHeader>
            <TableRow className="hover:bg-transparent">
              <TableHead className="w-12 font-mono text-xs">#</TableHead>
              <TableHead className="font-mono text-xs uppercase">Case</TableHead>
              <TableHead className="font-mono text-xs uppercase">Intent</TableHead>
              <TableHead className="font-mono text-xs uppercase">Status</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {suite.cases.map((row) => (
              <TableRow key={row.id} className="hover:bg-white/[0.02]">
                <TableCell className="font-mono text-xs tabular-nums">{row.id}</TableCell>
                <TableCell>
                  <p className="text-sm font-medium">{row.title}</p>
                  <p className="mt-0.5 line-clamp-1 text-xs text-muted-foreground">{row.query}</p>
                </TableCell>
                <TableCell className="font-mono text-xs text-[#C8A24A]">{row.expectedIntent}</TableCell>
                <TableCell>
                  <Badge
                    className={cn(
                      "rounded-sm bg-transparent text-[10px] uppercase tracking-wider",
                      STATUS_STYLES[row.status],
                    )}
                  >
                    {row.status === "roadmap" ? "Phase 4 target" : row.status}
                  </Badge>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>
    </section>
  );
}

function StatCard({ label, value, hint }: { label: string; value: string; hint: string }) {
  return (
    <Card className="border-[#2A2A2A] bg-[#111111] shadow-none">
      <CardContent className="p-5">
        <p className="text-[10px] uppercase tracking-[0.16em] text-muted-foreground">{label}</p>
        <p className="mt-1 font-mono text-3xl font-bold tabular-nums">{value}</p>
        <p className="mt-1 text-xs text-muted-foreground">{hint}</p>
      </CardContent>
    </Card>
  );
}
