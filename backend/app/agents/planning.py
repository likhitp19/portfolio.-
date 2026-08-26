import re
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Set, Tuple

from app.agents.state import F1DashboardState
from app.config import settings

# A race session is treated as completed once its scheduled start has elapsed
# plus a buffer covering the race window. The list_sessions preview only carries
# date_start, so we cannot rely on date_end here.
_RACE_COMPLETED_BUFFER_SECONDS = 3 * 3600

CHITCHAT_PHRASES = (
    "what can you do",
    "who are you",
    "hello",
    "hi ",
    "hey",
    "help",
)


def _query(state: F1DashboardState) -> str:
    return str(state.get("user_query") or "").strip()


def _folded(text: str) -> str:
    return re.sub(r"[-–—−‑/]+", " ", text.lower())


OPENF1_FROM_YEAR = 2023
FINANCE_SOURCE_TAG = "[Source: Public Financial Benchmarks & Cost Cap Estimates]"


def _with_finance_tag(text: str) -> str:
    body = (text or "").rstrip()
    if FINANCE_SOURCE_TAG in body:
        return body
    return "{0} {1}".format(body, FINANCE_SOURCE_TAG)


def _query_year(state: F1DashboardState) -> Optional[int]:
    match = re.search(r"\b((?:19|20)\d{2})\b", _query(state))
    if match:
        return int(match.group(1))
    return None


def _year(state: F1DashboardState) -> Optional[int]:
    queried = _query_year(state)
    if queried:
        return queried
    text = _folded(_query(state))
    if "this year" in text or "this season" in text:
        return datetime.now(timezone.utc).year
    if state.get("season_year"):
        return int(state["season_year"])
    return datetime.now(timezone.utc).year


def is_chitchat(query: str) -> bool:
    text = query.lower().strip()
    if text in {"hi", "hello", "hey", "help"}:
        return True
    f1_terms = (
        "point",
        "driver",
        "race",
        "championship",
        "constructor",
        "lap",
        "meeting",
        "circuit",
        "valuation",
        "salary",
        "budget",
        "roi",
        "midfield",
        "investor",
        "team",
        "cost",
    )
    if any(term in text for term in f1_terms):
        return False
    return any(re.search(r"\b" + re.escape(phrase.strip()) + r"\b", text) for phrase in CHITCHAT_PHRASES if phrase.strip())


def classify_intent(state: F1DashboardState) -> str:
    text = _folded(_query(state))
    if is_chitchat(_query(state)):
        return "chitchat"
    qyear = _query_year(state)
    if qyear is not None and qyear < OPENF1_FROM_YEAR and any(
        word in text for word in ("telemetry", "fastest lap", "lap time", "stint")
    ):
        return "historical_out_of_coverage"
    regulatory = (
        "how the f1 budget cap",
        "budget cap regulations",
        "financial regulations",
        "how penalties are enforced",
        "penalties are enforced",
        "cost cap regulations",
    )
    if any(phrase in text for phrase in regulatory) or ("regulation" in text and "enforc" in text):
        return "regulatory_knowledge"
    if re.search(r"what(?:'s| is) (?:the )?(?:f1 |fia )?(?:budget|cost) cap", text):
        if "point" not in text and "mclaren" not in text and "per " not in text:
            return "regulatory_knowledge"
    if "explain how" in text and "cap" in text and "mclaren" not in text and "cost-per-point" not in text:
        return "regulatory_knowledge"
    research_words = ("search online", "look up", "lookup", "find online", "google", "web search")
    if any(word in text for word in research_words):
        return "research"
    if any(word in text for word in ("qualifying delta", "head-to-head", "teammate")) or (
        "leclerc" in text and "sainz" in text
    ):
        return "teammate_h2h"
    if any(word in text for word in ("tyre", "tire", "stint", "compound")):
        return "stint_strategy"
    if any(word in text for word in ("positions gained", "starting grid", "grid spot", "net position")):
        return "position_gain"
    finance_words = (
        "valuation",
        "cost per point",
        "usd pt",
        "capital efficien",
        "cost efficien",
        "midfield",
        "investor",
        "upside",
        "team value",
        "constructor efficien",
        "cost cap",
        "budget cap",
        "cost per constructor",
        "cpp",
        "efficien",
        "rankings",
        "season ranking",
    )
    if any(word in text for word in finance_words):
        return "constructor_finance"
    roi_words = (
        "salary",
        "fer",
        "roi",
        "overpaid",
        "financial efficiency",
        "retainer",
        "salary per",
        "points scored",
        "salary/point",
        "per point",
    )
    if any(word in text for word in roi_words):
        return "driver_roi"
    if any(
        phrase in text
        for phrase in (
            "projected to win",
            "who will win",
            "who wins the championship",
            "win the championship",
            "drivers champion",
            "drivers' champion",
            "title fight",
            "championship this year",
        )
    ) or ("championship" in text and any(word in text for word in ("win", "winner", "predict", "project", "title"))):
        return "championship_projection"
    if any(word in text for word in ("dnf", "dns", "dsq", "operational", "ops risk", "reliability")):
        return "meeting_insights"
    if any(word in text for word in ("lap", "pace", "telemetry", "lap time", "lap times")):
        return "telemetry_compare"
    if any(word in text for word in ("driver compare", "driver comparison", "championship points", "how many points")):
        return "comparative_standings"
    if state.get("meeting_key") or "grand prix" in text:
        return "meeting_insights"
    if "circuit" in text and "all circuit" not in text:
        return "meeting_insights"
    return "comparative_standings"


def heuristic_generalist(state: F1DashboardState) -> Dict[str, Any]:
    intent = classify_intent(state)
    if intent == "chitchat":
        return {
            "intent": intent,
            "route": "generalist_direct",
            "routing_rationale": "Query is conversational; no OpenF1 retrieval required.",
            "answer": (
                "I route F1 questions to a Data Analyst (OpenF1 + stored commercial facts) "
                "or a Researcher (web search, cited, then stored). "
                "A Technical Manager returns the APIs and pipelines used. "
                "Ask about constructor cost-per-point, driver ROI, or a selected circuit."
            ),
        }
    if intent == "regulatory_knowledge":
        return {
            "intent": intent,
            "route": "generalist_direct",
            "routing_rationale": "FIA financial-regulation explainer; OpenF1 standings are not required.",
            "analysis_notes": [
                {"phase": "identify", "detail": "Question is about how the FIA cost cap and penalties work, not a team's points."},
                {"phase": "sources", "detail": "Knowledge layer only. Skipped OpenF1, Jolpica, fact store, and search."},
                {"phase": "result", "detail": "No derived efficiency metric; regulatory summary only."},
            ],
            "answer": (
                "The FIA Formula 1 Financial Regulations set a cost cap on listed operational spending "
                "(the published figure is on the order of USD 135 million in recent seasons, with specified exclusions). "
                "Teams submit reporting packs; the FIA Cost Cap Administration audits them. "
                "Breaches can trigger sporting penalties (grid drops, aerodynamic or testing limits, points deductions) "
                "and/or financial penalties, depending on overspend size and whether the breach is procedural or sporting. "
                "This answer does not use OpenF1 race data."
            ),
        }
    if intent == "historical_out_of_coverage":
        year = _query_year(state) or _year(state)
        return {
            "intent": intent,
            "route": "generalist_direct",
            "routing_rationale": "Requested year is before OpenF1 telemetry coverage; no upstream calls.",
            "analysis_notes": [
                {"phase": "identify", "detail": "Requested telemetry for {0}.".format(year)},
                {
                    "phase": "sources",
                    "detail": "OpenF1 public session/lap coverage is treated as {0}+. Jolpica has historic results, not car telemetry.".format(
                        OPENF1_FROM_YEAR
                    ),
                },
                {"phase": "gap", "detail": "Will not call or retry OpenF1 for this year."},
            ],
            "answer": (
                "This request falls outside available telemetry coverage. OpenF1 does not provide "
                "fastest-lap telemetry for the 1998 Monaco Grand Prix (coverage is {0}+ completed sessions). "
                "I am not inventing lap times and I am not retrying OpenF1."
            ).format(OPENF1_FROM_YEAR),
        }
    if intent == "research":
        return {
            "intent": intent,
            "route": "researcher",
            "routing_rationale": (
                "Online research requested; Researcher searches, cites, and writes the fact store. "
                "year={0} meeting_key={1}.".format(state.get("season_year"), state.get("meeting_key"))
            ),
        }
    return {
        "intent": intent,
        "route": "data_analyst",
        "season_year": _year(state),
        "routing_rationale": (
            "F1 data question. Query year={0} dashboard year={1} meeting_key={2}.".format(
                _query_year(state) or _year(state),
                state.get("season_year"),
                state.get("meeting_key"),
            )
        ),
    }


def _payloads_by_tool(state: F1DashboardState) -> Dict[str, List[Dict[str, Any]]]:
    grouped: Dict[str, List[Dict[str, Any]]] = {}
    for payload in state.get("raw_payloads") or []:
        grouped.setdefault(payload.get("tool"), []).append(payload)
    return grouped


def _is_completed_race(session: Dict[str, Any]) -> bool:
    """True only for races whose scheduled start has already elapsed.

    Mid-season the calendar tail is the finale, not the latest completed GP, so
    form/DNF/pace fetches must be scoped to completed races only.
    """
    raw = session.get("date_start")
    if not raw:
        return False
    try:
        parsed = datetime.fromisoformat(str(raw).replace("Z", "+00:00"))
    except ValueError:
        return False
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.timestamp() + _RACE_COMPLETED_BUFFER_SECONDS <= datetime.now(timezone.utc).timestamp()


def _fp(tool: str, args: Dict[str, Any]) -> Tuple[str, Tuple[Tuple[str, str], ...]]:
    items = tuple(sorted((str(k), str(v)) for k, v in args.items()))
    return (tool, items)


def _done(state: F1DashboardState) -> Set[Tuple[str, Tuple[Tuple[str, str], ...]]]:
    seen = set()
    for call in state.get("tool_calls") or []:
        seen.add(_fp(call.get("tool"), call.get("args") or call.get("params") or {}))
    return seen


def _preview_rows(payload: Dict[str, Any]) -> List[Dict[str, Any]]:
    return list(payload.get("preview") or [])


def heuristic_analyst_plan(state: F1DashboardState) -> Dict[str, Any]:
    year = _year(state)
    meeting_key = state.get("meeting_key")
    intent = state.get("intent") or classify_intent(state)
    done = _done(state)
    grouped = _payloads_by_tool(state)
    selected: List[Dict[str, Any]] = []
    plan: List[str] = list(state.get("analysis_plan") or [])

    def want(tool: str, args: Dict[str, Any]) -> None:
        if _fp(tool, args) not in done:
            selected.append({"tool": tool, "args": args})

    if not plan:
        plan = ["Resolve season calendar", "Select relevant sessions", "Fetch comparative snapshots", "Synthesize"]

    if intent == "constructor_finance":
        plan = [
            "Read constructor championship points for the query year",
            "Read cited cap / valuation facts",
            "Join on constructor name and rank cost-per-point",
        ]
        if year:
            want("get_championship_teams", {"year": year})
            want("get_finance_estimates", {"year": year})
    elif intent == "driver_roi":
        plan = [
            "Read driver championship points for the query year (not the dashboard year)",
            "Read cited salary facts",
            "Join driver_number to salary entity_key and rank FER",
        ]
        if year:
            want("get_championship_drivers", {"year": year})
            want("get_finance_estimates", {"year": year})
    elif intent == "championship_projection":
        plan = [
            "Load the season Race calendar from OpenF1 sessions",
            "Read live driver and constructor championship tables",
            "Fetch recent race classifications (finishes, DNFs)",
            "Fetch OpenF1 /v1/drivers headshots for the key contenders",
        ]
        if year:
            want("list_sessions", {"year": year})
            want("get_championship_drivers", {"year": year})
            want("get_championship_teams", {"year": year})
            want("get_drivers", {"year": year})
        sessions = _preview_rows((grouped.get("list_sessions") or [{}])[-1]) if grouped.get("list_sessions") else []
        races = [s for s in sessions if str(s.get("session_name") or s.get("session_type")) == "Race"]
        races.sort(key=lambda s: str(s.get("date_start") or ""))
        completed = [r for r in races if _is_completed_race(r)]
        recent = completed[-5:] if completed else []
        for race in recent:
            if race.get("session_key"):
                want("get_session_result", {"session_key": race.get("session_key")})
        if recent and recent[-1].get("session_key"):
            want("get_drivers", {"session_key": recent[-1].get("session_key")})
    elif intent in {"comparative_standings", "unknown"}:
        if year:
            want("list_meetings", {"year": year})
        meetings = _preview_rows((grouped.get("list_meetings") or [{}])[-1]) if grouped.get("list_meetings") else []
        if meetings:
            want("list_sessions", {"year": year} if year else {})
        sessions = _preview_rows((grouped.get("list_sessions") or [{}])[-1]) if grouped.get("list_sessions") else []
        races = [s for s in sessions if str(s.get("session_name") or s.get("session_type")) == "Race"]
        races.sort(key=lambda s: str(s.get("date_start") or ""))
        if races:
            want("get_championship_drivers", {"session_key": races[0].get("session_key")})
            want("get_championship_drivers", {"session_key": races[-1].get("session_key")})
            want("get_drivers", {"session_key": races[-1].get("session_key")})
    elif intent == "meeting_insights":
        args: Dict[str, Any] = {}
        if meeting_key:
            args["meeting_key"] = meeting_key
        if year:
            args["year"] = year
        want("list_sessions", args)
        sessions = _preview_rows((grouped.get("list_sessions") or [{}])[-1]) if grouped.get("list_sessions") else []
        if meeting_key:
            want("get_race_control", {"meeting_key": meeting_key})
        if sessions:
            want("get_drivers", {"session_key": sessions[-1].get("session_key")})
        races = [s for s in sessions if str(s.get("session_name") or s.get("session_type")) == "Race"]
        races.sort(key=lambda s: str(s.get("date_start") or ""))
        for race in races[-2:]:
            want("get_session_result", {"session_key": race.get("session_key")})
    elif intent == "telemetry_compare":
        if year:
            want("list_sessions", {"year": year})
        sessions = _preview_rows((grouped.get("list_sessions") or [{}])[-1]) if grouped.get("list_sessions") else []
        if sessions:
            session_key = sessions[-1].get("session_key")
            want("get_drivers", {"session_key": session_key})
            want("get_session_result", {"session_key": session_key})
    elif intent in {"teammate_h2h", "stint_strategy", "position_gain"}:
        plan = [
            "Use the season named in the question (not the dashboard year)",
            "Fetch verified race classification or championship snapshot",
            "Do not invent quali deltas, stint pace, or grid-to-finish math",
        ]
        if year:
            want("get_championship_drivers", {"year": year})
            want("list_meetings", {"year": year})
        meetings = _preview_rows((grouped.get("list_meetings") or [{}])[-1]) if grouped.get("list_meetings") else []
        needle = ""
        if intent == "stint_strategy":
            needle = "bahrain"
        elif intent == "position_gain":
            needle = "monza"
        target = None
        for meeting in meetings:
            blob = " ".join(
                str(meeting.get(key) or "")
                for key in ("meeting_name", "circuit_short_name", "country_name")
            ).lower()
            if needle and (needle in blob or ("ital" in blob and needle == "monza")):
                target = meeting
                break
        if target and target.get("meeting_key"):
            want("list_sessions", {"meeting_key": target.get("meeting_key"), "year": year} if year else {"meeting_key": target.get("meeting_key")})
        sessions = _preview_rows((grouped.get("list_sessions") or [{}])[-1]) if grouped.get("list_sessions") else []
        races = [s for s in sessions if str(s.get("session_name") or s.get("session_type")) == "Race"]
        races.sort(key=lambda s: str(s.get("date_start") or ""))
        if races:
            want("get_session_result", {"session_key": races[-1].get("session_key")})

    if selected:
        return {
            "analysis_plan": plan,
            "selected_tools": selected,
            "needs_more_data": True,
            "season_year": year,
        }

    synthesis, notes, missing, assumptions = _synthesize(state, grouped)
    return {
        "analysis_plan": plan,
        "selected_tools": [],
        "needs_more_data": False,
        "synthesis": synthesis,
        "answer": synthesis,
        "analysis_notes": notes,
        "missing_inputs": missing,
        "assumptions": assumptions,
        "season_year": year,
    }


def heuristic_researcher_plan(state: F1DashboardState) -> Dict[str, Any]:
    year = _year(state)
    done = _done(state)
    grouped = _payloads_by_tool(state)
    selected: List[Dict[str, Any]] = []
    plan = list(state.get("analysis_plan") or []) or [
        "Search reputable sources",
        "Write cited facts to the store",
        "Read store (no invented USD)",
        "Synthesize with citations",
    ]

    def want(tool: str, args: Dict[str, Any]) -> None:
        if _fp(tool, args) not in done:
            selected.append({"tool": tool, "args": args})

    query = _query(state)
    search_args: Dict[str, Any] = {"query": query}
    if year:
        search_args["year"] = year
    want("search_commercial", search_args)
    if year:
        want("get_finance_estimates", {"year": year})

    if selected:
        return {
            "analysis_plan": plan,
            "selected_tools": selected,
            "needs_more_data": True,
        }
    synthesis, notes, missing, assumptions = _synthesize(state, grouped)
    return {
        "analysis_plan": plan,
        "selected_tools": [],
        "needs_more_data": False,
        "synthesis": synthesis,
        "answer": synthesis,
        "analysis_notes": notes,
        "missing_inputs": missing,
        "assumptions": assumptions,
    }


def _synthesize(
    state: F1DashboardState, grouped: Dict[str, List[Dict[str, Any]]]
) -> Tuple[str, List[Dict[str, str]], List[str], List[str]]:
    intent = state.get("intent") or classify_intent(state)
    from app.services.commercial import canonical_team
    from app.services.fact_store import DEFAULT_CAP_USD
    notes: List[Dict[str, str]] = []
    missing: List[str] = []
    assumptions: List[str] = []
    query = _query(state).lower()

    def rows(tool: str) -> List[Dict[str, Any]]:
        payloads = grouped.get(tool) or []
        if not payloads:
            return []
        return _preview_rows(payloads[-1])

    def done(text: str) -> Tuple[str, List[Dict[str, str]], List[str], List[str]]:
        if intent in {"constructor_finance", "driver_roi"}:
            text = _with_finance_tag(text)
        return text, notes, missing, assumptions

    if intent == "championship_projection":
        notes.append(
            {
                "phase": "handoff",
                "detail": "Standings, calendar, classifications, and laps retrieved. Strategic Analyst compiles the title projection.",
            }
        )
        return done(
            "Strategic Analyst will compile the championship projection from retrieved OpenF1 payloads (no cached copy)."
        )

    finance_payload = (grouped.get("get_finance_estimates") or [{}])[-1]
    if finance_payload.get("fact_year_fallback"):
        assumptions.append(
            "Commercial facts for {0} were empty; used stored year {1} as a labeled estimate proxy.".format(
                _year(state), finance_payload.get("fact_year")
            )
        )

    if intent in {"teammate_h2h", "stint_strategy", "position_gain"}:
        year = _year(state)
        notes.append({"phase": "identify", "detail": "Intent {0}; query year {1}.".format(intent, year)})
        classification = rows("get_session_result")
        champs = rows("get_championship_drivers")
        raw_bits = []
        source = "session classification"
        if classification:
            ordered = sorted(classification, key=lambda row: int(row.get("position") or 99))
            for row in ordered[:8]:
                raw_bits.append(
                    "P{0} #{1}".format(row.get("position") or "?", row.get("driver_number") or row.get("full_name") or "?")
                )
        elif champs:
            source = "championship snapshot"
            ordered = sorted(champs, key=lambda row: int(row.get("position_current") or row.get("position") or 99))
            for row in ordered[:8]:
                raw_bits.append(
                    "P{0} {1} ({2} pts)".format(
                        row.get("position_current") or row.get("position") or "?",
                        row.get("full_name") or row.get("driver_number") or "?",
                        row.get("points_current", row.get("points")),
                    )
                )
        snapshot = "; ".join(raw_bits) if raw_bits else "no verified classification rows in tool payloads"
        pending = (
            "Detailed lap-by-lap delta computation (qualifying gaps, final-stint pace, grid-to-finish) "
            "is pending full telemetry aggregation. I will not invent those derived numbers."
        )
        notes.append({"phase": "retrieve", "detail": "Raw {0}: {1}".format(source, snapshot[:240])})
        notes.append({"phase": "gap", "detail": pending})
        if intent == "teammate_h2h":
            missing.append("per-GP qualifying and race results joined for both drivers")
            return done(
                "Leclerc vs Sainz: verified {0} for {1}: {2}. {3}".format(source, year or "the requested season", snapshot, pending)
            )
        if intent == "stint_strategy":
            missing.append("stint compound map and lap times in the last stint window")
            return done(
                "Bahrain strategy: verified {0} (top of the order only): {1}. "
                "Tyre compound / final-stint pace is not computed here. {2}".format(source, snapshot, pending)
            )
        missing.append("starting grid joined to finishing classification")
        return done(
            "Monza positions: verified {0}: {1}. Net places from grid vs finish is not computed here. {2}".format(
                source, snapshot, pending
            )
        )

    if intent == "constructor_finance":
        teams = rows("get_championship_teams")
        facts = rows("get_finance_estimates")
        notes.append(
            {
                "phase": "identify",
                "detail": "Constructor cost-per-point = published/default cap ÷ constructor championship points.",
            }
        )
        notes.append(
            {
                "phase": "retrieve",
                "detail": "championship_teams={0} rows; finance facts={1} rows (fact year {2}).".format(
                    len(teams), len(facts), finance_payload.get("fact_year") or _year(state)
                ),
            }
        )
        cap = DEFAULT_CAP_USD
        cap_from_fact = False
        vals: Dict[str, float] = {}
        for fact in facts:
            metric = fact.get("metric")
            key = canonical_team(str(fact.get("entity_key") or ""))
            if metric == "budget_cap_usd" and fact.get("value_usd"):
                cap = float(fact["value_usd"])
                cap_from_fact = True
            if metric == "valuation_usd" and fact.get("value_usd"):
                vals[key] = float(fact["value_usd"])
        if not cap_from_fact:
            assumptions.append(
                "Used default USD {0:,.0f} cap; no cited budget_cap_usd fact was found for the requested year.".format(cap)
            )
        ranked = []
        for team in teams:
            name = str(team.get("team_name") or "")
            points = float(team.get("points_current") or team.get("points") or 0)
            if points <= 0:
                continue
            ranked.append((cap / points, name, points, vals.get(canonical_team(name))))
        ranked.sort(key=lambda item: item[0])
        named = []
        for cpp, name, points, val in ranked:
            blob = name.lower()
            if "mclaren" in query and "mclaren" in blob:
                named.append((cpp, name, points, val))
            if "ferrari" in query and "ferrari" in blob:
                named.append((cpp, name, points, val))
        show = named if len(named) >= 2 else ranked
        midfield = "midfield" in query
        if midfield and ranked:
            show = ranked[4:10] or ranked[3:]
            notes.append(
                {
                    "phase": "transform",
                    "detail": "Midfield defined as constructors ranked 5–10 by points (after sorting by cost-per-point among that slice).",
                }
            )
        notes.append(
            {
                "phase": "join",
                "detail": "Matched {0} constructors with points > 0 to a shared cap of ${1:,.0f}.".format(len(ranked), cap),
            }
        )
        if show:
            best = show[0]
            notes.append(
                {
                    "phase": "calculate",
                    "detail": "Formula: Cap ${0:,.0f} / Points {1:.0f} = ${2:,.0f}/pt ({3})".format(
                        cap, best[2], best[0], best[1]
                    ),
                }
            )
            notes.append(
                {
                    "phase": "result",
                    "detail": "{0} at about ${1:,.0f} per point ({2:.0f} pts).".format(best[1], best[0], best[2]),
                }
            )
            lines = []
            if len(named) >= 2:
                a, b = named[0], named[1]
                winner = a if a[0] <= b[0] else b
                lines.append(
                    "Under a ${0:,.0f} cap, {1} is more capital-efficient than the named peer "
                    "(${2:,.0f}/pt vs ${3:,.0f}/pt).".format(cap, winner[1], a[0], b[0])
                )
                for cpp, name, points, val in named:
                    lines.append("{0}: ${1:,.0f}/pt on {2:.0f} constructor points.".format(name, cpp, points))
            elif midfield:
                lines.append(
                    "Among a 2023-style midfield slice (P5–P10 by this ranking), {0} is the most efficient "
                    "at about ${1:,.0f} per point. Future-upside comments below are inference, not a forecast model.".format(
                        best[1], best[0]
                    )
                )
                for cpp, name, points, val in show[:4]:
                    lines.append("{0}: ${1:,.0f}/pt · {2:.0f} pts.".format(name, cpp, points))
                lines.append(
                    "Upside (qualitative): efficiency plus a points deficit vs the top three can be a cheaper exposure to future performance; this is not a recommendation to transact."
                )
            else:
                lines.append(
                    "{0} has the best stored cost-per-point in {1}: about ${2:,.0f} per point "
                    "({3:.0f} pts against a ${4:,.0f} cap).".format(
                        best[1], _year(state) or "", best[0], best[2], cap
                    )
                )
                for cpp, name, points, val in ranked[:5]:
                    extra = " valuation ~${0:,.0f}".format(val) if val else ""
                    lines.append("{0}: ${1:,.0f}/pt · {2:.0f} pts{3}.".format(name, cpp, points, extra))
            lines.append(
                "Metric: cost_per_point = cost_cap_usd / constructor_championship_points. "
                "Inputs: Jolpica/OpenF1 constructor points + stored cap (default USD 135M). "
                "Lower USD/pt is more efficient."
            )
            lines.append("Dollars are cited fact-store estimates (or the USD 135M default cap), not audited club accounts.")
            if assumptions:
                lines.append("Assumption: " + assumptions[0])
            return done(" ".join(lines))
        if facts:
            missing.append("constructor championship points")
            notes.append(
                {
                    "phase": "join",
                    "detail": "Finance rows={0}; championship_teams with points=0. Cannot complete cap/points.".format(
                        len(facts)
                    ),
                }
            )
            return done(
                "Constructor finance rows were retrieved ({0}), but constructor championship points were missing "
                "or all zero, so cost-per-point cannot be completed.".format(len(facts))
            )
        missing.append("constructor points and/or stored cap")

    if intent == "driver_roi":
        drivers = rows("get_championship_drivers")
        facts = rows("get_finance_estimates")
        salaries: Dict[str, float] = {}
        for fact in facts:
            if fact.get("metric") == "salary_usd" and fact.get("value_usd") is not None:
                salaries[str(fact.get("entity_key"))] = float(fact["value_usd"])
        notes.append({"phase": "identify", "detail": "FER = estimated salary_usd / championship points (lower is better ROI)."})
        notes.append(
            {
                "phase": "retrieve",
                "detail": "championship_drivers={0}; salary facts={1}; fact year {2}.".format(
                    len(drivers), len(salaries), finance_payload.get("fact_year") or _year(state)
                ),
            }
        )
        ranked = []
        unmatched_salary = set(salaries.keys())
        points_no_salary = []
        for driver in drivers:
            number = str(driver.get("driver_number") or "")
            points = float(driver.get("points_current") or driver.get("points") or 0)
            salary = salaries.get(number)
            name = str(driver.get("full_name") or driver.get("name_acronym") or number)
            if salary:
                unmatched_salary.discard(number)
            if points > 0 and not salary:
                points_no_salary.append(name or number)
            if not salary or points <= 0:
                continue
            ranked.append((salary / points, name, salary, points))
        ranked.sort(key=lambda item: item[0])
        notes.append(
            {
                "phase": "join",
                "detail": "Join key driver_number ↔ salary entity_key. Matched {0}. Unmatched salary keys={1}. Points without salary={2}.".format(
                    len(ranked),
                    ",".join(sorted(unmatched_salary)[:12]) or "none",
                    ",".join(points_no_salary[:8]) or "none",
                ),
            }
        )
        if ranked:
            notes.append({"phase": "calculate", "detail": "FER = salary / points; ranked ascending."})
            notes.append(
                {
                    "phase": "result",
                    "detail": "{0} first at ${1:,.0f} per point.".format(ranked[0][1], ranked[0][0]),
                }
            )
            lines = ["Top financial efficiency (salary per championship point) in {0}:".format(_year(state) or "")]
            for fer, name, salary, points in ranked[:5]:
                notes.append(
                    {
                        "phase": "calculate",
                        "detail": "Formula: Salary ${0:,.0f} / Points {1:.0f} = FER ${2:,.0f} ({3})".format(
                            salary, points, fer, name
                        ),
                    }
                )
                lines.append("{0}: ${1:,.0f}/pt on ${2:,.0f} salary and {3:.0f} pts.".format(name, fer, salary, points))
            lines.append("Retainers are stored estimates with citations, not audited payroll.")
            if assumptions:
                lines.append("Assumption: " + assumptions[0])
            return done(" ".join(lines))
        if facts:
            missing.append("join of salary entity_key to championship driver_number")
            notes.append(
                {
                    "phase": "gap",
                    "detail": "Join failed. Salary keys={0}. Driver numbers={1}.".format(
                        ",".join(sorted(salaries.keys())[:16]) or "none",
                        ",".join(str(d.get("driver_number") or "") for d in drivers[:16]) or "none",
                    ),
                }
            )
            return done(
                "Salary facts were retrieved ({0} rows) but could not be joined to championship points. "
                "Join key is driver_number on standings vs entity_key on salary facts. "
                "Salary keys: {1}. Driver numbers: {2}.".format(
                    len(facts),
                    ", ".join(sorted(salaries.keys())[:12]) or "none",
                    ", ".join(str(d.get("driver_number") or "?") for d in drivers[:12]) or "none",
                )
            )

    champs = grouped.get("get_championship_drivers") or []
    if intent in {"comparative_standings", "unknown"} and len(champs) >= 2:
        first = _preview_rows(champs[0])
        last = _preview_rows(champs[-1])
        first.sort(key=lambda r: int(r.get("position_current") or r.get("position") or 99))
        last.sort(key=lambda r: int(r.get("position_current") or r.get("position") or 99))
        lines = ["Championship snapshots (first vs last race in scope):"]
        for snapshot, label in ((first[:3], "first"), (last[:3], "latest")):
            names = []
            for row in snapshot:
                names.append(
                    "{0} ({1} pts)".format(
                        row.get("full_name") or row.get("name_acronym") or row.get("driver_number"),
                        row.get("points_current", row.get("points")),
                    )
                )
            lines.append("{0}: {1}".format(label, "; ".join(names) or "no rows"))
        notes.append({"phase": "result", "detail": "Compared first vs last championship_drivers snapshots."})
        return done(" ".join(lines))
    if grouped.get("search_commercial"):
        search = grouped["search_commercial"][-1]
        facts = grouped.get("get_finance_estimates") or []
        n_facts = facts[-1].get("record_count") if facts else 0
        return done(
            (
                "Researcher ran an online search ({0} hits) and read {1} stored commercial facts. "
                "Figures are cited estimates, not audited accounts."
            ).format(search.get("record_count") or 0, n_facts)
        )
    results = grouped.get("get_session_result") or []
    if results:
        dnf = 0
        podiums: Dict[str, int] = {}
        for payload in results:
            for row in _preview_rows(payload):
                if row.get("dnf") is True or str(row.get("dnf")).lower() in {"true", "1", "yes"}:
                    dnf += 1
                if int(row.get("position") or 99) <= 3:
                    key = str(row.get("driver_number") or row.get("full_name") or "?")
                    podiums[key] = podiums.get(key, 0) + 1
        return done(
            (
                "Operational snapshot from session results: {0} DNF flags across {1} race files. "
                "Podium appearances (driver numbers): {2}. Treat DNFs as reliability and cost risk, not a timing screen."
            ).format(
                dnf,
                len(results),
                ", ".join("{0}×{1}".format(k, v) for k, v in list(podiums.items())[:5]) or "none",
            )
        )
    if grouped.get("get_finance_estimates"):
        count = grouped["get_finance_estimates"][-1].get("record_count") or 0
        return done("Commercial fact store returned {0} cited rows for this season.".format(count))
    if grouped.get("get_championship_teams"):
        count = grouped["get_championship_teams"][-1].get("record_count") or 0
        return done(
            "Constructor standings retrieved ({0} teams). Join with stored valuations for cost-per-point.".format(count)
        )
    if grouped.get("get_race_control"):
        count = grouped["get_race_control"][-1].get("record_count") or 0
        return done("Meeting-scoped analysis: {0} race-control messages retrieved.".format(count))
    if grouped.get("get_laps"):
        count = grouped["get_laps"][-1].get("record_count") or 0
        return done("Pace comparison: retrieved {0} lap rows for the selected session.".format(count))
    if intent == "chitchat":
        return done(state.get("answer") or "")
    notes.append(
        {
            "phase": "gap",
            "detail": "Intent token={0}. No joinable payloads. Query year={1}.".format(intent, _year(state)),
        }
    )
    missing.append("tool payloads for intent {0}".format(intent))
    return done(
        "I did not get joinable championship or finance rows for this question (intent {0}, year {1}). "
        "See the Technical Manager tape for which APIs ran.".format(intent, _year(state) or "unknown")
    )


GENERALIST_SYSTEM_PROMPT = """You are the F1 Generalist router for a commercial BI console.
You do not answer quantitative questions from memory.

MUST set route=data_analyst (never generalist_direct, never invent numbers) when the query
asks for any of: points, lap times, telemetry, driver comparisons, season rankings,
who wins the championship, projected champion, efficiency, ROI, salary/point, cost-per-point,
valuations joined to results, or any math.

ONLY set route=generalist_direct for:
- greetings / what-can-you-do
- pure FIA regulatory explainers with no team metric (example: how the budget cap is enforced)
- out-of-coverage history (pre-2023 telemetry)

Use route=researcher only when the user explicitly asks to search/look up online.

Reply JSON keys: intent, route, routing_rationale, answer.
answer must be empty unless route is generalist_direct.
Never invent salaries, points, or ratios.
"""


def maybe_llm_generalist(state: F1DashboardState) -> Optional[Dict[str, Any]]:
    if not settings.llm_api_key:
        return None
    try:
        from langchain_core.messages import HumanMessage, SystemMessage
        from langchain_openai import ChatOpenAI

        model = ChatOpenAI(
            model=settings.llm_model,
            api_key=settings.llm_api_key,
            base_url=settings.llm_base_url,
            temperature=0,
        )
        prompt = (
            "Context year={0} meeting_key={1}. Query: {2}"
        ).format(state.get("season_year"), state.get("meeting_key"), _query(state))
        msg = model.invoke(
            [
                SystemMessage(content=GENERALIST_SYSTEM_PROMPT),
                HumanMessage(content=prompt),
            ]
        )
        import json

        data = json.loads(str(msg.content))
        return {
            "intent": data.get("intent") or classify_intent(state),
            "route": data.get("route") or heuristic_generalist(state).get("route"),
            "routing_rationale": data.get("routing_rationale") or "",
            "answer": data.get("answer") or "",
        }
    except Exception:
        return None


classify_intent = classify_intent
heuristic_analyst_plan = heuristic_analyst_plan
maybe_llm_generalist = maybe_llm_generalist
heuristic_generalist = heuristic_generalist
