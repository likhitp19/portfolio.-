"use client";

import { Bar, BarChart, CartesianGrid, Cell, ReferenceLine, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { formatUsd } from "@/lib/formatMoney";
import { constructorCode, cppBand, cppBandColor } from "@/lib/manufacturerMetrics";
import type { ConstructorStanding } from "@/lib/types";

export function CostPerPointChart({ rows }: { rows: ConstructorStanding[] }) {
  const withCpp = rows.filter((row) => row.cost_per_point != null && row.points > 0);
  const avg =
    withCpp.length > 0
      ? withCpp.reduce((sum, row) => sum + (row.cost_per_point as number), 0) / withCpp.length
      : 0;
  const data = withCpp.map((row) => {
    const cpp = row.cost_per_point as number;
    const band = cppBand(cpp, avg);
    const colors = cppBandColor(band);
    return {
      team: constructorCode(row.team_name),
      fullName: row.team_name,
      cpp,
      points: row.points,
      cap: row.budget_cap_usd,
      band,
      fill: colors.fill,
      stroke: colors.stroke,
    };
  });
  if (!data.length) {
    return null;
  }
  return (
    <Card className="flex min-h-[420px] flex-col border-[#2A2A2A] bg-[#1A1A1A] shadow-none">
      <CardHeader className="flex flex-row items-start justify-between gap-4 border-b border-[#2A2A2A] p-6">
        <div>
          <CardTitle className="text-xl font-bold tracking-tight">Cost Per Point (CPP) Efficiency Matrix</CardTitle>
          <p className="mt-1 text-xs uppercase tracking-[0.16em] text-muted-foreground">
            Constructors · estimated cap / constructor yield
          </p>
        </div>
        <div className="flex gap-2">
          <span className="rounded-sm bg-[#2A2A2A] px-3 py-1 text-[10px] font-medium uppercase tracking-[0.16em] text-foreground">
            YTD
          </span>
          <span className="rounded-sm border border-[#2A2A2A] px-3 py-1 text-[10px] font-medium uppercase tracking-[0.16em] text-muted-foreground">
            LTM
          </span>
          <span className="rounded-sm border border-[#2A2A2A] px-3 py-1 text-[10px] font-medium uppercase tracking-[0.16em] text-muted-foreground">
            PROJ
          </span>
        </div>
      </CardHeader>
      <CardContent className="h-[320px] flex-1 p-6 pt-4">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data} margin={{ top: 12, right: 48, left: 8, bottom: 8 }}>
            <CartesianGrid stroke="#2A2A2A" strokeDasharray="0" vertical={false} />
            <XAxis
              dataKey="team"
              tick={{ fill: "#F5F5F5", fontSize: 11, fontWeight: 700 }}
              axisLine={{ stroke: "#2A2A2A" }}
              tickLine={false}
            />
            <YAxis
              tick={{ fill: "#A3A3A3", fontSize: 11, fontFamily: "var(--font-jetbrains), ui-monospace, monospace" }}
              tickFormatter={(value) => formatUsd(Number(value))}
              axisLine={false}
              tickLine={false}
              width={56}
            />
            <Tooltip
              cursor={{ fill: "rgba(255,255,255,0.03)" }}
              contentStyle={{
                background: "#0A0A0A",
                border: "1px solid #2A2A2A",
                borderRadius: 2,
                fontFamily: "var(--font-jetbrains), ui-monospace, monospace",
              }}
              formatter={(value, _name, item) => {
                const row = item?.payload as { points?: number; fullName?: string } | undefined;
                return [formatUsd(Number(value), false), `${row?.fullName ?? ""} · ${row?.points ?? "—"} pts`];
              }}
            />
            {avg > 0 ? (
              <ReferenceLine
                y={avg}
                stroke="#A3A3A3"
                strokeDasharray="4 4"
                label={{
                  value: `AVG ${formatUsd(avg)}`,
                  fill: "#A3A3A3",
                  fontSize: 10,
                  position: "right",
                  fontFamily: "var(--font-jetbrains), ui-monospace, monospace",
                }}
              />
            ) : null}
            <Bar dataKey="cpp" radius={0} maxBarSize={40}>
              {data.map((entry) => (
                <Cell key={entry.team} fill={entry.fill} stroke={entry.stroke} strokeWidth={1} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
}
