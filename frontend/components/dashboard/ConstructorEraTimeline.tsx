"use client";

import { useEffect, useMemo, useState } from "react";
import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ReferenceArea,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { fetchConstructorTimeline, formatApiError } from "@/lib/api";
import { eraForYear, REGULATORY_ERAS, whatChanged } from "@/lib/regulatoryEras";
import type { ConstructorTimeline } from "@/lib/types";

const LINE_COLORS: Record<string, string> = {
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

type ChartRow = { year: number; [team: string]: number | null };

export function ConstructorEraTimeline() {
  const [data, setData] = useState<ConstructorTimeline>();
  const [error, setError] = useState<string>();
  const [selectedYear, setSelectedYear] = useState<number>();

  useEffect(() => {
    let cancelled = false;
    fetchConstructorTimeline(2014)
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
  }, []);

  const rows = useMemo(() => {
    if (!data) {
      return [];
    }
    return data.years.map((year, index) => {
      const row: ChartRow = { year };
      for (const series of data.series) {
        row[series.display_name] = series.points[index];
      }
      return row;
    });
  }, [data]);

  const briefing = selectedYear != null ? whatChanged(selectedYear) : null;

  return (
    <div className="grid gap-4 xl:grid-cols-[minmax(0,1fr)_280px]">
      <Card className="rounded-sm border-[#2A2A2A] bg-[#1A1A1A] shadow-none">
        <CardHeader className="border-b border-[#2A2A2A]">
          <CardTitle className="text-xl font-bold tracking-tight">Constructor yield · regulatory eras</CardTitle>
          <p className="text-xs uppercase tracking-[0.16em] text-muted-foreground">
            2014–present · click a year for the rule change
          </p>
        </CardHeader>
        <CardContent className="h-[380px] p-4">
          {error ? <p className="text-sm text-destructive">{error}</p> : null}
          {!error && !data ? <p className="text-sm text-muted-foreground">Loading constructor history…</p> : null}
          {data ? (
            <ResponsiveContainer width="100%" height="100%">
              <LineChart
                data={rows}
                onClick={(state) => {
                  const year = Number(state?.activeLabel);
                  if (Number.isFinite(year)) {
                    setSelectedYear(year);
                  }
                }}
              >
                <CartesianGrid stroke="#2A2A2A" vertical={false} />
                {REGULATORY_ERAS.map((era) => (
                  <ReferenceArea
                    key={era.id}
                    x1={era.startYear}
                    x2={Math.min(era.endYear, data.to_year)}
                    fill={era.fill}
                    ifOverflow="extendDomain"
                  />
                ))}
                <XAxis
                  type="number"
                  dataKey="year"
                  domain={[data.from_year, data.to_year]}
                  tick={{ fill: "#A3A3A3", fontSize: 11 }}
                  axisLine={{ stroke: "#2A2A2A" }}
                  allowDecimals={false}
                />
                <YAxis
                  tick={{ fill: "#A3A3A3", fontSize: 11 }}
                  axisLine={false}
                  tickLine={false}
                  width={40}
                  label={{ value: "Constructor yield", angle: -90, position: "insideLeft", fill: "#A3A3A3", fontSize: 10 }}
                />
                <Tooltip
                  contentStyle={{ background: "#0A0A0A", border: "1px solid #2A2A2A", borderRadius: 2 }}
                  formatter={(value, name) => [value == null ? "—" : `${value} pts`, String(name)]}
                />
                <Legend wrapperStyle={{ fontSize: 11 }} />
                {data.series.map((series) => (
                  <Line
                    key={series.constructor_id}
                    type="monotone"
                    dataKey={series.display_name}
                    stroke={LINE_COLORS[series.constructor_id] ?? "#A3A3A3"}
                    strokeWidth={2}
                    dot={{ r: 3 }}
                    connectNulls={false}
                  />
                ))}
              </LineChart>
            </ResponsiveContainer>
          ) : null}
        </CardContent>
      </Card>
      <Card className="rounded-sm border-[#2A2A2A] bg-[#1A1A1A] shadow-none">
        <CardContent className="p-5">
          <p className="text-[10px] font-medium uppercase tracking-[0.2em] text-[#E10600]">What changed?</p>
          {briefing ? (
            <>
              <h3 className="mt-2 text-lg font-semibold tracking-tight">{selectedYear} · {briefing.era.label}</h3>
              <p className="mt-3 text-sm leading-relaxed text-muted-foreground">{briefing.note}</p>
            </>
          ) : (
            <>
              <h3 className="mt-2 text-lg font-semibold tracking-tight">Regulatory overlay</h3>
              <ul className="mt-3 space-y-2 text-sm text-muted-foreground">
                {REGULATORY_ERAS.map((era) => (
                  <li key={era.id}>
                    <span className="font-medium text-foreground">{era.label}</span> · {era.startYear}–{era.endYear}
                  </li>
                ))}
              </ul>
              <p className="mt-4 text-xs text-muted-foreground">Click a year on the chart for the diagnostic.</p>
            </>
          )}
          {selectedYear != null ? (
            <p className="mt-4 font-mono text-[10px] uppercase tracking-widest text-muted-foreground">
              Era {eraForYear(selectedYear).id.replace("_", " ")}
            </p>
          ) : null}
        </CardContent>
      </Card>
    </div>
  );
}
