import { CitationHover } from "@/components/dashboard/CitationHover";
import { MediaAvatar } from "@/components/dashboard/MediaAvatar";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import { formatUsd } from "@/lib/formatMoney";
import { driverHeadshotUrl } from "@/lib/media";
import type { DriverStanding } from "@/lib/types";

function initials(name: string): string {
  return name
    .split(" ")
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0]?.toUpperCase() ?? "")
    .join("");
}

function roiBand(fer: number | null | undefined): { label: string; xp: number; tone: string } {
  if (fer == null) {
    return { label: "Unrated", xp: 12, tone: "bg-muted" };
  }
  if (fer < 200_000) {
    return { label: "S-tier ROI", xp: 96, tone: "bg-[color:var(--gold)]" };
  }
  if (fer < 500_000) {
    return { label: "A-tier ROI", xp: 68, tone: "bg-emerald-500" };
  }
  return { label: "B-tier spend", xp: 34, tone: "bg-orange-500" };
}

export function DriverCard({ row, maxPoints = 0 }: { row: DriverStanding; maxPoints?: number }) {
  const band = roiBand(row.financial_efficiency);
  const xp = maxPoints > 0 ? Math.min(100, Math.round((row.points / maxPoints) * 100)) : band.xp;
  return (
    <Card className="overflow-hidden border-[color:var(--gold)]/25 bg-[linear-gradient(180deg,rgba(200,162,74,0.12),transparent_42%),var(--card)] shadow-[0_0_24px_rgba(200,162,74,0.08)]">
      <CardContent className="pt-4">
        <div className="flex items-start justify-between gap-3">
          <MediaAvatar
            src={driverHeadshotUrl(row.full_name)}
            alt={row.full_name}
            fallback={initials(row.full_name)}
          />
          <div className="text-right">
            <Badge className="border-[color:var(--gold)]/40 bg-black/40 text-[color:var(--gold)]">P{row.position}</Badge>
            <p className="mt-1 text-[10px] uppercase tracking-[0.18em] text-[color:var(--gold)]">{band.label}</p>
          </div>
        </div>
        <p className="mt-3 font-serif text-lg leading-tight">{row.full_name}</p>
        <p className="text-xs text-muted-foreground">{row.team_name}</p>
        <div className="mt-3">
          <div className="mb-1 flex justify-between text-[10px] uppercase tracking-wider text-muted-foreground">
            <span>Championship XP</span>
            <span>{xp}%</span>
          </div>
          <div className="h-1.5 overflow-hidden rounded-full bg-secondary">
            <div className={`h-full ${band.tone}`} style={{ width: `${xp}%` }} />
          </div>
        </div>
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
            <dd className="font-semibold tabular-nums">{formatUsd(row.financial_efficiency ?? null, false)}</dd>
          </div>
        </dl>
      </CardContent>
    </Card>
  );
}

export function DriverRoiGrid({ rows }: { rows: DriverStanding[] }) {
  const top5 = rows.slice(0, 5);
  const maxPoints = Math.max(0, ...top5.map((row) => row.points));
  if (!top5.length) {
    return <p className="text-sm text-muted-foreground">No driver standings for this selection.</p>;
  }
  return (
    <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-5">
      {top5.map((row) => (
        <DriverCard key={row.driver_number} row={row} maxPoints={maxPoints} />
      ))}
    </div>
  );
}
