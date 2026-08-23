import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Skeleton } from "@/components/ui/skeleton";
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

export function TraceInspector({ trace, pending }: { trace?: AgentTrace; pending?: boolean }) {
  return (
    <div className="h-full">
      <div className="mb-3 flex items-center justify-between">
        <div>
          <p className="text-[10px] uppercase tracking-[0.22em] text-[color:var(--gold)]">Tape</p>
          <h3 className="font-serif text-xl">Technical Manager</h3>
        </div>
        {trace?.routing?.chosen_node ? (
          <Badge className="border-[color:var(--gold)]/30 bg-transparent text-[color:var(--gold)]">
            {asText(trace.routing.chosen_node)}
          </Badge>
        ) : null}
      </div>
      {pending ? (
        <div className="space-y-2">
          <Skeleton className="h-4 w-40" />
          <Skeleton className="h-24 w-full" />
        </div>
      ) : !trace ? (
        <p className="text-sm text-muted-foreground">No server trace yet. This panel never invents one.</p>
      ) : (
        <ScrollArea className="h-[28rem] pr-1 text-sm">
          <div className="space-y-4">
            <section>
              <h4 className="mb-1 text-[10px] font-semibold uppercase tracking-[0.16em] text-muted-foreground">
                Routing
              </h4>
              <p>intent: {asText(trace.routing.intent)}</p>
              <p>rationale: {asText(trace.routing.rationale)}</p>
            </section>
            <section>
              <h4 className="mb-1 text-[10px] font-semibold uppercase tracking-[0.16em] text-muted-foreground">
                Execution trace
              </h4>
              {!(trace.execution_trace && trace.execution_trace.length) ? (
                <p className="text-muted-foreground">No transformation steps recorded.</p>
              ) : (
                <ol className="space-y-2">
                  {trace.execution_trace.map((step, index) => (
                    <li key={index} className="border-l border-[color:var(--gold)]/30 pl-3">
                      <span className="text-[color:var(--gold)]">{asText(step.phase)}</span>
                      <span className="text-muted-foreground"> — {asText(step.detail)}</span>
                    </li>
                  ))}
                </ol>
              )}
              {trace.missing_inputs && trace.missing_inputs.length ? (
                <p className="mt-2 text-muted-foreground">Missing: {trace.missing_inputs.map(asText).join("; ")}</p>
              ) : null}
              {trace.assumptions && trace.assumptions.length ? (
                <p className="mt-1 text-muted-foreground">Assumptions: {trace.assumptions.map(asText).join("; ")}</p>
              ) : null}
            </section>
            <section>
              <h4 className="mb-1 text-[10px] font-semibold uppercase tracking-[0.16em] text-muted-foreground">
                Reasoning path
              </h4>
              <ol className="space-y-2">
                {trace.reasoning_path.map((step, index) => (
                  <li key={index} className="border-l border-[color:var(--gold)]/30 pl-3">
                    <span className="text-[color:var(--gold)]">{asText(step.actor)}</span>
                    <span className="text-muted-foreground"> — {asText(step.summary)}</span>
                  </li>
                ))}
              </ol>
            </section>
            <section>
              <h4 className="mb-1 text-[10px] font-semibold uppercase tracking-[0.16em] text-muted-foreground">
                API calls
              </h4>
              {!trace.api_calls.length ? (
                <p className="text-muted-foreground">None (no tools on this turn).</p>
              ) : (
                <ul className="space-y-2">
                  {trace.api_calls.map((call, index) => (
                    <li key={index} className="rounded-lg border border-border bg-black/30 p-2 font-mono text-[11px]">
                      <div>
                        {asText(call.method)} {asText(call.path)}
                      </div>
                      <div>
                        tool={asText(call.tool)} status={asText(call.status)}
                      </div>
                      <div>params={asText(call.params)}</div>
                      <div>record_count={asText(call.record_count)}</div>
                      {call.error ? <div className="text-destructive">{asText(call.error)}</div> : null}
                    </li>
                  ))}
                </ul>
              )}
            </section>
            <section>
              <h4 className="mb-1 text-[10px] font-semibold uppercase tracking-[0.16em] text-muted-foreground">
                Pipelines
              </h4>
              <ul className="space-y-1">
                {trace.pipelines.map((pipeline, index) => (
                  <li key={index}>
                    <span className="font-medium text-[color:var(--gold)]">{asText(pipeline.name)}</span>
                    {pipeline.description ? ` — ${asText(pipeline.description)}` : ""}
                  </li>
                ))}
              </ul>
            </section>
          </div>
        </ScrollArea>
      )}
    </div>
  );
}
