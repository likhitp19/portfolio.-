"use client";

import { CartesianGrid, Legend, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { progressionToChartRows } from "@/lib/chart";
import type { StandingsProgression } from "@/lib/types";

const LINE_COLORS = ["#ef4444", "#e5e7eb", "#f59e0b", "#38bdf8", "#a78bfa"];

export function PointsProgressionChart({
  data,
  title = "Top 5 points across circuits",
  subtitle,
}: {
  data: StandingsProgression;
  title?: string;
  subtitle?: string;
}) {
  const rows = progressionToChartRows(data);
  if (!rows.length || !data.series.length) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>{title}</CardTitle>
        </CardHeader>
        <CardContent className="text-sm text-muted-foreground">
          Not enough championship snapshots to draw a progression chart.
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="overflow-hidden border-[#2A2A2A] bg-[#1A1A1A]">
      <CardHeader>
        <CardTitle>{title}</CardTitle>
        {subtitle ? <p className="text-xs text-muted-foreground">{subtitle}</p> : null}
      </CardHeader>
      <CardContent className="h-80">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={rows}>
            <CartesianGrid stroke="#2A2A2A" vertical={false} />
            <XAxis dataKey="circuit" stroke="currentColor" tick={{ fontSize: 11 }} />
            <YAxis stroke="currentColor" tick={{ fontSize: 11 }} />
            <Tooltip
              contentStyle={{ background: "#0A0A0A", border: "1px solid #2A2A2A", borderRadius: 2 }}
              formatter={(value, name) => [`${value} pts`, String(name)]}
              labelFormatter={(label) => `GP: ${label}`}
            />
            <Legend />
            {data.series.map((series, index) => (
              <Line
                key={series.driver}
                type="monotone"
                dataKey={series.driver}
                stroke={LINE_COLORS[index % LINE_COLORS.length]}
                strokeWidth={2}
                dot={{ r: 3 }}
              />
            ))}
          </LineChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
}
