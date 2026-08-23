import { ScrollArea } from "@/components/ui/scroll-area";
import type { AgentTrace, ChatMessage } from "@/lib/types";

function highlight(text: string) {
  const parts = text.split(/(\bFormula:.*?(?=\s{2,}|$)|https?:\/\/\S+|\/v1\/\S+|fact_store:\/\/\S+|search:\/\/\S+)/g);
  return parts.map((part, index) => {
    const isFormula = part.startsWith("Formula:");
    const isEndpoint = /^(https?:\/\/|\/v1\/|fact_store:\/\/|search:\/\/)/.test(part);
    if (isFormula || isEndpoint) {
      return (
        <code
          key={`${part}-${index}`}
          className={
            isFormula
              ? "rounded bg-[color:var(--gold)]/15 px-1 font-mono text-[11px] text-[color:var(--gold)]"
              : "rounded bg-emerald-500/10 px-1 font-mono text-[11px] text-emerald-300"
          }
        >
          {part}
        </code>
      );
    }
    return <span key={`${part}-${index}`}>{part}</span>;
  });
}

function asText(value: unknown): string {
  if (value == null) {
    return "";
  }
  if (typeof value === "string" || typeof value === "number") {
    return String(value);
  }
  return JSON.stringify(value);
}

function InlineTrace({ trace }: { trace: AgentTrace }) {
  return (
    <details className="mt-3 rounded-lg border border-[color:var(--gold)]/20 bg-black/40 p-2">
      <summary className="cursor-pointer text-[10px] uppercase tracking-[0.18em] text-[color:var(--gold)]">
        Technical Manager trace
      </summary>
      <div className="mt-2 space-y-2 text-[11px] leading-relaxed">
        <p>
          {asText(trace.routing?.intent)} → {asText(trace.routing?.chosen_node ?? trace.routing?.chosen_node)}
        </p>
        {(trace.execution_trace ?? []).map((step, index) => (
          <p key={index} className="font-mono text-muted-foreground">
            {highlight(`${asText(step.phase ?? step.phase)} — ${asText(step.detail ?? step.detail)}`)}
          </p>
        ))}
        {trace.api_calls.map((call, index) => (
          <p key={`api-${index}`} className="font-mono text-emerald-300/90">
            {highlight(`${asText(call.method)} ${asText(call.path)} tool=${asText(call.tool)}`)}
          </p>
        ))}
        {(trace.finance_cards ?? []).map((card, index) => (
          <p key={`fer-${index}`}>{highlight(`Formula: ${card.formula ?? ""}`)}</p>
        ))}
      </div>
    </details>
  );
}

export function MessageList({ messages, pending }: { messages: ChatMessage[]; pending?: boolean }) {
  return (
    <ScrollArea className="h-72 pr-1">
      <div className="space-y-3">
        {!messages.length && !pending ? (
          <div className="rounded-xl border border-dashed border-[color:var(--gold)]/25 px-4 py-8 text-center">
            <p className="text-[10px] uppercase tracking-[0.22em] text-[color:var(--gold)]">Briefing</p>
            <p className="mt-2 text-sm text-muted-foreground">
              Ask like a commercial director: efficiency, retainers, or a cited look-up. Context follows the season and circuit above.
            </p>
          </div>
        ) : null}
        {messages.map((message, index) => (
          <div
            key={`${message.role}-${index}`}
            className={
              message.role === "user"
                ? "ml-8 rounded-xl bg-primary/15 px-3 py-2 text-sm"
                : "mr-4 rounded-xl border border-[color:var(--gold)]/15 bg-black/25 px-3 py-2 text-sm"
            }
          >
            <p className="mb-1 text-[10px] uppercase tracking-[0.18em] text-[color:var(--gold)]">
              {message.role === "user" ? "You" : "Desk"}
            </p>
            <p className="whitespace-pre-wrap leading-relaxed">{message.content}</p>
            {message.role === "assistant" && message.trace ? <InlineTrace trace={message.trace} /> : null}
            {message.error ? <p className="mt-2 text-xs text-destructive">{message.error}</p> : null}
          </div>
        ))}
        {pending ? (
          <p className="text-[11px] uppercase tracking-[0.16em] text-muted-foreground">Graph running…</p>
        ) : null}
      </div>
    </ScrollArea>
  );
}
