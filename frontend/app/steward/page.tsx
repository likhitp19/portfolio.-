"use client";

import { useCallback, useMemo, useRef, useState } from "react";
import Link from "next/link";
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
  type ProtestDossier,
  type StewardAnalyzeResponse,
  type StewardPipelineStage,
} from "@/lib/steward";

const STAGES: { id: StewardPipelineStage; label: string }[] = [
  { id: "vision", label: "Ingest" },
  { id: "telemetry", label: "OpenF1" },
  { id: "rules", label: "ISC RAG" },
  { id: "reasoning", label: "Dossier" },
];

export default function StewardPage() {
  const inputRef = useRef<HTMLInputElement>(null);
  const [file, setFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState("");
  const [clipUrl, setClipUrl] = useState("");
  const [year, setYear] = useState("2026");
  const [circuit, setCircuit] = useState("Spa");
  const [hint, setHint] = useState(
    "Car 63 on the outside of Car 44 at Turn 5 on lap 1 — alleged understeer / failure to leave racing room.",
  );
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [active, setActive] = useState<StewardPipelineStage[]>([]);
  const [result, setResult] = useState<StewardAnalyzeResponse | null>(null);
  const [dragOver, setDragOver] = useState(false);

  const onFile = useCallback(
    (next: File | null) => {
      setFile(next);
      setResult(null);
      setActive([]);
      if (previewUrl.startsWith("blob:")) URL.revokeObjectURL(previewUrl);
      setPreviewUrl(next ? URL.createObjectURL(next) : "");
    },
    [previewUrl],
  );

  const playerSrc = previewUrl || clipUrl;
  const dossier: ProtestDossier | null = result?.protest_dossier ?? null;

  async function analyze() {
    setBusy(true);
    setError("");
    setResult(null);
    setActive([]);
    const yearNum = Number(year) || undefined;
    const liveFeed = {
      session_type: "Race",
      lap_number: 1,
      involved_driver_numbers: [63, 44],
      timing_note: hint,
    };
    try {
      if (file) {
        const payload = await analyzeStewardUpload({
          file,
          year: yearNum,
          circuit: circuit || undefined,
          incidentHint: hint,
          clipUrl: clipUrl || undefined,
          liveFeed,
          filingTeam: "Mercedes-AMG Petronas Formula One Team",
          filingType: "protest",
        });
        setActive((payload.pipeline || []).map((item) => item.stage));
        setResult(payload);
        return;
      }
      const payload = await analyzeStewardClipStream(
        {
          clip_url: clipUrl || undefined,
          year: yearNum,
          circuit: circuit || undefined,
          incident_hint: hint,
          live_feed: liveFeed,
          filing_team: "Mercedes-AMG Petronas Formula One Team",
          filing_type: "protest",
        },
        (stage) => setActive((current) => (current.includes(stage.stage) ? current : [...current, stage.stage])),
      );
      setResult(payload);
    } catch (caught) {
      try {
        const fallback = await analyzeStewardClip({
          clip_url: clipUrl || undefined,
          year: yearNum,
          circuit: circuit || undefined,
          incident_hint: hint,
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
      <header className="sticky top-0 z-50 border-b border-[#2A2A2A] bg-[#121212]/95 backdrop-blur">
        <div className="mx-auto flex h-14 max-w-7xl items-center justify-between px-6">
          <Link href="/season/2026" className="text-lg font-black tracking-tighter text-[#E10600]">
            APEX ANALYTICS
          </Link>
          <Badge className="rounded-sm border-[#C8A24A]/40 bg-transparent text-[10px] uppercase tracking-[0.16em] text-[#C8A24A]">
            Mercedes-AMG · Protest Engine
          </Badge>
        </div>
      </header>
      <main className="mx-auto grid max-w-7xl gap-6 px-6 py-8 lg:grid-cols-2">
        <section className="grid gap-4">
          <Card className="border-[#2A2A2A] bg-[#111111]">
            <CardHeader>
              <CardTitle className="text-base">Incident intake</CardTitle>
            </CardHeader>
            <CardContent className="grid gap-3">
              <div
                className={`flex min-h-48 cursor-pointer flex-col items-center justify-center rounded-sm border border-dashed px-4 text-center ${
                  dragOver ? "border-[#E10600] bg-[#E10600]/10" : "border-[#2A2A2A] bg-[#0A0A0A]"
                }`}
                onClick={() => inputRef.current?.click()}
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
                  <video className="max-h-64 w-full rounded-sm bg-black" src={playerSrc} controls />
                ) : (
                  <p className="text-sm text-muted-foreground">
                    Drop broadcast / onboard clip. Live timing context is attached automatically for the demo.
                  </p>
                )}
              </div>
              <input
                ref={inputRef}
                type="file"
                accept="video/*,image/*"
                className="hidden"
                onChange={(event) => onFile(event.target.files?.[0] ?? null)}
              />
              <label className="grid gap-1 text-[10px] uppercase tracking-[0.16em] text-muted-foreground">
                Clip URL
                <Input value={clipUrl} onChange={(event) => setClipUrl(event.target.value)} placeholder="https://..." />
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
              <Button disabled={busy} onClick={() => void analyze()}>
                {busy ? "Building protest dossier…" : "File Phase 1 assessment"}
              </Button>
              {error ? <p className="text-sm text-[#E10600]">{error}</p> : null}
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
        <section className="grid gap-4">
          <Card className="border-[#2A2A2A] bg-[#111111]">
            <CardHeader>
              <CardTitle className="text-base">Phase 1 pipeline</CardTitle>
            </CardHeader>
            <CardContent className="grid gap-2">
              {STAGES.map((stage, index) => {
                const done = active.includes(stage.id) || (result?.pipeline || []).some((item) => item.stage === stage.id);
                const current = busy && !done && (index === 0 || active.includes(STAGES[index - 1].id));
                return (
                  <div
                    key={stage.id}
                    className={`flex items-center justify-between rounded-sm border px-3 py-2 text-sm ${
                      done ? "border-[#E10600] bg-[#E10600]/10" : current ? "border-[#C8A24A]" : "border-[#2A2A2A]"
                    }`}
                  >
                    <span>{stage.label}</span>
                    <span className="text-[10px] uppercase tracking-[0.16em] text-muted-foreground">
                      {done ? "done" : current ? "running" : "idle"}
                    </span>
                  </div>
                );
              })}
            </CardContent>
          </Card>

          <ProtestDossierPanel dossier={dossier} disclaimer={result?.disclaimer} />
        </section>
      </main>
    </div>
  );
}
