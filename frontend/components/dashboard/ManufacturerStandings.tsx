import { CitationHover } from "@/components/dashboard/CitationHover";
import { CostPerPointChart } from "@/components/dashboard/CostPerPointChart";
import { ManufacturerPointsChart } from "@/components/dashboard/ManufacturerPointsChart";
import { Card, CardContent } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { formatUsd } from "@/lib/formatMoney";
import type { ConstructorStanding } from "@/lib/types";

export function ManufacturerStandings({ rows }: { rows: ConstructorStanding[] }) {
  if (!rows.length) {
    return <p className="text-sm text-muted-foreground">No constructor standings for this selection.</p>;
  }
  const efficient = rows
    .filter((row) => row.cost_per_point != null && row.points > 0)
    .slice()
    .sort((a, b) => (a.cost_per_point ?? Infinity) - (b.cost_per_point ?? Infinity))[0];

  return (
    <div className="space-y-4">
      {efficient ? (
        <Card>
          <CardContent className="pt-4 text-sm">
            Most efficient: <span className="font-semibold">{efficient.team_name}</span> at{" "}
            {formatUsd(efficient.cost_per_point, false)} per point.
          </CardContent>
        </Card>
      ) : null}
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Pos</TableHead>
            <TableHead>Manufacturer</TableHead>
            <TableHead className="text-right">Points</TableHead>
            <TableHead className="text-right">Valuation</TableHead>
            <TableHead className="text-right">Cap</TableHead>
            <TableHead className="text-right">USD / pt</TableHead>
            <TableHead className="text-right">Wins</TableHead>
            <TableHead className="text-right">Avg wins</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {rows.map((row) => (
            <TableRow key={row.team_name}>
              <TableCell>{row.position}</TableCell>
              <TableCell className="font-medium">{row.team_name}</TableCell>
              <TableCell className="text-right tabular-nums">{row.points}</TableCell>
              <TableCell className="text-right">
                <span className="mr-2 tabular-nums">{formatUsd(row.valuation_usd)}</span>
                <CitationHover label={row.valuation?.status ?? "n/a"} citation={row.valuation} />
              </TableCell>
              <TableCell className="text-right tabular-nums">{formatUsd(row.budget_cap_usd)}</TableCell>
              <TableCell className="text-right tabular-nums">{formatUsd(row.cost_per_point, false)}</TableCell>
              <TableCell className="text-right tabular-nums">{row.wins ?? 0}</TableCell>
              <TableCell className="text-right tabular-nums">{(row.avg_wins ?? 0).toFixed(2)}</TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
      <ManufacturerPointsChart rows={rows} />
      <CostPerPointChart rows={rows} />
    </div>
  );
}
