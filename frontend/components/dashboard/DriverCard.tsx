import { CitationHover } from "@/components/dashboard/CitationHover";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import { formatUsd } from "@/lib/formatMoney";
import type { DriverStanding } from "@/lib/types";

function initials(name: string): string {
  return name
    .split(" ")
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0]?.toUpperCase() ?? "")
    .join("");
}

function roiBand(fer: number | null | undefined): string {
  if (fer == null) {
    return "n/a";
  }
  if (fer < 200_000) {
    return "High ROI";
  }
  if (fer < 500_000) {
    return "Fair ROI";
  }
  return "Expensive";
}

export function DriverCard({ row }: { row: DriverStanding }) {
  return (
    <Card className="overflow-hidden border-border bg-gradient-to-b from-card to-background">
      <CardContent className="pt-4">
        <div className="flex items-start justify-between gap-3">
          <div className="flex h-14 w-14 items-center justify-center rounded-full border border-border bg-secondary text-sm font-bold tracking-wide">
            {initials(row.full_name)}
          </div>
          <Badge>P{row.position}</Badge>
        </div>
        <p className="mt-3 text-lg font-semibold leading-tight">{row.full_name}</p>
        <p className="text-xs text-muted-foreground">{row.team_name}</p>
        <dl className="mt-4 grid grid-cols-2 gap-2 text-sm">
          <div>
            <dt className="text-xs uppercase text-muted-foreground">Points</dt>
            <dd className="font-semibold tabular-nums">{row.points}</dd>
          </div>
          <div>
            <dt className="text-xs uppercase text-muted-foreground">Salary</dt>
            <dd className="flex items-center gap-1 font-semibold">
              <span className="tabular-nums">{formatUsd(row.salary_usd ?? null)}</span>
              <CitationHover label={row.salary?.status ?? "defaulted"} citation={row.salary} />
            </dd>
          </div>
          <div className="col-span-2">
            <dt className="text-xs uppercase text-muted-foreground">FER (salary / pts)</dt>
            <dd className="flex items-center gap-2 font-semibold">
              <span className="tabular-nums">{formatUsd(row.financial_efficiency ?? null, false)}</span>
              <Badge>{roiBand(row.financial_efficiency)}</Badge>
            </dd>
          </div>
        </dl>
      </CardContent>
    </Card>
  );
}

export function DriverRoiGrid({ rows }: { rows: DriverStanding[] }) {
  const top5 = rows.slice(0, 5);
  if (!top5.length) {
    return <p className="text-sm text-muted-foreground">No driver standings for this selection.</p>;
  }
  return (
    <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-5">
      {top5.map((row) => (
        <DriverCard key={row.driver_number} row={row} />
      ))}
    </div>
  );
}
