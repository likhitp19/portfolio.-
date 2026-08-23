"use client";

import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { ConstructorStanding } from "@/lib/types";

export function ManufacturerPointsChart({ rows }: { rows: ConstructorStanding[] }) {
  const data = rows.slice(0, 10).map((row) => ({
    team: row.team_name.replace(" Racing", ""),
    points: row.points,
  }));
  if (!data.length) {
    return null;
  }
  return (
    <Card className="mt-4">
      <CardHeader>
        <CardTitle className="text-base">Constructor championship points</CardTitle>
        <p className="text-xs text-muted-foreground">
          Official manufacturer standings — both cars combined, not individual drivers.
        </p>
      </CardHeader>
      <CardContent className="h-72">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data}>
            <CartesianGrid strokeDasharray="3 3" stroke="oklch(1 0 0 / 12%)" />
            <XAxis dataKey="team" tick={{ fontSize: 11 }} />
            <YAxis tick={{ fontSize: 11 }} />
            <Tooltip
              contentStyle={{ background: "#18181b", border: "1px solid #27272a", borderRadius: 8 }}
              formatter={(value) => [`${value} pts`, "Constructors"]}
            />
            <Bar dataKey="points" fill="#c8a24a" radius={[4, 4, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
}
