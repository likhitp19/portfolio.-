"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

import { ProtestDossierPanel } from "@/components/steward/ProtestDossierPanel";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import {
  analyzeStewardClip,
  analyzeStewardClipStream,
  analyzeStewardUpload,
  normalizeProtestDossier,
  type LiveFeedContext,
  type ProtestDossier,
  type StewardAnalyzeResponse,
  type StewardPipelineStage,
} from "@/lib/steward";

const DEMO_CLIP = "/testf1incident1.mp4";
const DEMO_HINT =
  "Car 63 on the outside of Car 44 at Turn 5 on lap 1 — alleged understeer / failure to leave racing room.";

const REASONING_PHRASES = [
  "Analyzing OpenF1 telemetry gaps...",
  "Cross-referencing FIA Appendix L...",
  "Applying DeepSeek R1 logical reasoning...",
  "Drafting formal protest claims...",
] as const;

const STAGES: {
  id: StewardPipelineStage;
  pending: string;
  done: string;
}[] = [
  { id: "vision", pending: "⏳ Analyzing Video (Qwen-VL)", done: "✅ Analyzing Video (Qwen-VL)" },
  { id: "telemetry", pending: "⏳ Fetching Telemetry & Radio (OpenF1)", done: "✅ Fetching Telemetry & Radio (OpenF1)" },
  { id: "rules", pending: "⏳ Querying Sporting Regulations (Pinecone)", done: "✅ Querying Sporting Regulations (Pinecone)" },
  { id: "reasoning", pending: "⏳ Synthesizing Protest Dossier (DeepSeek)", done: "✅ Synthesizing Protest Dossier (DeepSeek)" },
];

function formatElapsed(totalSeconds: number): string {
  const mins = Math.floor(totalSeconds / 60);
  const secs = totalSeconds % 60;
  return `${String(mins).padStart(2, "0")}:${String(secs).padStart(2, "0")}s elapsed`;
}

export default function StewardPage() {
  const inputRef = useRef<HTMLInputElement>(null);
  const [file, setFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState("");
  const [clipUrl, setClipUrl] = useState("");
  const [year, setYear] = useState("2024");
  const [circuit, setCircuit] = useState("Spa");
  const [hint, setHint] = useState(DEMO_HINT);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [active, setActive] = useState<StewardPipelineStage[]>([]);
  const [result, setResult] = useState<StewardAnalyzeResponse | null>(null);
  const [dragOver, setDragOver] = useState(false);
  const [reasoningElapsed, setReasoningElapsed] = useState(0);
  const [phraseIndex, setPhraseIndex] = useState(0);

  const onFile = useCallback(
    (next: File | null) => {
      if (next && next.type && !next.type.startsWith("video/") && !next.type.startsWith("image/")) {
        setError("Please drop an MP4 (or other video) clip.");
        return;
      }
      setFile(next);
      setResult(null);
      setActive([]);
      setError("");
      if (previewUrl.startsWith("blob:")) URL.revokeObjectURL(previewUrl);
      setPreviewUrl(next ? URL.createObjectURL(next) : "");
    },
    [previewUrl],
  );

  const playerSrc = previewUrl || clipUrl;
  const dossier: ProtestDossier | null = normalizeProtestDossier(result?.protest_dossier);

  const reasoningActive = useMemo(() => {
    if (!busy) return false;
    const done = (id: StewardPipelineStage) =>
      active.includes(id) || (result?.pipeline || []).some((item) => item.stage === id);
    return done("rules") && !done("reasoning");
  }, [busy, active, result]);

  useEffect(() => {
    if (!reasoningActive) {
      setReasoningElapsed(0);
      setPhraseIndex(0);
      return;
    }
    setReasoningElapsed(0);
    setPhraseIndex(0);
    const tick = window.setInterval(() => setReasoningElapsed((value) => value + 1), 1000);
    const cycle = window.setInterval(
      () => setPhraseIndex((value) => (value + 1) % REASONING_PHRASES.length),
      4000,
    );
    return () => {
      window.clearInterval(tick);
      window.clearInterval(cycle);
    };
  }, [reasoningActive]);

  function markStage(stage: StewardPipelineStage) {
    setActive((current) => (current.includes(stage) ? current : [...current, stage]));
  }

  async function analyze(options?: {
    file?: File | null;
    clipUrl?: string;
    year?: string;
    circuit?: string;
    hint?: string;
  }) {
    const nextFile = options && "file" in options ? options.file ?? null : file;
    const nextClip = options?.clipUrl ?? clipUrl;
    const nextYear = options?.year ?? year;
    const nextCircuit = options?.circuit ?? circuit;
    const nextHint = options?.hint ?? hint;

    setBusy(true);
    setError("");
    setResult(null);
    setActive([]);
    const yearNum = Number(nextYear) || undefined;
    const liveFeed: LiveFeedContext = {
      session_type: "Race",
      lap_number: 1,
      involved_driver_numbers: [63, 44],
      timing_note: nextHint,
    };
    try {
      if (nextFile) {
        markStage("vision");
        const uploadPromise = analyzeStewardUpload({
          file: nextFile,
          year: yearNum,
          circuit: nextCircuit || undefined,
          incidentHint: nextHint,
          clipUrl: nextClip || undefined,
          liveFeed,
          filingTeam: "Mercedes-AMG Petronas Formula One Team",
          filingType: "protest",
        });
        const tick = window.setTimeout(() => markStage("telemetry"), 700);
        const tick2 = window.setTimeout(() => markStage("rules"), 1600);
        const payload = await uploadPromise;
        window.clearTimeout(tick);
        window.clearTimeout(tick2);
        setActive((payload.pipeline || []).map((item) => item.stage));
        markStage("reasoning");
        setResult(payload);
        return;
      }
      const payload = await analyzeStewardClipStream(
        {
          clip_url: nextClip || undefined,
          year: yearNum,
          circuit: nextCircuit || undefined,
          incident_hint: nextHint,
          live_feed: liveFeed,
          filing_team: "Mercedes-AMG Petronas Formula One Team",
          filing_type: "protest",
        },
        (stage) => markStage(stage.stage),
      );
      setActive((payload.pipeline || []).map((item) => item.stage));
      setResult(payload);
    } catch (caught) {
      try {
        markStage("vision");
        const fallback = await analyzeStewardClip({
          clip_url: nextClip || undefined,
          year: yearNum,
          circuit: nextCircuit || undefined,
          incident_hint: nextHint,
          live_feed: liveFeed,
          filing_team: "Mercedes-AMG Petronas Formula One Team",
          filing_type: "protest",
        });
        setActive((fallback.pipeline || []).map((item) => item.stage));
        setResult(fallback);
      } catch (second) {
        setError(second instanceof Error ? second.message : caught instanceof Error ? caught.message : "Analyze failed");
      }
    } finally {
      setBusy(false);
    }
  }

  async function runSpaDemo() {
    setError("");
    try {
      const response = await fetch(DEMO_CLIP);
      if (!response.ok) throw new Error("Demo clip not found in /public");
      const blob = await response.blob();
      const demoFile = new File([blob], "testf1incident1.mp4", { type: blob.type || "video/mp4" });
      if (previewUrl.startsWith("blob:")) URL.revokeObjectURL(previewUrl);
      const objectUrl = URL.createObjectURL(demoFile);
      setFile(demoFile);
      setPreviewUrl(objectUrl);
      setClipUrl(DEMO_CLIP);
      setYear("2024");
      setCircuit("Spa");
      setHint(DEMO_HINT);
      await analyze({
        file: demoFile,
        clipUrl: DEMO_CLIP,
        year: "2024",
        circuit: "Spa",
        hint: DEMO_HINT,
      });
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Failed to start Spa demo");
    }
  }

  const chartData = useMemo(() => {
    const series = result?.telemetry_series || [];
    const length = Math.max(0, ...series.map((item) => item.samples.length));
    const rows: Record<string, number | string>[] = [];
    for (let index = 0; index < length; index += 1) {
      const row: Record<string, number | string> = { t: index };
      for (const item of series) {
        const sample = item.samples[index];
        if (!sample) continue;
        row[`speed_${item.driver_number}`] = Number(sample.speed ?? 0);
        row[`brake_${item.driver_number}`] = Number(sample.brake ?? 0);
      }
      rows.push(row);
    }
    return rows;
  }, [result]);

  return (
    <div className="min-h-screen bg-[#0A0A0A] text-foreground">
      <main className="mx-auto grid max-w-7xl gap-6 px-6 py-8 lg:grid-cols-2">
        <section className="grid gap-4">
          <Card className="border-[#2A2A2A] bg-[#111111]">
            <CardHeader className="flex flex-row items-center justify-between gap-3">
              <CardTitle className="text-base">Incident intake</CardTitle>
              <Badge className="rounded-sm border-[#C8A24A]/40 bg-transparent text-[10px] uppercase tracking-[0.14em] text-[#C8A24A]">
                Regulatory Desk
              </Badge>
            </CardHeader>
            <CardContent className="grid gap-3">
              <div
                role="button"
                tabIndex={0}
                aria-label="Video dropzone"
                className={`flex min-h-52 cursor-pointer flex-col items-center justify-center rounded-sm border border-dashed px-4 text-center transition-colors ${
                  dragOver ? "border-[#E10600] bg-[#E10600]/10" : "border-[#2A2A2A] bg-[#0A0A0A]"
                }`}
                onClick={() => inputRef.current?.click()}
                onKeyDown={(event) => {
                  if (event.key === "Enter" || event.key === " ") inputRef.current?.click();
                }}
                onDragOver={(event) => {
                  event.preventDefault();
                  setDragOver(true);
                }}
                onDragLeave={() => setDragOver(false)}
                onDrop={(event) => {
                  event.preventDefault();
                  setDragOver(false);
                  const next = event.dataTransfer.files?.[0];
                  if (next) onFile(next);
                }}
              >
                {playerSrc ? (
                  <video className="max-h-72 w-full rounded-sm bg-black" src={playerSrc} controls />
                ) : (
                  <div className="grid gap-2">
                    <p className="text-sm font-medium text-[#F5F5F5]">Drop MP4 broadcast / onboard clip</p>
                    <p className="text-xs text-muted-foreground">
                      Drag &amp; drop, or click to browse. Qwen-VL reads TV graphics and overlays.
                    </p>
                  </div>
                )}
              </div>
              <input
                ref={inputRef}
                type="file"
                accept="video/mp4,video/*,image/*"
                className="hidden"
                onChange={(event) => onFile(event.target.files?.[0] ?? null)}
              />

              <Button
                type="button"
                variant="outline"
                disabled={busy}
                className="w-full border-[#C8A24A]/50 bg-[#C8A24A]/5 text-[#F5F5F5] hover:bg-[#C8A24A]/15 hover:text-white"
                onClick={() => void runSpaDemo()}
              >
                🏎️ Run Spa Incident Demo
              </Button>
              <p className="text-[11px] text-muted-foreground">
                Loads <span className="font-mono text-[#C8A24A]">testf1incident1.mp4</span> with Spa / Lap 1 / cars 44 &amp; 63 and starts the pipeline.
              </p>

              {file ? (
                <p className="truncate text-xs text-muted-foreground">
                  Selected: <span className="text-[#C8A24A]">{file.name}</span>
                </p>
              ) : null}
              <label className="grid gap-1 text-[10px] uppercase tracking-[0.16em] text-muted-foreground">
                Clip URL
                <Input value={clipUrl} onChange={(event) => setClipUrl(event.target.value)} placeholder="https://... or /demo.mp4" />
              </label>
              <div className="grid grid-cols-2 gap-3">
                <label className="grid gap-1 text-[10px] uppercase tracking-[0.16em] text-muted-foreground">
                  Year
                  <Input value={year} onChange={(event) => setYear(event.target.value)} />
                </label>
                <label className="grid gap-1 text-[10px] uppercase tracking-[0.16em] text-muted-foreground">
                  Circuit
                  <Input value={circuit} onChange={(event) => setCircuit(event.target.value)} />
                </label>
              </div>
              <label className="grid gap-1 text-[10px] uppercase tracking-[0.16em] text-muted-foreground">
                Incident / timing note
                <Input value={hint} onChange={(event) => setHint(event.target.value)} />
              </label>
              <Button
                disabled={busy || (!file && !clipUrl && !hint)}
                onClick={() => void analyze()}
              >
                {busy ? "Building protest dossier…" : "File Phase 1 assessment"}
              </Button>
              {error ? <p className="text-sm text-[#E10600]">{error}</p> : null}
            </CardContent>
          </Card>

          <Card className="border-[#2A2A2A] bg-[#111111]">
            <CardHeader>
              <CardTitle className="text-base">Pipeline stepper</CardTitle>
            </CardHeader>
            <CardContent className="grid gap-2">
              {STAGES.map((stage, index) => {
                const done =
                  active.includes(stage.id) || (result?.pipeline || []).some((item) => item.stage === stage.id);
                const current =
                  busy &&
                  !done &&
                  (index === 0 || active.includes(STAGES[index - 1].id) || (result?.pipeline || []).some((item) => item.stage === STAGES[index - 1].id));
                const isReasoningWait = stage.id === "reasoning" && (current || reasoningActive);
                return (
                  <div
                    key={stage.id}
                    className={`rounded-sm border px-3 py-2.5 text-sm transition-colors ${
                      done
                        ? "border-[#10B981]/50 bg-[#10B981]/10"
                        : isReasoningWait
                          ? "border-[#C8A24A] bg-[#C8A24A]/10 shadow-[inset_0_0_0_1px_rgba(200,162,74,0.15)]"
                          : current
                            ? "border-[#C8A24A] bg-[#C8A24A]/10"
                            : "border-[#2A2A2A]"
                    }`}
                  >
                    <div className="flex items-center justify-between gap-3">
                      <span className={done || current || isReasoningWait ? "text-[#F5F5F5]" : "text-muted-foreground"}>
                        {done ? stage.done : current || isReasoningWait ? stage.pending : stage.pending.replace("⏳", "•")}
                      </span>
                      <span className="shrink-0 text-[10px] uppercase tracking-[0.16em] text-muted-foreground">
                        {done ? "done" : isReasoningWait || current ? "running" : "idle"}
                      </span>
                    </div>
                    {isReasoningWait ? (
                      <div className="mt-2 space-y-1 border-t border-[#C8A24A]/20 pt-2">
                        <p className="font-mono text-[11px] text-[#C8A24A]">{formatElapsed(reasoningElapsed)}</p>
                        <p className="text-xs text-muted-foreground transition-opacity duration-500">
                          {REASONING_PHRASES[phraseIndex]}
                        </p>
                        <p className="text-[10px] text-muted-foreground/80">
                          DeepSeek R1 may take 20–40s while it reasons before emitting the dossier.
                        </p>
                      </div>
                    ) : null}
                  </div>
                );
              })}
            </CardContent>
          </Card>

          <Card className="border-[#2A2A2A] bg-[#111111]">
            <CardHeader>
              <CardTitle className="text-base">Coarse OpenF1 traces</CardTitle>
            </CardHeader>
            <CardContent>
              {result?.telemetry_degraded ? (
                <p className="text-sm text-muted-foreground">{result.telemetry_summary}</p>
              ) : chartData.length ? (
                <div className="h-56">
                  <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={chartData}>
                      <XAxis dataKey="t" tick={{ fill: "#A3A3A3", fontSize: 10 }} />
                      <YAxis tick={{ fill: "#A3A3A3", fontSize: 10 }} width={36} />
                      <Tooltip contentStyle={{ background: "#0A0A0A", border: "1px solid #2A2A2A", fontSize: 12 }} />
                      {(result?.telemetry_series || []).map((item, index) => (
                        <Line
                          key={`speed-${item.driver_number}`}
                          type="monotone"
                          dataKey={`speed_${item.driver_number}`}
                          stroke={index === 0 ? "#E10600" : "#C8A24A"}
                          dot={false}
                          name={`#${item.driver_number} speed`}
                        />
                      ))}
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              ) : (
                <p className="text-sm text-muted-foreground">Whole-lap traces appear after telemetry binds.</p>
              )}
            </CardContent>
          </Card>
        </section>

        <section className="grid gap-4 self-start lg:sticky lg:top-24">
          <ProtestDossierPanel dossier={dossier} disclaimer={result?.disclaimer} />
        </section>
      </main>
    </div>
  );
}
