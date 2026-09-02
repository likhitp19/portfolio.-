import type { ProjectLensContent } from "@/lib/portfolio/types";

export const APEX_F1_META = {
  title: "Apex F1 Suite",
  subtitle: "Commercial desk · Executive Co-Pilot · Regulatory Protest Engine",
  oneLiner:
    "If you ran a team or a book, what is a point, a driver, and a constructor actually worth — and if you had to protest, what would the dossier look like?",
  role: "AI Product Analyst · Full-stack builder",
  stack: ["Next.js App Router", "FastAPI", "LangGraph", "Pinecone", "OpenF1", "Supabase", "OpenRouter"],
  liveLinks: [
    { label: "Manufacturer ROI", href: "/season/2026?tab=manufacturer" },
    { label: "Driver Assets", href: "/season/2026?tab=driver" },
    { label: "Regulatory Desk", href: "/steward" },
  ],
};

export const APEX_F1_BUSINESS: ProjectLensContent = {
  headline: "Decision velocity for commercial & executive stakeholders",
  intro:
    "Apex Analytics turns scattered sporting feeds and uncited financial rumors into a single season ledger — constructor yield, cited USD, and an Executive Co-Pilot that answers championship questions in seconds, not slide decks.",
  sections: [
    {
      id: "problem",
      title: "Problem",
      body:
        "Public F1 APIs expose points and results — not valuations, retainers, or budget-cap filings. Dashboards that invent dollars on every request destroy executive trust. Live timing answers a different question entirely.",
    },
    {
      id: "desks",
      title: "Three desks, one contract",
      body: "Each desk serves a distinct decision — without forking data models.",
      bullets: [
        "Manufacturer ROI — Financial Telemetry KPIs, constructor book, cost-per-point matrix, era timeline",
        "Driver Assets — Top-5 FER cards, teammate delta scatter, title-chase progression",
        "Executive Co-Pilot — Multi-turn chat for championship projection, constructor finance, and driver ROI",
      ],
    },
    {
      id: "kpis",
      title: "Financial telemetry KPIs",
      body: "Every metric ties to a formula the CFO can audit.",
      metrics: [
        { label: "Cost-per-point (CPP)", value: "cap ÷ constructor pts", hint: "Shared FIA cap unless team-specific cite exists" },
        { label: "FER", value: "salary ÷ driver pts", hint: "Lower = better driver asset ROI" },
        { label: "Market Inefficiency Index", value: "CPP dispersion", hint: "TIGHT · ELEVATED · HIGH bands" },
        { label: "Grid valuation", value: "Σ constructor valuations", hint: "Midfield filled — no blank cells" },
      ],
    },
    {
      id: "copilot",
      title: "Executive Co-Pilot — decision support",
      body:
        "Natural-language questions return an executive TL;DR, predicted winner + confidence, contender cards, and a deep-dive report. Follow-up chips keep the conversation inside the season context. Finance answers carry a public-benchmarks tag — never silent invention.",
      bullets: [
        "Default starter: “Who is projected to win the Championship this year, and what does the data say?”",
        "Year resolves from the query (“this season” → 2026), not only the UI dropdown",
        "Regulation explainers abstain from APIs — knowledge-layer answers only",
      ],
    },
    {
      id: "compliance",
      title: "Regulatory compliance acceleration",
      body:
        "The Regulatory Desk (/steward) simulates how a Team Principal would assemble an FIA Protest — verbatim rule citations, evidence checklist, and success probability — compressing hours of counsel prep into a structured dossier for portfolio review. Output is explicitly labeled simulation, not an official filing.",
    },
    {
      id: "impact",
      title: "Business impact",
      body: "Designed for demo-to-production credibility with sponsors, investors, and internal strategy teams.",
      bullets: [
        "One circuit, one payload — changing GP re-fetches dashboard; no stale widgets",
        "Search once, store forever — completed-year commercial facts are immutable",
        "15-minute dashboard cache + boot preload — cold starts tolerable on Railway",
        "Honest coverage boundaries — pre-2023 telemetry abstains instead of hallucinating",
      ],
    },
  ],
};

export const APEX_F1_TECHNICAL: ProjectLensContent = {
  headline: "LangGraph orchestration, streaming contracts, and hybrid RAG",
  intro:
    "Two compiled graphs share sporting keys (year, meeting_key, session_key) but never share prompts: commercial chat optimizes finance joins and abstention; steward_graph optimizes multimodal context + legal citation integrity.",
  sections: [
    {
      id: "stack",
      title: "Core stack",
      body: "Next.js App Router (Tailwind, shadcn, Recharts) on Vercel. FastAPI + LangGraph on Railway. Browser calls Railway directly via NEXT_PUBLIC_API_URL.",
      bullets: [
        "Dashboard aggregate: GET /api/dashboard — no LLM on page load",
        "Commercial agents: POST /api/chat + POST /api/chat/stream (SSE)",
        "Steward: POST /api/steward/analyze_clip/stream (SSE stages → result)",
      ],
    },
    {
      id: "commercial-graph",
      title: "Commercial LangGraph",
      body: "Generalist → Data Analyst ⇄ tools → Strategic Analyst (championship_projection) → Technical Manager.",
      bullets: [
        "SSE handoff events: generalist, data_analyst, strategic_analyst, technical_manager",
        "Server-owned trace: routing, execution_trace, api_calls, pipelines, assumptions, missing_inputs",
        "Intent routing: driver_roi, constructor_finance, championship_projection, regulatory_knowledge, historical_out_of_coverage, research",
        "Tool catalog: OpenF1 championship + sessions + get_finance_estimates (fact_store://commercial)",
      ],
    },
    {
      id: "steward-graph",
      title: "Regulatory LangGraph (steward_graph)",
      body: "vision_extraction → openf1_context_gather → pinecone_retrieve_rules → verdict_reasoning → ProtestDossier JSON.",
      bullets: [
        "Vision: Qwen2.5-VL via OpenRouter — circuit, lap, driver numbers, spatial narrative",
        "OpenF1: car_data, location, race_control, team_radio — 404 → [], 401 → F1_LIVE_LOCK degrade",
        "Counsel: DeepSeek-R1 — verbatim exact_quote per regulatory_violations; no paraphrase",
        "Evidence checklist: present · pending_phase2 · insufficient (Phase 4 HF ingest contract stubbed)",
      ],
    },
    {
      id: "rag",
      title: "Pinecone hybrid RAG",
      body: "Official FIA Sporting PDFs → PyMuPDF extract → MarkdownHeaderTextSplitter (Article/Chapter boundaries, no fixed char windows) → Pinecone Serverless upsert.",
      bullets: [
        "Metadata: source_document, page_number, article on every chunk",
        "Retrieve: semantic + BM25-light hybrid merge",
        "Offline fallback: teaching Markdown + keyword when PINECONE_API_KEY unset (CI-safe)",
        "153 vectors upserted live on FIA 2026 Sporting corpus",
      ],
    },
    {
      id: "facts",
      title: "Fact store contract",
      body: "Commercial USD lives in SQLite or Supabase (public.commercial_facts). Dashboard GET and get_finance_estimates read only — Tavily runs only on explicit research intent.",
      metrics: [
        { label: "Entity types", value: "regulation · constructor · driver" },
        { label: "Metrics", value: "valuation_usd · budget_cap_usd · salary_usd" },
        { label: "Health", value: "GET /health → facts_backend + facts_count" },
      ],
    },
    {
      id: "streaming",
      title: "SSE streaming architecture",
      body: "Both graphs stream progress to the UI — handoffs for chat, pipeline stages for steward — so latency is visible per node rather than hidden behind a spinner.",
      bullets: [
        "Chat: event:handoff → event:result with full ChatResponse + trace",
        "Steward: event:stage (vision · telemetry · rules · reasoning) → event:result",
        "Fallback: non-stream POST when SSE body unavailable",
      ],
    },
    {
      id: "observability",
      title: "Trace observability",
      body: "The UI never constructs trace objects. AgentTracePanel renders api_calls (tool, path, status, record_count) and execution_trace phases (identify → sources → retrieve → join → calculate → result → gap).",
    },
  ],
};
