import { ScrollArea } from "@/components/ui/scroll-area";
import type { ChatMessage } from "@/lib/types";

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
