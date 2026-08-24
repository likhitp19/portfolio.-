"use client";

import { Bar, BarChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

import { numericSeriesFromTables, splitCopilotLayers } from "@/lib/copilotLayers";
import type { ChatLayers } from "@/lib/types";

export function AnswerChart({ content, layers }: { content: string; layers?: ChatLayers }) {
  const parsed = splitCopilotLayers(content, layers?.executive_summary);
  const series = numericSeriesFromTables(parsed.tables);
  if (series.length < 2) {
    return null;
  }
  return (
    <div className="rounded-2xl border border-[#2A2A2A] bg-[#0A0A0A] p-4">
      <p className="mb-3 text-[10px] font-medium uppercase tracking-[0.16em] text-muted-foreground">
        Contender yield
      </p>
      <div className="h-48">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={series} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
            <XAxis dataKey="label" tick={{ fill: "#A3A3A3", fontSize: 10 }} axisLine={{ stroke: "#2A2A2A" }} />
            <YAxis tick={{ fill: "#A3A3A3", fontSize: 10 }} axisLine={false} tickLine={false} width={48} />
            <Tooltip
              contentStyle={{ background: "#0A0A0A", border: "1px solid #2A2A2A", borderRadius: 8, fontSize: 12 }}
            />
            <Bar dataKey="value" fill="#E10600" radius={0} maxBarSize={28} />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
