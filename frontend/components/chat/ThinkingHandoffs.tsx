"use client";

import { useEffect, useState } from "react";

const FALLBACK = [
  "🤖 Generalist Orchestrator: Planning query...",
  "📊 Data Analyst Agent: Querying race telemetry...",
  "📈 Strategic Analyst: Evaluating pace, reliability, and margins...",
  "🛠️ Technical Manager: Synthesizing validation trace...",
];

export function ThinkingHandoffs({ label }: { label?: string }) {
  const [index, setIndex] = useState(0);

  useEffect(() => {
    if (label) {
      return;
    }
    const timer = window.setInterval(() => {
      setIndex((current) => (current + 1) % FALLBACK.length);
    }, 1600);
    return () => window.clearInterval(timer);
  }, [label]);

  const text = label || FALLBACK[index];

  return (
    <div className="flex items-center gap-3 rounded-2xl border border-[#2A2A2A] bg-[#111] px-4 py-3">
      <span className="relative flex h-3 w-3">
        <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-[#E10600] opacity-60" />
        <span className="relative inline-flex h-3 w-3 rounded-full bg-[#E10600]" />
      </span>
      <p className="text-sm text-foreground/90">{text}</p>
    </div>
  );
}
