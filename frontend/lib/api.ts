import type {
  ChampionshipSummary,
  ChatRequest,
  ChatResponse,
  ConstructorStanding,
  ConstructorTimeline,
  DashboardPayload,
  DriverStanding,
  Meeting,
  StandingsProgression,
  TeammateDeltaMatrix,
} from "@/lib/types";

export class ApiError extends Error {
  status: number;
  code?: string;

  constructor(status: number, message: string, code?: string) {
    super(message);
    this.status = status;
    this.code = code;
  }
}

export const F1_LIVE_LOCK = "F1_LIVE_LOCK";

export function formatApiError(error: unknown): { code?: string; message: string } {
  if (error instanceof ApiError) {
    return { code: error.code, message: error.message };
  }
  if (error instanceof Error) {
    return { message: error.message };
  }
  return { message: "Dashboard data is unavailable." };
}

const DEFAULT_API_BASE = "http://127.0.0.1:8000";

function apiBase(): string {
  const base =
    typeof window === "undefined"
      ? process.env.API_INTERNAL_URL ?? process.env.NEXT_PUBLIC_API_URL ?? DEFAULT_API_BASE
      : process.env.NEXT_PUBLIC_API_URL ?? DEFAULT_API_BASE;
  return base.replace(/\/$/, "");
}

function parseApiError(status: number, raw: string): ApiError {
  try {
    const json = JSON.parse(raw) as { detail?: unknown };
    const detail = json.detail;
    if (detail && typeof detail === "object" && "message" in detail) {
      const body = detail as { code?: string; message: string };
      return new ApiError(status, body.message, body.code);
    }
    if (typeof detail === "string") {
      const live = /live f1 session/i.test(detail);
      return new ApiError(status, detail, live ? F1_LIVE_LOCK : undefined);
    }
  } catch {
    /* not JSON */
  }
  if (/live f1 session/i.test(raw)) {
    return new ApiError(status, raw, F1_LIVE_LOCK);
  }
  return new ApiError(status, raw || `Request failed (${status})`);
}

async function getJson<T>(path: string, timeoutMs = 90000): Promise<T> {
  const response = await fetch(`${apiBase()}${path}`, {
    cache: "no-store",
    signal: AbortSignal.timeout(timeoutMs),
  });
  if (!response.ok) {
    throw parseApiError(response.status, await response.text());
  }
  return response.json() as Promise<T>;
}

export function fetchSeasons() {
  return getJson<{ years: number[] }>("/api/seasons");
}

export function fetchMeetings(year: number) {
  return getJson<Meeting[]>(`/api/meetings?year=${year}`);
}

export function fetchDrivers(year: number, meetingKey?: number) {
  const q = meetingKey ? `&meeting_key=${meetingKey}` : "";
  return getJson<DriverStanding[]>(`/api/championship/drivers?year=${year}${q}`);
}

export function fetchConstructors(year: number, meetingKey?: number) {
  const q = meetingKey ? `&meeting_key=${meetingKey}` : "";
  return getJson<ConstructorStanding[]>(`/api/championship/constructors?year=${year}${q}`);
}

export function fetchSummary(year: number, meetingKey?: number) {
  const q = meetingKey ? `&meeting_key=${meetingKey}` : "";
  return getJson<ChampionshipSummary>(`/api/championship/summary?year=${year}${q}`);
}

export function fetchProgression(year: number) {
  return getJson<StandingsProgression>(`/api/standings/progression?year=${year}`);
}

export function fetchConstructorTimeline(fromYear = 2014) {
  return getJson<ConstructorTimeline>(`/api/analytics/constructor-timeline?from_year=${fromYear}`, 120000);
}

export function fetchTeammateDelta(year: number) {
  return getJson<TeammateDeltaMatrix>(`/api/analytics/teammate-delta?year=${year}`, 120000);
}

export async function loadDashboard(year: number, meetingKey?: number): Promise<DashboardPayload> {
  const q = meetingKey ? `&meeting_key=${meetingKey}` : "";
  const overview = await getJson<{
    year: number;
    meeting_key?: number | null;
    years: number[];
    meetings: Meeting[];
    drivers: DriverStanding[];
    constructors: ConstructorStanding[];
    summary: ChampionshipSummary;
    progression: StandingsProgression;
    constructor_progression?: StandingsProgression;
  }>(`/api/dashboard?year=${year}${q}`);
  return {
    year: overview.year,
    meetingKey: overview.meeting_key ?? meetingKey,
    years: overview.years,
    meetings: overview.meetings,
    drivers: overview.drivers,
    constructors: overview.constructors,
    summary: overview.summary,
    progression: overview.progression,
    constructor_progression: overview.constructor_progression,
  };
}

export class ChatApiError extends Error {
  status: number;
  payload: Partial<ChatResponse> | null;

  constructor(status: number, message: string, payload: Partial<ChatResponse> | null) {
    super(message);
    this.status = status;
    this.payload = payload;
  }
}

export async function sendChat(body: ChatRequest): Promise<ChatResponse> {
  const payload: ChatRequest = {
    message: body.message,
    year: body.year,
  };
  if (body.thread_id) {
    payload.thread_id = body.thread_id;
  }
  if (body.meeting_key != null) {
    payload.meeting_key = body.meeting_key;
  }
  const response = await fetch(`${apiBase()}/api/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
    signal: AbortSignal.timeout(180000),
  });
  const json = (await response.json().catch(() => null)) as ChatResponse | null;
  if (!response.ok) {
    throw new ChatApiError(response.status, "Chat request failed", json);
  }
  if (!json || !json.trace) {
    throw new ChatApiError(response.status, "Chat response missing trace", json);
  }
  return json;
}

export async function sendChatStream(
  body: ChatRequest,
  onHandoff: (label: string) => void,
): Promise<ChatResponse> {
  const payload: ChatRequest = {
    message: body.message,
    year: body.year,
  };
  if (body.thread_id) {
    payload.thread_id = body.thread_id;
  }
  if (body.meeting_key != null) {
    payload.meeting_key = body.meeting_key;
  }
  const response = await fetch(`${apiBase()}/api/chat/stream`, {
    method: "POST",
    headers: { "Content-Type": "application/json", Accept: "text/event-stream" },
    body: JSON.stringify(payload),
    signal: AbortSignal.timeout(180000),
  });
  if (!response.ok || !response.body) {
    return sendChat(body);
  }
  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  let result: ChatResponse | null = null;
  while (true) {
    const { done, value } = await reader.read();
    if (done) {
      break;
    }
    buffer += decoder.decode(value, { stream: true });
    const chunks = buffer.split("\n\n");
    buffer = chunks.pop() ?? "";
    for (const chunk of chunks) {
      const eventLine = chunk.split("\n").find((line) => line.startsWith("event:"));
      const dataLine = chunk.split("\n").find((line) => line.startsWith("data:"));
      if (!dataLine) {
        continue;
      }
      const event = eventLine?.slice(6).trim();
      const data = JSON.parse(dataLine.slice(5).trim()) as { label?: string } & ChatResponse;
      if (event === "handoff" && data.label) {
        onHandoff(data.label);
      }
      if (event === "result" && data.trace) {
        result = data;
      }
    }
  }
  if (!result) {
    return sendChat(body);
  }
  return result;
}

export function fetchChatThread(threadId: string) {
  return getJson<ChatResponse>(`/api/chat/${threadId}`);
}
