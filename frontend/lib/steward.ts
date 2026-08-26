export type StewardPipelineStage = "vision" | "telemetry" | "rules" | "reasoning";

export type StewardSample = {
  t: number;
  date?: string | null;
  speed?: number | null;
  brake?: number | null;
  throttle?: number | null;
};

export type StewardSeries = {
  driver_number: number;
  samples: StewardSample[];
  location_points?: number;
};

export type StewardVerdict = {
  incident: string;
  rule_cited: string;
  telemetry_facts: string;
  verdict: string;
  penalty: string;
};

export type EvidenceStatus = "present" | "pending_phase2" | "insufficient";
export type SuccessProbability = "Low" | "Medium" | "High";

export type RequiredEvidenceItem = {
  id: string;
  label: string;
  rationale: string;
  status: EvidenceStatus;
  phase2_schema_ref: string;
};

export type RegulatoryCitation = {
  article_name: string;
  exact_quote: string;
  page_number: number;
  source_document: string;
};

export type ProtestDossier = {
  filing_type: "protest" | "right_of_review";
  filing_team: string;
  competitor_team: string;
  primary_claim: string;
  regulatory_violations: RegulatoryCitation[];
  available_evidence_summary: string;
  required_telemetry_evidence: RequiredEvidenceItem[];
  success_probability: SuccessProbability;
  legal_risk_notes: string;
  recommended_next_step: string;
  phase2_bridge: string;
};

/** Coerce legacy string citations into RegulatoryCitation objects for the dossier UI. */
export function normalizeProtestDossier(raw: ProtestDossier | null | undefined): ProtestDossier | null {
  if (!raw) return null;
  const violations = ((raw.regulatory_violations || []) as unknown[]).map((item) => {
    if (typeof item === "string") {
      return {
        article_name: item.slice(0, 120),
        exact_quote: item,
        page_number: 0,
        source_document: "unknown",
      } satisfies RegulatoryCitation;
    }
    const cite = (item || {}) as Partial<RegulatoryCitation>;
    return {
      article_name: cite.article_name || "",
      exact_quote: cite.exact_quote || "",
      page_number: Number(cite.page_number) || 0,
      source_document: cite.source_document || "",
    };
  });
  return { ...raw, regulatory_violations: violations };
}

export type LiveFeedContext = {
  session_type?: string;
  lap_number?: number;
  involved_driver_numbers?: number[];
  timing_note?: string;
};

export type StewardAnalyzeRequest = {
  clip_url?: string;
  year?: number;
  circuit?: string;
  meeting_key?: number;
  session_key?: number;
  incident_hint?: string;
  live_feed?: LiveFeedContext;
  filing_team?: string;
  filing_type?: "protest" | "right_of_review";
};

export type StewardAnalyzeResponse = {
  vision: Record<string, unknown>;
  telemetry_summary: string;
  telemetry_series: StewardSeries[];
  telemetry_degraded: boolean;
  session_key?: number | null;
  retrieved_rules: Array<{ id?: string; title?: string; text?: string; score?: number }>;
  verdict: StewardVerdict;
  protest_dossier: ProtestDossier;
  pipeline: Array<{ stage: StewardPipelineStage; status: string; detail?: string }>;
  assumptions: string[];
  errors: string[];
  disclaimer: string;
};

const DEFAULT_API_BASE = "http://127.0.0.1:8000";

function apiBase(): string {
  const base =
    typeof window === "undefined"
      ? process.env.API_INTERNAL_URL ?? process.env.NEXT_PUBLIC_API_URL ?? DEFAULT_API_BASE
      : process.env.NEXT_PUBLIC_API_URL ?? DEFAULT_API_BASE;
  return base.replace(/\/$/, "");
}

export async function analyzeStewardClip(body: StewardAnalyzeRequest): Promise<StewardAnalyzeResponse> {
  const response = await fetch(`${apiBase()}/api/steward/analyze_clip`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
    signal: AbortSignal.timeout(180000),
  });
  if (!response.ok) {
    throw new Error(await response.text());
  }
  return response.json() as Promise<StewardAnalyzeResponse>;
}

export async function analyzeStewardUpload(input: {
  file: File;
  year?: number;
  circuit?: string;
  incidentHint?: string;
  clipUrl?: string;
  liveFeed?: LiveFeedContext;
  filingTeam?: string;
  filingType?: "protest" | "right_of_review";
}): Promise<StewardAnalyzeResponse> {
  const form = new FormData();
  form.append("file", input.file);
  if (input.year) form.append("year", String(input.year));
  if (input.circuit) form.append("circuit", input.circuit);
  if (input.incidentHint) form.append("incident_hint", input.incidentHint);
  if (input.clipUrl) form.append("clip_url", input.clipUrl);
  if (input.liveFeed) form.append("live_feed_json", JSON.stringify(input.liveFeed));
  if (input.filingTeam) form.append("filing_team", input.filingTeam);
  if (input.filingType) form.append("filing_type", input.filingType);
  const response = await fetch(`${apiBase()}/api/steward/analyze_clip/upload`, {
    method: "POST",
    body: form,
    signal: AbortSignal.timeout(180000),
  });
  if (!response.ok) {
    throw new Error(await response.text());
  }
  return response.json() as Promise<StewardAnalyzeResponse>;
}

export async function analyzeStewardClipStream(
  body: StewardAnalyzeRequest,
  onStage: (stage: StewardAnalyzeResponse["pipeline"][number]) => void,
): Promise<StewardAnalyzeResponse> {
  const response = await fetch(`${apiBase()}/api/steward/analyze_clip/stream`, {
    method: "POST",
    headers: { "Content-Type": "application/json", Accept: "text/event-stream" },
    body: JSON.stringify(body),
    signal: AbortSignal.timeout(180000),
  });
  if (!response.ok || !response.body) {
    return analyzeStewardClip(body);
  }
  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  let result: StewardAnalyzeResponse | null = null;
  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    const chunks = buffer.split("\n\n");
    buffer = chunks.pop() ?? "";
    for (const chunk of chunks) {
      const eventLine = chunk.split("\n").find((line) => line.startsWith("event:"));
      const dataLine = chunk.split("\n").find((line) => line.startsWith("data:"));
      if (!dataLine) continue;
      const event = eventLine?.slice(6).trim();
      const data = JSON.parse(dataLine.slice(5).trim());
      if (event === "stage") onStage(data);
      if (event === "result") result = data as StewardAnalyzeResponse;
    }
  }
  if (!result) return analyzeStewardClip(body);
  return result;
}
