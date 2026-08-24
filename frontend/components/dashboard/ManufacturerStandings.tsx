import { CitationHover } from "@/components/dashboard/CitationHover";
import { TeamLogo } from "@/components/dashboard/MediaAvatar";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { formatUsd } from "@/lib/formatMoney";
import { constructorLogoFallbacks } from "@/lib/media";
import type { ConstructorStanding } from "@/lib/types";

export function ManufacturerStandings({ rows }: { rows: ConstructorStanding[] }) {
  if (!rows.length) {
    return <p className="text-sm text-muted-foreground">No constructor standings for this selection.</p>;
  }

  return (
    <div className="overflow-hidden rounded-sm border border-[#2A2A2A] bg-[#1A1A1A]">
      <div className="border-b border-[#2A2A2A] px-5 py-3">
        <p className="text-[10px] font-medium uppercase tracking-[0.2em] text-muted-foreground">Constructor book</p>
        <p className="mt-1 text-sm font-semibold">Event Classification &amp; ROI</p>
      </div>
      <Table>
        <TableHeader>
          <TableRow className="hover:bg-transparent">
            <TableHead className="font-mono uppercase tracking-widest">Pos</TableHead>
            <TableHead className="font-mono uppercase tracking-widest">Manufacturer</TableHead>
            <TableHead className="text-right font-mono uppercase tracking-widest">Constructor Yield</TableHead>
            <TableHead className="text-right font-mono uppercase tracking-widest">Valuation</TableHead>
            <TableHead className="text-right font-mono uppercase tracking-widest">Cap</TableHead>
            <TableHead className="text-right font-mono uppercase tracking-widest">USD / pt</TableHead>
            <TableHead className="text-right font-mono uppercase tracking-widest">Race wins</TableHead>
            <TableHead className="text-right font-mono uppercase tracking-widest">Wins / GP</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {rows.map((row) => (
            <TableRow key={row.team_name} className="hover:bg-white/[0.03]">
              <TableCell className="font-mono tabular-nums">{row.position}</TableCell>
              <TableCell className="font-medium">
                <span className="inline-flex items-center gap-2">
                  <TeamLogo urls={constructorLogoFallbacks(row.team_name)} alt={row.team_name} />
                  {row.team_name}
                </span>
              </TableCell>
              <TableCell className="text-right font-mono tabular-nums">{row.points}</TableCell>
              <TableCell className="text-right">
                <span className="mr-2 font-mono tabular-nums">{formatUsd(row.valuation_usd)}</span>
                <CitationHover label={row.valuation?.status ?? "n/a"} citation={row.valuation} />
              </TableCell>
              <TableCell className="text-right font-mono tabular-nums">{formatUsd(row.budget_cap_usd)}</TableCell>
              <TableCell className="text-right font-mono tabular-nums">{formatUsd(row.cost_per_point, false)}</TableCell>
              <TableCell className="text-right font-mono tabular-nums">{row.wins ?? 0}</TableCell>
              <TableCell className="text-right font-mono tabular-nums">{(row.avg_wins ?? 0).toFixed(2)}</TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  );
}
