"use client";

import { ContenderCards } from "@/components/chat/ContenderCards";
import { Alert } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { splitCopilotLayers } from "@/lib/copilotLayers";
import type { ChatLayers } from "@/lib/types";

function DeepDiveBody({ text }: { text: string }) {
  const blocks = text.split(/\n{2,}/).filter(Boolean);
  return (
    <div className="space-y-4 text-sm leading-relaxed">
      {blocks.map((block, index) => {
        const lines = block.split("\n").map((line) => line.trim());
        if (lines[0]?.startsWith("## ")) {
          return (
            <h3 key={index} className="pt-2 text-xs font-semibold uppercase tracking-[0.16em] text-[#E10600]">
              {lines[0].replace(/^##\s*/, "")}
            </h3>
          );
        }
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
    <div className="overflow-hidden rounded-lg border border-[#2A2A2A]">
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
  error,
}: {
  content: string;
  layers?: ChatLayers;
  error?: string;
}) {
  const parsed = splitCopilotLayers(content, layers?.executive_summary);
  const deepDive = layers?.deep_dive || parsed.deepDive;
  const winner = layers?.predicted_winner;
  const confidence = layers?.confidence;
  const drivers = layers?.key_drivers ?? [];

  return (
    <div className="space-y-5">
      <Alert className="rounded-2xl border-[#10B981]/35 bg-[#10B981]/10 text-foreground">
        <div className="mb-3 flex flex-wrap items-center gap-2">
          <Badge className="rounded-sm border-[#10B981]/40 bg-transparent font-mono text-[10px] uppercase tracking-widest text-[#10B981]">
            Executive TL;DR
          </Badge>
          {winner ? <p className="text-lg font-semibold tracking-tight">{winner}</p> : null}
          {confidence != null ? (
            <span className="rounded-full border border-[#10B981]/30 px-2 py-0.5 font-mono text-[11px] text-[#10B981]">
              {Math.round(confidence * 100)}% win probability
            </span>
          ) : null}
        </div>
        <p className="text-sm leading-relaxed text-foreground">{parsed.summary}</p>
        {drivers.length ? (
          <ol className="mt-3 space-y-1.5 text-sm text-foreground/90">
            {drivers.slice(0, 2).map((item) => (
              <li key={item} className="flex gap-2">
                <span className="mt-1 h-1.5 w-1.5 shrink-0 rounded-full bg-[#10B981]" />
                <span>{item}</span>
              </li>
            ))}
          </ol>
        ) : null}
      </Alert>

      <ContenderCards contenders={layers?.contenders ?? []} />

      <div className="rounded-2xl border border-[#2A2A2A] bg-[#0A0A0A] p-4">
        <p className="mb-3 text-[10px] font-medium uppercase tracking-[0.16em] text-muted-foreground">
          In-Depth Research Report
        </p>
        <DeepDiveBody text={deepDive} />
      </div>
      {error ? <p className="text-xs text-destructive">{error}</p> : null}
    </div>
  );
}
