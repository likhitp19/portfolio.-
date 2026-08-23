import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { ChampionshipSummary, ConstructorStanding } from "@/lib/types";

export function OverallSummary({
  summary,
  constructors = [],
}: {
  summary: ChampionshipSummary;
  constructors?: ConstructorStanding[];
}) {
  if (!summary.leader_name) {
    return <p className="text-sm text-muted-foreground">No championship summary for this season yet.</p>;
  }
  const items = [
    { label: "Leader", value: summary.leader_name },
    { label: "Leader points", value: String(summary.leader_points ?? "—") },
    { label: "Gap to P2", value: String(summary.points_gap ?? "—") },
    { label: "Races completed", value: String(summary.race_count) },
  ];
  const fastest =
    summary.fastest_lap_driver != null
      ? `${summary.fastest_lap_driver}${summary.fastest_lap_duration != null ? ` · ${summary.fastest_lap_duration}s` : ""}`
      : "—";
  const podium =
    summary.top3_finishes?.length
      ? summary.top3_finishes.map((row) => `${row.driver_name} (${row.count})`).join(", ")
      : "—";
  const manufacturer =
    summary.best_manufacturer_reason ||
    (constructors[0]
      ? `${constructors[0].team_name} leads the constructor table on ${constructors[0].points} pts.`
      : "—");
  const insights = [
    { label: "Fastest lap", value: fastest },
    { label: "Total DNFs", value: String(summary.total_dnfs ?? 0) },
    { label: "Top-3 finishes", value: podium },
  ];
  return (
    <div className="space-y-4">
      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        {items.map((item) => (
          <Card key={item.label}>
            <CardHeader className="pb-2">
              <CardTitle className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
                {item.label}
              </CardTitle>
            </CardHeader>
            <CardContent className="text-xl font-semibold">{item.value}</CardContent>
          </Card>
        ))}
      </div>
      <Card className="border-[color:var(--gold)]/25">
        <CardHeader className="pb-2">
          <CardTitle className="text-xs font-medium uppercase tracking-wide text-[color:var(--gold)]">
            Manufacturer to own
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className="font-serif text-2xl">{summary.best_manufacturer || constructors[0]?.team_name || "—"}</p>
          <p className="mt-2 text-sm leading-relaxed text-muted-foreground">{manufacturer}</p>
        </CardContent>
      </Card>
      <div>
        <p className="mb-2 text-xs font-medium uppercase tracking-wide text-muted-foreground">Insights overview</p>
        <div className="grid gap-3 sm:grid-cols-3">
          {insights.map((item) => (
            <Card key={item.label}>
              <CardHeader className="pb-2">
                <CardTitle className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
                  {item.label}
                </CardTitle>
              </CardHeader>
              <CardContent className="text-sm font-semibold leading-snug">{item.value}</CardContent>
            </Card>
          ))}
        </div>
      </div>
    </div>
  );
}
