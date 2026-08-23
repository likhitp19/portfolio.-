# Agent evaluation — Paddock Ledger

This document is the evaluation contract for `POST /api/chat`. It is **not** a live-timing scorecard. The question is whether a Technical Manager can audit **routing, orchestration, transformation, and answer quality** from the server trace alone.

Related: [ARCHITECTURE.md](./ARCHITECTURE.md) §5, [IMPLEMENTATION_PLAN.md](./IMPLEMENTATION_PLAN.md) Phase 6, machine catalog [`eval/catalog.json`](./eval/catalog.json).

---

## 1. What we are not scoring

We do **not** treat “an API call happened” as success.

A passing run must show the chain:

**user question → intent / routing → execution plan → tools → joins / filters / normalizations → calculations → result → spoken answer**

The Technical Manager emits that chain as `trace.execution_trace` (operational steps). `trace.reasoning_path` remains the **node tape** (who ran: generalist, analyst, tools). Hidden model chain-of-thought is out of scope.

Commercial dollars are **cited fact-store estimates** (or explicit defaults), never audited club accounts and never invented by the LLM.

---

## 2. Four scoring dimensions

Score each test **A–D independently** (0–3). Do not average away a routing failure just because the prose sounds confident.

| Score | Meaning |
| --- | --- |
| **0 Poor** | Wrong source, hallucinated numbers, or no evidence of the required transformation |
| **1 Acceptable** | Right direction; missing a join, a citation, or an explicit gap |
| **2 Good** | Required sequence and math visible; minor extra calls or incomplete prose |
| **3 Excellent** | Minimal necessary calls; auditable steps; assumptions labeled |

### A. Routing

Did the graph pick the right **agent** and **source**?

| Check | Fail if |
| --- | --- |
| Correct node (`generalist_direct` / `data_analyst` / `researcher`) | OpenF1 used for a regulation explainer |
| Correct year from the **query** (not only the dashboard dropdown) | 1998 telemetry answered from 2024 context |
| Store vs search | Live Tavily on a cost-per-point question when the store already has rows |
| Coverage boundary | OpenF1 retries for pre-2023 telemetry |

### B. Orchestration

Did it run the **required sequence**, not a bag of endpoints?

Example (Test 5): meeting → race classification → top 3 → stints → laps in stint windows → aggregate → compare.

A trace that only lists `get_laps` with no top-3 filter **fails orchestration** even if the HTTP status is 200.

### C. Reasoning / transformation (primary gap vs older traces)

`execution_trace` steps must be inspectable. Each step has `phase` + `detail`:

| Phase | What the evaluator looks for |
| --- | --- |
| `identify` | Entities, season, meeting, metric definition |
| `sources` | Which tools/stores were judged necessary — and which were skipped |
| `retrieve` | What came back (counts, year actually used) |
| `join` | Join keys, match count, **why** a join failed |
| `transform` | Filters (midfield, named teams, race-only) |
| `calculate` | Formula with units (USD / point, positions gained) |
| `result` | Ranked outcome tied to those numbers |
| `gap` | Missing input, coverage, or unimplemented pipeline |

Forbidden as the only content: “Retrieved data / processed data / generated answer.”

### D. Answer quality

- Answers the **asked** question (ROI rank, McLaren vs Ferrari, midfield upside, qualifying delta, etc.).
- Arithmetic matches tool payloads.
- Distinguishes **OpenF1/Jolpica sporting facts** from **mock/benchmark retainers**.
- If a calculation cannot be completed, names **which input is missing**.

---

## 3. State cleanliness (API call efficiency)

Separate 0–3 score on `trace.api_calls`.

**Question:** did `api_calls` contain only calls necessary for this question?

| Score | Pattern |
| --- | --- |
| **0** | Irrelevant OpenF1 (laps/stints/race_control) on a regulation or FER question; retry storms |
| **1** | Mostly relevant; extra calendar/session listing that was not used |
| **2** | Necessary set plus one cheap lookup |
| **3** | Optimal: Test 7 and Test 8 have **empty** `api_calls` |

Also flag: **wrong endpoint**, **missed endpoint** (needed join never attempted), **redundant identical calls**.

---

## 4. Trace schema (server-owned)

`AgentTrace`:

| Field | Role |
| --- | --- |
| `routing` | `intent`, `chosen_node`, `rationale` |
| `execution_trace` | Auditable phases (this spec) |
| `reasoning_path` | Actor tape for debugging the graph |
| `api_calls` | Tool, path, params, status, `record_count`, error |
| `pipelines` | Named joins (e.g. `finance_fact_store`, `driver_fer_join`) |
| `missing_inputs` | Strings the synthesizer could not satisfy |
| `assumptions` | e.g. nearest-year salary proxy, $135M cap default |

The chat UI must **never invent** this object.

---

## 5. Test catalog

Canonical queries live in [`eval/catalog.json`](./eval/catalog.json). Summary below.

OpenF1 public coverage is treated as **2023+ completed sessions**. Jolpica can supply older **results**, not 1998 car telemetry.

Fact-store salaries/valuations in-repo are **seeded mainly for 2024**. For a 2023 commercial question the agent may **read the nearest stored year** only if `execution_trace` and the answer say so (benchmark proxy, not 2023 payroll).

### Test 1 — Driver salary vs ROI

**Query:** Which driver delivered the highest financial ROI in the 2023 season based on estimated salary versus championship points scored?

| | Expected |
| --- | --- |
| Route | `data_analyst` |
| Intent | `driver_roi` |
| Tools | `get_championship_drivers` + `get_finance_estimates` |
| Forbidden | `search_commercial`, `get_laps`, `get_race_control` |
| Metric | FER = `salary_usd / championship_points` (lower = better ROI). Also valid: points per dollar if labeled. |
| Join | Salary `entity_key` (driver number) ↔ championship `driver_number` |

**Required trace:** retrieve salaries; retrieve points; match N drivers; rank; name the leader with USD/point.

**Join failure:** list salary keys vs driver numbers and the likely cause (year mismatch, preview truncation, name vs number keys). Never stop at “could not be joined.”

**Capability now:** implemented, with nearest-year fact fallback labeled as estimate.

### Test 2 — Constructor budget efficiency

**Query:** Compare the capital efficiency and cost-per-point between McLaren and Ferrari under the cost cap in 2023.

| | Expected |
| --- | --- |
| Route | `data_analyst` |
| Intent | `constructor_finance` |
| Tools | `get_championship_teams` + `get_finance_estimates` |
| Metric | `budget_cap_usd / constructor_points` (shared FIA cap unless a team-specific cited cap exists) |
| Compare | McLaren vs Ferrari only in the **result**, after a full constructor retrieve if needed |

**Capability now:** implemented (named-team filter in synthesis).

### Test 3 — Sponsor / value pitch (open-ended)

**Query:** If an investor wanted to back the most cost-efficient midfield team from 2023 for future upside, who would the data suggest and why?

| | Expected |
| --- | --- |
| Route | `data_analyst` |
| Intent | `constructor_finance` (midfield is a **transform**, not a new store) |
| Define midfield | Explicit: e.g. constructors ranked 5–10 by points, or everyone except the top-3 points scorers |
| Answer | Recommendation + efficiency numbers + **qualitative upside** labeled as inference |

**Capability now:** partial — ranks by cost-per-point among a midfield slice; upside language is templated, not a second research pass.

### Test 4 — Teammate head-to-head

**Query:** Compare Charles Leclerc and Carlos Sainz across the 2023 season. What was their qualifying delta and race finish ratio?

| | Expected orchestration |
| --- | --- |
| Identify both drivers | |
| Qualifying results per GP | session type Qualifying |
| Race results per GP | session type Race |
| Normalize by meeting | |
| Qualifying delta | e.g. mean(Leclerc quali pos − Sainz quali pos) |
| Race finish ratio | define in trace (wins in H2H, or mean finish delta) |

**Capability now:** **not implemented.** Intent `teammate_h2h` is recognized. The analyst must **not** dump season-wide laps. The answer and `gap` step must state that qualifying/race H2H aggregation is not in the tool plan yet.

### Test 5 — Race-specific strategy

**Query:** At the 2023 Bahrain Grand Prix, how did the tyre compound strategies of the top 3 finishers impact their final stint pace?

| | Expected orchestration |
| --- | --- |
| Meeting ID | 2023 Bahrain |
| Top 3 | race `session_result` |
| Stints | compounds + lap ranges |
| Laps | only those drivers, in final stint windows |
| Compare | pace vs compound vs stint length |

**Capability now:** **not implemented** (no `get_stints` in the catalog; laps are not pulled for this intent). Must resolve the meeting if cheap, then `gap`.

### Test 6 — Position change / overtake flow

**Query:** Who gained the most net positions from their starting grid spot across the 2023 Monza Grand Prix?

**Formula:** `positions_gained = starting_position − finishing_position` (higher is more places gained).

**Capability now:** **not implemented** as a ranked grid join (`get_position` exists on the client but is not in the analyst plan). Intent `position_gain` → `gap` without lap dumps.

### Test 7 — Generalist vs Data Analyst (when **not** to call APIs)

**Query:** Explain how the F1 budget cap regulations work and how penalties are enforced.

| | Expected |
| --- | --- |
| Route | `generalist_direct` |
| Intent | `regulatory_knowledge` |
| `api_calls` | **[]** |
| Content | FIA financial regulations: cap, reporting, sporting/financial penalties — knowledge layer, not OpenF1 |

This scores **orchestration of abstention**. Calling `get_laps` or even `get_championship_teams` is a **0** on cleanliness.

**Capability now:** implemented (heuristic before “budget cap” finance routing).

### Test 8 — Historical coverage boundary

**Query:** Show me the fastest lap telemetry from the 1998 Monaco Grand Prix.

| | Expected |
| --- | --- |
| Route | `generalist_direct` |
| Intent | `historical_out_of_coverage` |
| `api_calls` | **[]** — no retries |
| Answer | OpenF1 does not cover 1998 telemetry; do not hallucinate lap times |

**Capability now:** implemented.

---

## 6. How to run a review

1. Send each catalog `query` to `POST /api/chat` with `year` from the query (do not rely on the UI year for Tests 7–8).
2. Fill the scorecard in §7 using **only** `answer` + `trace`.
3. Pytest: `backend/tests/test_eval_catalog.py` asserts routing and cleanliness for implemented cases; it does **not** claim Tests 4–6 compute the sporting metrics.

---

## 7. Scorecard template (copy per test)

```text
Test #:
A Routing:            /3   notes:
B Orchestration:      /3   notes:
C Transformation:     /3   notes:
D Answer quality:     /3   notes:
API cleanliness:      /3   extra/wrong/missed calls:
execution_trace OK?   yes/no
```

Feedback to give when the tape is still API-shaped:

> The output does not show that the agent understood the task. It reports retrieval, not the join, the formula, or the missing input. Require an execution_trace with identify → sources → retrieve → join/transform → calculate → result → gaps. Score api_calls for unnecessary, redundant, wrong, and missed endpoints.

---

## 8. Current vs target (honest)

| Test | Routing | Transformation in product | Notes |
| --- | --- | --- | --- |
| 1 Driver FER | yes | yes | Seed finance is 2024-heavy; 2023 uses nearest year + assumption |
| 2 Constructor CPP | yes | yes | Shared cap / constructor points |
| 3 Midfield pitch | yes | partial | Efficiency rank yes; investor “upside” is labeled inference |
| 4 Quali / race H2H | intent only | no | Gap in trace |
| 5 Stint / pace | intent only | no | Gap; no stint tool |
| 6 Grid gains | intent only | no | Gap |
| 7 Regulations | yes | n/a | Zero tools |
| 8 1998 telemetry | yes | n/a | Zero tools |

---

## 9. Formulae (must match dashboard)

| Metric | Formula | Source split |
| --- | --- | --- |
| Cost-per-point | `budget_cap_usd / constructor_points` | Cap = store; points = OpenF1/Jolpica |
| FER | `salary_usd / driver_points` | Salary = store estimate; points = championship |
| Positions gained | `grid − finish` | Not implemented in chat yet |

Division by zero → do not rank; say points were 0.

---

## 10. Changelog

| Date | Change |
| --- | --- |
| 2026-08-23 | First eval contract: eight tests, four dimensions, cleanliness rubric, execution_trace, capability matrix |
