import { CopilotAnswer } from "@/components/chat/CopilotAnswer";
import { ThinkingHandoffs } from "@/components/chat/ThinkingHandoffs";
import type { ChatMessage } from "@/lib/types";

export function MessageList({
  messages,
  pending,
  handoff,
}: {
  messages: ChatMessage[];
  pending?: boolean;
  handoff?: string;
}) {
  return (
    <div className="space-y-6 pb-2">
      {messages.map((message, index) => (
        <div
          key={`${message.role}-${index}`}
          className={
            message.role === "user"
              ? "ml-auto max-w-[85%] rounded-2xl bg-[#1A1A1A] px-4 py-3 text-sm"
              : "w-full text-sm"
          }
        >
          {message.role === "assistant" ? (
            <CopilotAnswer content={message.content} layers={message.layers} error={message.error} />
          ) : (
            <p className="whitespace-pre-wrap leading-relaxed">{message.content}</p>
          )}
        </div>
      ))}
      {pending ? <ThinkingHandoffs label={handoff} /> : null}
    </div>
  );
}
