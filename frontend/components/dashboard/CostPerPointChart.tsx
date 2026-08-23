"use client";

import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { formatUsd } from "@/lib/formatMoney";
import type { ConstructorStanding } from "@/lib/types";

export function CostPerPointChart({ rows }: { rows: ConstructorStanding[] }) {
  const data = rows
    .filter((row) => row.cost_per_point != null)
    .map((row) => ({
      team: row.team_name.replace(" Racing", ""),
      cpp: row.cost_per_point as number,
      points: row.points,
      cap: row.budget_cap_usd,
    }));
  if (!data.length) {
    return null;
  }
  return (
    <Card className="mt-4 border-[color:var(--gold)]/20 bg-[linear-gradient(180deg,rgba(185,28,28,0.08),transparent_38%),var(--card)]">
      <CardHeader>
        <CardTitle className="font-serif text-base tracking-tight">Cost per point — paddock board</CardTitle>
        <p className="text-xs text-muted-foreground">Cap (USD 135M class) divided by constructor championship points.</p>
      </CardHeader>
      <CardContent className="h-72">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data}>
            <CartesianGrid strokeDasharray="3 3" stroke="oklch(1 0 0 / 12%)" />
            <XAxis dataKey="team" tick={{ fontSize: 11 }} />
            <YAxis tick={{ fontSize: 11 }} tickFormatter={(v) => formatUsd(Number(v))} />
            <Tooltip
              contentStyle={{ background: "#18181b", border: "1px solid #27272a", borderRadius: 8 }}
              formatter={(value) => [formatUsd(Number(value), false), "USD / pt"]}
              labelFormatter={(label, payload) => {
                const row = payload?.[0]?.payload as { points?: number; cap?: number } | undefined;
                return `${label} · ${row?.points ?? "—"} pts · cap ${formatUsd(row?.cap ?? null)}`;
              }}
            />
            <Bar dataKey="cpp" fill="#ef4444" radius={[4, 4, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
}
