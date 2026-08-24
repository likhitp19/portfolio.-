import { Activity, Landmark, Receipt, TrendingUp } from "lucide-react";

import { CostPerPointChart } from "@/components/dashboard/CostPerPointChart";
import { ManufacturerStandings } from "@/components/dashboard/ManufacturerStandings";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import { formatUsd } from "@/lib/formatMoney";
import { manufacturerKpis } from "@/lib/manufacturerMetrics";
import type { ConstructorStanding } from "@/lib/types";

function formatIndex(value: number | null): string {
  if (value == null || Number.isNaN(value)) {
    return "—";
  }
  return value.toFixed(2);
}

function formatPct(value: number | null, digits = 1): string {
  if (value == null || Number.isNaN(value)) {
    return "—";
  }
  return `${(value * 100).toFixed(digits)}%`;
}

export function ManufacturerDashboard({
  rows,
  year,
}: {
  rows: ConstructorStanding[];
  year: number;
}) {
  const kpis = manufacturerKpis(rows);
  const inefficiencyTone =
    kpis.inefficiencyLabel === "HIGH"
      ? "text-[#E10600]"
      : kpis.inefficiencyLabel === "ELEVATED"
        ? "text-[#F59E0B]"
        : "text-[#10B981]";

  const cards = [
    {
      label: "Total Grid Valuation",
      value: formatUsd(kpis.totalGridValuation),
      hint: `${rows.length} constructors`,
      tone: "text-[#10B981]",
      icon: Landmark,
      bar: "w-3/4 bg-[#10B981]",
    },
    {
      label: "Avg. Budget Cap Spend",
      value: formatUsd(kpis.avgCap),
      hint: kpis.capUtilization != null ? `${formatPct(kpis.capUtilization, 0)} of $135M FIA cap` : "FIA cost cap class",
      tone: "text-[#F59E0B]",
      icon: Receipt,
      bar: "w-[98%] bg-[#F59E0B]",
    },
    {
      label: "Market Inefficiency Index",
      value: formatIndex(kpis.inefficiency),
      hint: kpis.inefficiencyLabel,
      tone: inefficiencyTone,
      icon: Activity,
      bar:
        kpis.inefficiencyLabel === "HIGH"
          ? "w-full bg-[#E10600]"
          : kpis.inefficiencyLabel === "ELEVATED"
            ? "w-2/3 bg-[#F59E0B]"
            : "w-1/3 bg-[#10B981]",
    },
    {
      label: "Constructor Yield Leader",
      value: kpis.leader ? `${kpis.leader.points} pts` : "—",
      hint: kpis.leader
        ? `${kpis.leader.team_name} · ${formatPct(kpis.yieldShare, 0)} of grid yield`
        : "No standings",
      tone: "text-[#10B981]",
      icon: TrendingUp,
      bar: "w-4/5 bg-[#10B981]",
    },
  ];

  return (
    <div className="space-y-6">
      <div className="flex items-end justify-between gap-4 border-b border-[#2A2A2A] pb-4">
        <div>
          <h2 className="text-3xl font-bold tracking-tight">Financial Telemetry</h2>
          <p className="mt-1 font-mono text-sm text-muted-foreground">
            SEASON {year} · COST PER POINT · CONSTRUCTOR YIELD
          </p>
        </div>
        <div className="flex gap-2">
          <Badge className="rounded-sm border-[#2A2A2A] bg-[#1A1A1A] font-mono text-[10px] uppercase tracking-widest text-muted-foreground">
            FY{year}
          </Badge>
          <Badge className="rounded-sm border-[#10B981]/30 bg-[#10B981]/10 font-mono text-[10px] uppercase tracking-widest text-[#10B981]">
            Fact store live
          </Badge>
        </div>
      </div>

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {cards.map((card) => (
          <Card key={card.label} className="rounded-sm border-[#2A2A2A] bg-[#1A1A1A] shadow-none transition-colors hover:border-[#A3A3A3]">
            <CardContent className="p-5">
              <div className="mb-4 flex items-start justify-between">
                <h3 className="text-[11px] font-medium uppercase tracking-[0.16em] text-muted-foreground">{card.label}</h3>
                <card.icon className="h-4 w-4 text-muted-foreground" />
              </div>
              <p className="font-mono text-3xl font-bold tracking-tight">{card.value}</p>
              <p className={`mt-1 font-mono text-xs font-bold ${card.tone}`}>{card.hint}</p>
              <div className="mt-4 h-1 w-full overflow-hidden rounded-sm bg-[#2A2A2A]">
                <div className={`h-full ${card.bar}`} />
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      <div className="grid gap-4 xl:grid-cols-[minmax(0,1fr)_280px]">
        <CostPerPointChart rows={rows} />
        <Card className="rounded-sm border-[#2A2A2A] bg-[#1A1A1A] shadow-none">
          <CardContent className="flex h-full flex-col p-5">
            <p className="text-[10px] font-medium uppercase tracking-[0.2em] text-[#E10600]">Co-Pilot Insight</p>
            <h3 className="mt-2 text-sm font-semibold tracking-tight">Generate AI Investment Thesis</h3>
            {kpis.efficient ? (
              <>
                <p className="mt-3 text-sm leading-relaxed text-muted-foreground">
                  {kpis.efficient.team_name} is the grid&apos;s most efficient manufacturer at{" "}
                  <span className="font-mono text-[#10B981]">{formatUsd(kpis.efficient.cost_per_point, false)}</span> per
                  constructor point against a {formatUsd(kpis.avgCpp)} average.
                </p>
                <p className="mt-4 border border-[#2A2A2A] bg-[#0A0A0A] px-3 py-2 font-mono text-[11px] leading-relaxed text-muted-foreground">
                  Prompt: Rank {year} constructors by cost per point and flag market inefficiency.
                </p>
              </>
            ) : (
              <p className="mt-3 text-sm text-muted-foreground">No cost-per-point series for this selection.</p>
            )}
            <p className="mt-auto pt-6 text-[10px] uppercase tracking-[0.16em] text-muted-foreground">
              Ask the co-pilot below
            </p>
          </CardContent>
        </Card>
      </div>

      <ManufacturerStandings rows={rows} />
    </div>
  );
}
