"use client";

import { FormEvent, useMemo, useState } from "react";

import { AgentTracePanel } from "@/components/chat/AgentTracePanel";
import { AnswerChart } from "@/components/chat/AnswerChart";
import { MessageList } from "@/components/chat/MessageList";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { ChatApiError, sendChat, sendChatStream } from "@/lib/api";
import type { AgentTrace, ChatMessage } from "@/lib/types";

export const CHAMPIONSHIP_STARTER =
  "Who is projected to win the Championship this year, and what does the data say?";

const CURRENT_SEASON = 2026;

function yearForPrompt(text: string, pageYear: number) {
  const named = text.match(/\b((?:19|20)\d{2})\b/);
  if (named) {
    return Number(named[1]);
  }
  if (/this year|this season/i.test(text)) {
    return CURRENT_SEASON;
  }
  return pageYear || CURRENT_SEASON;
}

type ChatPanelProps = {
  year?: number;
  meetingKey?: number;
};

export function ChatPanel({ year = CURRENT_SEASON, meetingKey }: ChatPanelProps) {
  const [input, setInput] = useState("");
  const [threadId, setThreadId] = useState<string | undefined>();
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [pending, setPending] = useState(false);
  const [handoff, setHandoff] = useState<string>();

  const latestAssistant = useMemo(() => {
    for (let index = messages.length - 1; index >= 0; index -= 1) {
      if (messages[index].role === "assistant") {
        return messages[index];
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
    setHandoff("🤖 Generalist Orchestrator: Planning query...");
    const request = {
      message: trimmed,
      thread_id: threadId,
      year: yearForPrompt(trimmed, year),
      meeting_key: meetingKey,
    };
    try {
      let response;
      try {
        response = await sendChatStream(request, (label) => setHandoff(label));
      } catch {
        response = await sendChat(request);
      }
      setThreadId(response.thread_id);
      setMessages((current) => [
        ...current,
        { role: "assistant", content: response.answer, layers: response.layers, trace: response.trace },
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
          layers: failed?.payload?.layers,
          trace,
          error: failed ? `HTTP ${failed.status}` : "Network error",
        },
      ]);
    } finally {
      setPending(false);
      setHandoff(undefined);
    }
  }

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    await runPrompt(input);
  }

  const empty = !messages.length && !pending;
  const followUps = latestAssistant?.layers?.follow_ups ?? [];
  const season = year === 2025 ? CURRENT_SEASON : year;

  return (
    <section className="mx-auto flex min-h-[calc(100vh-7rem)] w-full max-w-3xl flex-col">
      <div className="flex flex-1 flex-col">
        {empty ? (
          <div className="flex flex-1 flex-col items-center justify-center px-4">
            <p className="text-[10px] uppercase tracking-[0.28em] text-[#E10600]">Executive Co-Pilot</p>
            <h1 className="mt-3 text-center text-3xl font-semibold tracking-tight">Championship intelligence</h1>
            <p className="mt-2 text-sm text-muted-foreground">Season {season}</p>
            <Button
              type="button"
              variant="outline"
              disabled={pending}
              onClick={() => void runPrompt(CHAMPIONSHIP_STARTER)}
              className="mt-8 h-auto max-w-xl whitespace-normal rounded-2xl border-[#2A2A2A] bg-[#111] px-6 py-4 text-left text-base font-medium leading-relaxed hover:border-[#E10600]/50 hover:bg-[#1A1A1A]"
            >
              {CHAMPIONSHIP_STARTER}
            </Button>
          </div>
        ) : (
          <div className="flex-1 px-1 pb-4">
            <MessageList messages={messages} pending={pending} handoff={handoff} />
            {followUps.length ? (
              <div className="mt-6 space-y-2">
                <p className="text-[10px] font-medium uppercase tracking-[0.16em] text-muted-foreground">
                  Follow-up questions
                </p>
                <div className="flex flex-wrap gap-2">
                  {followUps.map((prompt) => (
                    <Button
                      key={prompt}
                      type="button"
                      variant="outline"
                      disabled={pending}
                      onClick={() => void runPrompt(prompt)}
                      className="h-auto max-w-full whitespace-normal rounded-full border-[#2A2A2A] px-4 py-2 text-left text-xs"
                    >
                      {prompt}
                    </Button>
                  ))}
                </div>
              </div>
            ) : null}
            <div className="mt-6">
              <AgentTracePanel trace={latestAssistant?.trace} />
            </div>
            {latestAssistant ? (
              <div className="mt-4">
                <AnswerChart content={latestAssistant.content} layers={latestAssistant.layers} />
              </div>
            ) : null}
          </div>
        )}
      </div>
      <form
        className="sticky bottom-0 mt-4 flex gap-2 border-t border-[#2A2A2A] bg-background py-4"
        onSubmit={onSubmit}
      >
        <Input
          value={input}
          onChange={(event) => setInput(event.target.value)}
          placeholder="Ask anything about the championship…"
          disabled={pending}
          className="h-12 rounded-full border-[#2A2A2A] bg-[#0A0A0A] px-5"
        />
        <Button type="submit" disabled={pending} className="h-12 rounded-full px-6">
          Send
        </Button>
      </form>
    </section>
  );
}
