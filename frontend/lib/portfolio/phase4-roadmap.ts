import type { RoadmapItem } from "@/lib/portfolio/types";

/** Phase 4 — forward-looking architectural expansion (not framed as gaps) */
export const PHASE4_ROADMAP: RoadmapItem[] = [
  {
    id: "stint-strategy",
    title: "Race-strategy orchestration layer",
    summary:
      "Extend the Data Analyst tool plan with meeting-scoped stint windows: top-N finishers → compound ranges → lap aggregates → pace comparison.",
    unlocks: [
      "Eval catalog Test 5 (Bahrain stint strategy) moves from intent-only to full orchestration",
      "Sponsor-facing “strategy alpha” narratives grounded in stint math",
    ],
    status: "in-design",
  },
  {
    id: "teammate-h2h",
    title: "Teammate head-to-head qualifying & race aggregation",
    summary:
      "Normalize qualifying and race results per meeting, compute mean quali delta and finish-ratio metrics across a season pair.",
    unlocks: [
      "Eval catalog Test 4 (Leclerc vs Sainz) completes the transformation pipeline",
      "Driver Assets desk gains chat parity with the teammate delta scatter",
    ],
    status: "planned",
  },
  {
    id: "position-gain",
    title: "Grid-to-finish position gain ranker",
    summary:
      "Join starting grid to race classification per GP; rank net positions gained with explicit formula in execution_trace.",
    unlocks: ["Eval catalog Test 6 (Monza grid gains)", "One-GP decision retrospectives for team principals"],
    status: "planned",
  },
  {
    id: "hf-telemetry",
    title: "High-frequency telemetry ingest (10–100 Hz)",
    summary:
      "Implement POST /api/steward/phase2/telemetry to flip dossier evidence from pending_phase2 to present — steering, brake, and apex-window proof.",
    unlocks: [
      "Article 13 Protest success probability rises when micro-telemetry sustains apex claims",
      "Contract already stubbed; channels schema defined on ProtestDossier",
    ],
    status: "contract-ready",
  },
];
