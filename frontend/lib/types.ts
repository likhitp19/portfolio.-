export type Meeting = {
  meeting_key: number;
  year: number;
  meeting_name: string;
  circuit_short_name: string;
  country_name: string;
  date_start: string | null;
};

export type FactCitation = {
  status: string;
  source_url: string | null;
  source_title: string | null;
  retrieved_at: string | null;
  value_low: number | null;
  value_high: number | null;
  snippet: string | null;
};

export type DriverStanding = {
  driver_number: number;
  full_name: string;
  team_name: string;
  points: number;
  position: number;
  salary_usd?: number | null;
  financial_efficiency?: number | null;
  salary?: FactCitation | null;
};

export type ConstructorStanding = {
  team_name: string;
  points: number;
  position: number;
  valuation_usd: number | null;
  budget_cap_usd: number | null;
  cost_per_point: number | null;
  wins?: number | null;
  avg_wins?: number | null;
  valuation: FactCitation | null;
  budget_cap: FactCitation | null;
};

export type ChampionshipSummary = {
  leader_name: string | null;
  leader_points: number | null;
  points_gap: number | null;
  race_count: number;
  fastest_lap_driver: string | null;
  fastest_lap_duration: number | null;
  total_dnfs: number;
  top3_finishes: { driver_name: string; count: number }[];
  best_manufacturer?: string | null;
  best_manufacturer_reason?: string | null;
};

export type CircuitLabel = {
  meeting_key: number;
  name: string;
};

export type ProgressionSeries = {
  driver: string;
  points: number[];
};

export type StandingsProgression = {
  circuits: CircuitLabel[];
  series: ProgressionSeries[];
};

export type DashboardPayload = {
  year: number;
  meetingKey?: number;
  years: number[];
  meetings: Meeting[];
  drivers: DriverStanding[];
  constructors: ConstructorStanding[];
  summary: ChampionshipSummary;
  progression: StandingsProgression;
  constructor_progression?: StandingsProgression;
};

export type AgentTrace = {
  routing: Record<string, unknown>;
  reasoning_path: Array<Record<string, unknown>>;
  api_calls: Array<Record<string, unknown>>;
  pipelines: Array<Record<string, unknown>>;
  execution_trace?: Array<Record<string, unknown>>;
  missing_inputs?: string[];
  assumptions?: string[];
  finance_cards?: Array<{ formula?: string; phase?: string }>;
};

export type ChatRequest = {
  message: string;
  thread_id?: string;
  year?: number;
  meeting_key?: number;
};

export type ChatResponse = {
  thread_id: string;
  answer: string;
  trace: AgentTrace;
};

export type ChatMessage = {
  role: "user" | "assistant";
  content: string;
  trace?: AgentTrace;
  error?: string;
};
