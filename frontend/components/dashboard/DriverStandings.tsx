import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import type { DriverStanding } from "@/lib/types";

export function DriverStandings({ rows }: { rows: DriverStanding[] }) {
  const top5 = rows.slice(0, 5);
  if (!top5.length) {
    return <p className="text-sm text-muted-foreground">No driver standings for this selection.</p>;
  }
  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>Pos</TableHead>
          <TableHead>Driver</TableHead>
          <TableHead>Team</TableHead>
          <TableHead className="text-right">Points</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {top5.map((row) => (
          <TableRow key={row.driver_number}>
            <TableCell>{row.position}</TableCell>
            <TableCell>{row.full_name}</TableCell>
            <TableCell>{row.team_name}</TableCell>
            <TableCell className="text-right">{row.points}</TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}
