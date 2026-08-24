"use client";

import { Collapsible, CollapsibleContent, CollapsibleTrigger } from "@/components/ui/collapsible";
import type { AgentTrace } from "@/lib/types";

function asText(value: unknown): string {
  if (value == null) {
    return "";
  }
  if (typeof value === "string" || typeof value === "number") {
    return String(value);
  }
  return JSON.stringify(value);
}

export function AgentTracePanel({ trace }: { trace?: AgentTrace }) {
  const handoffs = trace?.agent_handoffs?.length
    ? trace.agent_handoffs
    : (trace?.reasoning_path ?? []).map((step) => ({
        agent: asText(step.actor),
        label: `${asText(step.actor)} → ${asText(step.summary)}`,
      }));

  return (
    <Collapsible className="rounded-2xl">
      <CollapsibleTrigger>System Execution & Agent Trace</CollapsibleTrigger>
      <CollapsibleContent className="space-y-5 text-sm">
        {!trace ? (
          <p className="text-muted-foreground">No server trace on this turn.</p>
        ) : (
          <>
            <div>
              <p className="mb-2 text-[10px] uppercase tracking-[0.16em] text-muted-foreground">Agent handoffs</p>
              <ol className="space-y-3">
                {handoffs.map((step, index) => (
                  <li key={`h-${index}`} className="flex gap-3 border-l border-[#E10600]/40 pl-3">
                    <span className="mt-1 h-2 w-2 shrink-0 rounded-full bg-[#E10600]" />
                    <div>
                      <p className="font-medium text-foreground">{asText(step.agent || step.label)}</p>
                      <p className="text-xs text-muted-foreground">{asText(step.label)}</p>
                    </div>
                  </li>
                ))}
              </ol>
            </div>
            <div>
              <p className="mb-2 text-[10px] uppercase tracking-[0.16em] text-muted-foreground">OpenF1 routes</p>
              <ul className="space-y-2 font-mono text-[11px]">
                {(trace.api_calls ?? []).map((call, index) => (
                  <li key={`a-${index}`} className="rounded-lg border border-[#2A2A2A] bg-black/40 px-3 py-2 text-[#10B981]">
                    {asText(call.method)} {asText(call.path)} · HTTP {asText(call.status)}
                    {call.duration_ms != null ? ` · ${asText(call.duration_ms)} ms` : ""} · tool={asText(call.tool)}
                  </li>
                ))}
              </ul>
            </div>
            <div>
              <p className="mb-2 text-[10px] uppercase tracking-[0.16em] text-muted-foreground">Reasoning</p>
              <ol className="space-y-2 font-mono text-[11px] text-muted-foreground">
                {(trace.reasoning_path ?? []).map((step, index) => (
                  <li key={`r-${index}`}>
                    {asText(step.step)}. {asText(step.actor)} — {asText(step.summary)}
                  </li>
                ))}
              </ol>
            </div>
          </>
        )}
      </CollapsibleContent>
    </Collapsible>
  );
}
