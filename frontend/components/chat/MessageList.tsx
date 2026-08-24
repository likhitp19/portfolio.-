import { ScrollArea } from "@/components/ui/scroll-area";
import { CopilotAnswer } from "@/components/chat/CopilotAnswer";
import type { ChatMessage } from "@/lib/types";

export function MessageList({ messages, pending }: { messages: ChatMessage[]; pending?: boolean }) {
  return (
    <ScrollArea className="h-[28rem] pr-1">
      <div className="space-y-3">
        {!messages.length && !pending ? (
          <div className="rounded-sm border border-dashed border-[#2A2A2A] px-4 py-8 text-center">
            <p className="text-[10px] uppercase tracking-[0.22em] text-[#E10600]">Co-Pilot</p>
            <p className="mt-2 text-sm text-muted-foreground">
              Generate an investment thesis. The desk returns an executive summary, a data deep-dive, then the Technical Manager tape.
            </p>
          </div>
        ) : null}
        {messages.map((message, index) => (
          <div
            key={`${message.role}-${index}`}
            className={
              message.role === "user"
                ? "ml-8 rounded-sm bg-primary/15 px-3 py-2 text-sm"
                : "mr-2 rounded-sm border border-[#2A2A2A] bg-[#111] px-3 py-3 text-sm"
            }
          >
            <p className="mb-2 text-[10px] uppercase tracking-[0.18em] text-muted-foreground">
              {message.role === "user" ? "You" : "Executive Co-Pilot"}
            </p>
            {message.role === "assistant" ? (
              <CopilotAnswer content={message.content} layers={message.layers} trace={message.trace} error={message.error} />
            ) : (
              <p className="whitespace-pre-wrap leading-relaxed">{message.content}</p>
            )}
          </div>
        ))}
        {pending ? (
          <p className="text-[11px] uppercase tracking-[0.16em] text-muted-foreground">Graph running…</p>
        ) : null}
      </div>
    </ScrollArea>
  );
}
