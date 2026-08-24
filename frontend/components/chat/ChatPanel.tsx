"use client";

import { FormEvent, useMemo, useState } from "react";

import { InsightChips } from "@/components/chat/InsightChips";
import { MessageList } from "@/components/chat/MessageList";
import { TraceInspector } from "@/components/chat/TraceInspector";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { ChatApiError, sendChat } from "@/lib/api";
import { insightChips, type InsightChip } from "@/lib/chips";
import type { AgentTrace, ChatMessage } from "@/lib/types";

type ChatPanelProps = {
  year: number;
  meetingKey?: number;
};

export function ChatPanel({ year, meetingKey }: ChatPanelProps) {
  const [input, setInput] = useState("");
  const [threadId, setThreadId] = useState<string | undefined>();
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [pending, setPending] = useState(false);
  const chips = useMemo(() => insightChips(year, meetingKey), [year, meetingKey]);
  const latestTrace = useMemo(() => {
    for (let index = messages.length - 1; index >= 0; index -= 1) {
      if (messages[index].trace) {
        return messages[index].trace;
      }
    }
    return undefined;
  }, [messages]);

  async function runPrompt(text: string) {
    const trimmed = text.trim();
    if (!trimmed || pending) {
      return;
    }
    setInput("");
    setMessages((current) => [...current, { role: "user", content: trimmed }]);
    setPending(true);
    try {
      const response = await sendChat({
        message: trimmed,
        thread_id: threadId,
        year,
        meeting_key: meetingKey,
      });
      setThreadId(response.thread_id);
      setMessages((current) => [
        ...current,
        { role: "assistant", content: response.answer, trace: response.trace },
      ]);
    } catch (error) {
      const failed = error instanceof ChatApiError ? error : null;
      const trace = failed?.payload?.trace as AgentTrace | undefined;
      const answer = failed?.payload?.answer;
      setMessages((current) => [
        ...current,
        {
          role: "assistant",
          content: answer || "The graph did not complete.",
          trace,
          error: failed ? `HTTP ${failed.status}` : "Network error",
        },
      ]);
    } finally {
      setPending(false);
    }
  }

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    await runPrompt(input);
  }

  function onChip(chip: InsightChip) {
    void runPrompt(chip.prompt);
  }

  return (
    <section className="overflow-hidden rounded-sm border border-[#2A2A2A] bg-[#1A1A1A]">
      <div className="flex items-end justify-between gap-4 border-b border-[#2A2A2A] px-6 py-5">
        <div>
          <p className="text-[10px] uppercase tracking-[0.28em] text-[#E10600]">Investment thesis</p>
          <h2 className="text-2xl font-bold tracking-tight text-foreground">Generate AI Investment Thesis</h2>
          <p className="mt-1 text-xs text-muted-foreground">
            Season {year}
            {meetingKey != null ? ` · circuit ${meetingKey}` : " · all circuits"}
            {threadId ? ` · thread ${threadId.slice(0, 8)}` : ""}
          </p>
        </div>
        <p className="hidden max-w-xs text-right text-[11px] leading-relaxed text-muted-foreground sm:block">
          Analysts see the answer. Engineers see the Technical Manager tape. Trace is never invented on the client.
        </p>
      </div>
      <div className="grid gap-0 lg:grid-cols-2">
        <div className="space-y-4 border-b border-border p-6 lg:border-b-0 lg:border-r">
          <MessageList messages={messages} pending={pending} />
          <InsightChips chips={chips} disabled={pending} onSelect={onChip} />
          <form className="flex gap-2" onSubmit={onSubmit}>
            <Input
              value={input}
              onChange={(event) => setInput(event.target.value)}
              placeholder="Ask valuation, FER, or look up a figure online…"
              disabled={pending}
              className="h-11 rounded-sm border-[#2A2A2A] bg-[#0A0A0A]"
            />
            <Button type="submit" disabled={pending} className="h-11 px-6">
              Brief
            </Button>
          </form>
        </div>
        <div className="p-6">
          <TraceInspector trace={latestTrace} pending={pending} />
        </div>
      </div>
    </section>
  );
}
