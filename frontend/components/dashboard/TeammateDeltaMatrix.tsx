"use client";

import { useEffect, useMemo, useState } from "react";
import {
  CartesianGrid,
  Cell,
  ReferenceArea,
  ResponsiveContainer,
  Scatter,
  ScatterChart,
  Tooltip,
  XAxis,
  YAxis,
  ZAxis,
} from "recharts";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { fetchTeammateDelta, formatApiError } from "@/lib/api";
import type { TeammateDeltaMatrix, TeammateDeltaRow } from "@/lib/types";

const TEAM_COLORS: Record<string, string> = {
  mclaren: "#FF8000",
  ferrari: "#E10600",
  red_bull: "#3671C6",
  mercedes: "#00D2BE",
  aston_martin: "#229971",
  alpine: "#0093CC",
  williams: "#64C4FF",
  haas: "#B6BABD",
  rb: "#6692FF",
  sauber: "#52E252",
};

export function TeammateDeltaMatrix({ year }: { year: number }) {
  const [data, setData] = useState<TeammateDeltaMatrix>();
  const [error, setError] = useState<string>();

  useEffect(() => {
    let cancelled = false;
    fetchTeammateDelta(year)
      .then((payload) => {
        if (!cancelled) {
          setData(payload);
          setError(undefined);
        }
      })
      .catch((err: unknown) => {
        if (!cancelled) {
          setError(formatApiError(err).message);
        }
      });
    return () => {
      cancelled = true;
    };
  }, [year]);

  const points = useMemo(
    () =>
      (data?.rows ?? []).map((row) => ({
        ...row,
        x: row.dominant_share_pct,
        y: row.quali_pace_delta_ms ?? 0,
        fill: TEAM_COLORS[row.constructor_id] ?? "#A3A3A3",
      })),
    [data],
  );

  const shareRisk = data?.share_risk_pct ?? 62;
  const qualiRisk = data?.quali_risk_ms ?? 200;
  const maxY = Math.max(qualiRisk * 1.4, ...points.map((row) => row.y), 250);

  return (
    <Card className="rounded-sm border-[#2A2A2A] bg-[#1A1A1A] shadow-none">
      <CardHeader className="border-b border-[#2A2A2A]">
        <CardTitle className="text-xl font-bold tracking-tight">Teammate delta · asset reliance</CardTitle>
        <p className="text-xs uppercase tracking-[0.16em] text-muted-foreground">
          Points share % vs average qualifying pace delta · {year}
        </p>
      </CardHeader>
      <CardContent className="space-y-4 p-4">
        {error ? <p className="text-sm text-destructive">{error}</p> : null}
        {!error && !data ? <p className="text-sm text-muted-foreground">Loading teammate matrix…</p> : null}
        {data ? (
          <div className="relative h-[360px]">
            <p className="pointer-events-none absolute left-16 top-4 z-10 text-[10px] uppercase tracking-widest text-[#E10600]/80">
              High Asset Risk
            </p>
            <p className="pointer-events-none absolute bottom-14 left-16 z-10 text-[10px] uppercase tracking-widest text-[#10B981]/80">
              Balanced Portfolio
            </p>
            <ResponsiveContainer width="100%" height="100%">
              <ScatterChart margin={{ top: 16, right: 16, left: 8, bottom: 8 }}>
                <CartesianGrid stroke="#2A2A2A" />
                <ReferenceArea x1={50} x2={shareRisk} y1={0} y2={qualiRisk} fill="rgba(16, 185, 129, 0.10)" fillOpacity={1} />
                <ReferenceArea
                  x1={shareRisk}
                  x2={100}
                  y1={qualiRisk}
                  y2={maxY}
                  fill="rgba(225, 6, 0, 0.12)"
                  fillOpacity={1}
                />
                <XAxis
                  type="number"
                  dataKey="x"
                  name="Points share"
                  domain={[50, 100]}
                  tick={{ fill: "#A3A3A3", fontSize: 11 }}
                  unit="%"
                  label={{ value: "Points Share % (dominant driver)", position: "insideBottom", offset: -2, fill: "#A3A3A3", fontSize: 11 }}
                />
                <YAxis
                  type="number"
                  dataKey="y"
                  name="Quali delta"
                  domain={[0, maxY]}
                  tick={{ fill: "#A3A3A3", fontSize: 11 }}
                  unit="ms"
                  label={{ value: "Avg qualifying pace delta (ms)", angle: -90, position: "insideLeft", fill: "#A3A3A3", fontSize: 10 }}
                />
                <ZAxis range={[80, 80]} />
                <Tooltip
                  cursor={{ stroke: "#2A2A2A" }}
                  content={({ active, payload }) => {
                    if (!active || !payload?.[0]) {
                      return null;
                    }
                    const row = payload[0].payload as TeammateDeltaRow & { x: number; y: number };
                    return (
                      <div className="border border-[#2A2A2A] bg-[#0A0A0A] px-3 py-2 text-xs">
                        <p className="font-semibold">{row.team_name}</p>
                        <p className="text-muted-foreground">
                          {row.driver_a_name} {row.points_a} pts · {row.driver_b_name} {row.points_b} pts
                        </p>
                        <p className="font-mono">
                          Share {row.dominant_share_pct}% · Δ {row.quali_pace_delta_ms ?? "n/a"} ms · {row.sample_races} GPs
                        </p>
                      </div>
                    );
                  }}
                />
                <Scatter data={points} shape="circle">
                  {points.map((row) => (
                    <Cell key={row.constructor_id} fill={row.fill} />
                  ))}
                </Scatter>
              </ScatterChart>
            </ResponsiveContainer>
          </div>
        ) : null}
        <div className="flex flex-wrap gap-4 text-[11px] uppercase tracking-widest text-muted-foreground">
          <span className="inline-flex items-center gap-2">
            <span className="h-2 w-2 bg-[#10B981]/60" /> Balanced Portfolio
          </span>
          <span className="inline-flex items-center gap-2">
            <span className="h-2 w-2 bg-[#E10600]/60" /> High Asset Risk
          </span>
        </div>
        {data?.rows.length ? (
          <ul className="grid gap-2 text-xs sm:grid-cols-2">
            {data.rows.map((row) => (
              <li key={row.constructor_id} className="border border-[#2A2A2A] bg-[#0A0A0A] px-3 py-2">
                <span className="font-medium">{row.team_name}</span>
                <span className="ml-2 font-mono text-muted-foreground">{row.quadrant.replace(/_/g, " ")}</span>
                <p className="mt-1 text-muted-foreground">
                  {row.driver_a_name} vs {row.driver_b_name} · {row.dominant_share_pct}% yield concentration
                </p>
              </li>
            ))}
          </ul>
        ) : null}
      </CardContent>
    </Card>
  );
}
