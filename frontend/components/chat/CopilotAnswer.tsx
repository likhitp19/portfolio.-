"use client";

import { Bar, BarChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

import { Collapsible, CollapsibleContent, CollapsibleTrigger } from "@/components/ui/collapsible";
import { Alert } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { numericSeriesFromTables, splitCopilotLayers } from "@/lib/copilotLayers";
import type { AgentTrace, ChatLayers } from "@/lib/types";

function asText(value: unknown): string {
  if (value == null) {
    return "";
  }
  if (typeof value === "string" || typeof value === "number") {
    return String(value);
  }
  return JSON.stringify(value);
}

function DeepDiveBody({ text }: { text: string }) {
  const blocks = text.split(/\n{2,}/).filter(Boolean);
  return (
    <div className="space-y-3 text-sm leading-relaxed">
      {blocks.map((block, index) => {
        const lines = block.split("\n").map((line) => line.trim());
        const isTable = lines.length >= 3 && lines.every((line) => line.startsWith("|"));
        if (isTable) {
          return <MarkdownTableBlock key={index} block={block} />;
        }
        return (
          <p key={index} className="whitespace-pre-wrap text-foreground/90">
            {block}
          </p>
        );
      })}
    </div>
  );
}

function MarkdownTableBlock({ block }: { block: string }) {
  const lines = block
    .split("\n")
    .map((line) => line.trim())
    .filter((line) => line.startsWith("|"));
  const parsed = lines.map((line) =>
    line
      .replace(/^\|/, "")
      .replace(/\|$/, "")
      .split("|")
      .map((cell) => cell.trim()),
  );
  const [headers, , ...rows] = parsed;
  if (!headers?.length || !rows.length) {
    return <p className="whitespace-pre-wrap">{block}</p>;
  }
  return (
    <div className="overflow-hidden rounded-sm border border-[#2A2A2A]">
      <Table>
        <TableHeader>
          <TableRow className="hover:bg-transparent">
            {headers.map((header) => (
              <TableHead key={header} className="font-mono text-[10px] uppercase tracking-widest">
                {header}
              </TableHead>
            ))}
          </TableRow>
        </TableHeader>
        <TableBody>
          {rows.map((row, rowIndex) => (
            <TableRow key={rowIndex} className="hover:bg-white/[0.03]">
              {headers.map((_, cellIndex) => (
                <TableCell key={cellIndex} className="font-mono text-xs">
                  {row[cellIndex] ?? ""}
                </TableCell>
              ))}
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  );
}

export function CopilotAnswer({
  content,
  layers,
  trace,
  error,
}: {
  content: string;
  layers?: ChatLayers;
  trace?: AgentTrace;
  error?: string;
}) {
  const parsed = splitCopilotLayers(content, layers?.executive_summary);
  const deepDive = layers?.deep_dive || parsed.deepDive;
  const series = numericSeriesFromTables(parsed.tables);
  return (
    <div className="space-y-3">
      <Alert className="rounded-sm border-[#10B981]/30 bg-[#10B981]/8 text-foreground">
        <div className="mb-2 flex items-center gap-2">
          <Badge className="rounded-sm border-[#10B981]/40 bg-transparent font-mono text-[10px] uppercase tracking-widest text-[#10B981]">
            Executive Summary
          </Badge>
        </div>
        <p className="text-sm leading-relaxed text-foreground">{parsed.summary}</p>
      </Alert>

      <div className="rounded-sm border border-[#2A2A2A] bg-[#0A0A0A] p-3">
        <p className="mb-3 text-[10px] font-medium uppercase tracking-[0.16em] text-muted-foreground">Data Deep-Dive</p>
        <DeepDiveBody text={deepDive} />
        {series.length >= 2 ? (
          <div className="mt-4 h-36">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={series} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
                <XAxis dataKey="label" tick={{ fill: "#A3A3A3", fontSize: 10 }} axisLine={{ stroke: "#2A2A2A" }} />
                <YAxis tick={{ fill: "#A3A3A3", fontSize: 10 }} axisLine={false} tickLine={false} width={48} />
                <Tooltip
                  contentStyle={{ background: "#0A0A0A", border: "1px solid #2A2A2A", borderRadius: 2, fontSize: 12 }}
                />
                <Bar dataKey="value" fill="#E10600" radius={0} maxBarSize={28} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        ) : null}
      </div>

      <Collapsible>
        <CollapsibleTrigger>Technical Trace · reasoning_path + api_calls</CollapsibleTrigger>
        <CollapsibleContent className="space-y-3 font-mono text-[11px] text-muted-foreground">
          {!trace ? (
            <p>No server trace on this turn.</p>
          ) : (
            <>
              <p>
                {asText(trace.routing?.intent)} → {asText(trace.routing?.chosen_node)}
              </p>
              {(trace.reasoning_path ?? []).map((step, index) => (
                <p key={`r-${index}`}>
                  {asText(step.actor)} — {asText(step.summary)}
                </p>
              ))}
              {trace.api_calls.map((call, index) => (
                <p key={`a-${index}`} className="text-[#10B981]">
                  {asText(call.method)} {asText(call.path)} tool={asText(call.tool)} status={asText(call.status)}
                </p>
              ))}
              {(trace.execution_trace ?? []).slice(0, 8).map((step, index) => (
                <p key={`e-${index}`}>
                  {asText(step.phase)} — {asText(step.detail)}
                </p>
              ))}
            </>
          )}
        </CollapsibleContent>
      </Collapsible>
      {error ? <p className="text-xs text-destructive">{error}</p> : null}
    </div>
  );
}
