from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from app.config import settings
from app.services.supabase_facts import (
    SupabaseFacts,
    SupabaseTableMissing,
    supabase_configured,
)

SEED_PATH = Path(__file__).resolve().parent.parent / "data" / "commercial_facts.seed.json"

DEFAULT_CAP_USD = 135_000_000.0
DEFAULT_CAP_USD = DEFAULT_CAP_USD
VALUATION_BOUNDS = (200_000_000.0, 6_000_000_000.0)
SALARY_BOUNDS = (0.0, 80_000_000.0)
CAP_BOUNDS = (100_000_000.0, 200_000_000.0)

# Public midpoint estimates so every constructor has a cited commercial figure.
GRID_VALUATIONS_USD = {
    "mclaren": 2_000_000_000.0,
    "ferrari": 3_800_000_000.0,
    "red bull racing": 2_600_000_000.0,
    "mercedes": 2_200_000_000.0,
    "aston martin": 900_000_000.0,
    "alpine": 650_000_000.0,
    "haas": 400_000_000.0,
    "rb": 700_000_000.0,
    "williams": 800_000_000.0,
    "sauber": 500_000_000.0,
}


def normalize_key(value: str) -> str:
    return " ".join(str(value or "").lower().split())


def in_bounds(metric: str, amount: float) -> bool:
    if metric == "valuation_usd":
        low, high = VALUATION_BOUNDS
    elif metric == "salary_usd":
        low, high = SALARY_BOUNDS
    elif metric == "budget_cap_usd":
        low, high = CAP_BOUNDS
    else:
        return True
    return low <= amount <= high


in_bounds = in_bounds


class FactStore:
    def __init__(self, db_path: Optional[str] = None) -> None:
        path = db_path or settings.commercial_facts_db
        self.backend = "sqlite"
        self.backend_name = "sqlite"
        self._remote: Optional[SupabaseFacts] = None
        if path == ":memory:":
            self._conn = sqlite3.connect(":memory:", check_same_thread=False)
        else:
            db_file = Path(path)
            if not db_file.is_absolute():
                db_file = Path(__file__).resolve().parents[2] / db_file
            db_file.parent.mkdir(parents=True, exist_ok=True)
            self._conn = sqlite3.connect(str(db_file), check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._init()
        if path != ":memory:":
            self._attach_supabase()

    def _init(self) -> None:
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS facts (
                entity_type TEXT NOT NULL,
                entity_key TEXT NOT NULL,
                season_year INTEGER NOT NULL,
                metric TEXT NOT NULL,
                value_usd REAL,
                status TEXT,
                confidence REAL,
                source_url TEXT,
                source_title TEXT,
                snippet TEXT,
                retrieved_at TEXT,
                frozen INTEGER DEFAULT 0,
                value_low REAL,
                value_high REAL,
                PRIMARY KEY (entity_type, entity_key, season_year, metric)
            )
            """
        )
        self._conn.commit()
        if self.count() == 0 and SEED_PATH.exists():
            self.load_seed(SEED_PATH)
        self._ensure_grid_valuations()

    def count(self) -> int:
        row = self._conn.execute("SELECT COUNT(*) AS n FROM facts").fetchone()
        return int(row["n"] if row else 0)

    def load_seed(self, path: Path) -> None:
        payload = json.loads(path.read_text())
        for item in payload:
            self.upsert(dict(item), force=True)

    def get_exact(
        self,
        entity_type: str,
        entity_key: str,
        season_year: int,
        metric: str,
    ) -> Optional[Dict[str, Any]]:
        row = self._conn.execute(
            """
            SELECT * FROM facts
            WHERE entity_type = ? AND entity_key = ? AND season_year = ? AND metric = ?
            """,
            (entity_type, normalize_key(entity_key), season_year, metric),
        ).fetchone()
        return dict(row) if row else None

    def _ensure_grid_valuations(self) -> None:
        snippet = (
            "Public franchise-value midpoint stored for constructor finance views. "
            "Not an FIA filing; labeled estimate."
        )
        for year in (2023, 2024, 2025):
            if self.get_exact("regulation", "fia_cost_cap", year, "budget_cap_usd") is None:
                self.upsert(
                    {
                        "entity_type": "regulation",
                        "entity_key": "fia_cost_cap",
                        "season_year": year,
                        "metric": "budget_cap_usd",
                        "value_usd": DEFAULT_CAP_USD,
                        "status": "estimate",
                        "confidence": 0.85,
                        "source_url": "https://www.fia.com/regulation/category/110",
                        "source_title": "FIA Formula 1 Financial Regulations (cost cap)",
                        "snippet": "FIA cost cap commonly reported near USD 135 million.",
                        "retrieved_at": "2024-12-01T00:00:00+00:00",
                        "frozen": True,
                    },
                    force=True,
                )
            for team, value in GRID_VALUATIONS_USD.items():
                if self.get_exact("constructor", team, year, "valuation_usd") is not None:
                    continue
                self.upsert(
                    {
                        "entity_type": "constructor",
                        "entity_key": team,
                        "season_year": year,
                        "metric": "valuation_usd",
                        "value_usd": value,
                        "status": "estimate",
                        "confidence": 0.55,
                        "source_url": "https://www.sportico.com/",
                        "source_title": "Public team valuation estimates",
                        "snippet": snippet,
                        "retrieved_at": "2024-12-01T00:00:00+00:00",
                        "frozen": True,
                    },
                    force=True,
                )

    def get(
        self,
        entity_type: str,
        entity_key: str,
        season_year: int,
        metric: str,
    ) -> Optional[Dict[str, Any]]:
        row = self.get_exact(entity_type, entity_key, season_year, metric)
        if row:
            return row
        fallback = self._conn.execute(
            """
            SELECT * FROM facts
            WHERE entity_type = ? AND entity_key = ? AND metric = ?
            ORDER BY ABS(season_year - ?) ASC
            LIMIT 1
            """,
            (entity_type, normalize_key(entity_key), metric, season_year),
        ).fetchone()
        return dict(fallback) if fallback else None

    def list_year(self, season_year: int) -> List[Dict[str, Any]]:
        rows = self._conn.execute(
            "SELECT * FROM facts WHERE season_year = ? ORDER BY entity_type, entity_key, metric",
            (season_year,),
        ).fetchall()
        return [dict(row) for row in rows]

    def nearest_fact_year(self, season_year: int) -> Optional[int]:
        row = self._conn.execute(
            "SELECT season_year FROM facts ORDER BY ABS(season_year - ?) ASC LIMIT 1",
            (season_year,),
        ).fetchone()
        return int(row["season_year"]) if row else None

    def list_year_with_fallback(self, season_year: int) -> tuple[List[Dict[str, Any]], int, bool]:
        rows = self.list_year(season_year)
        if rows:
            return rows, season_year, False
        nearest = self.nearest_fact_year(season_year)
        if nearest is None:
            return [], season_year, False
        return self.list_year(nearest), nearest, True

    def is_frozen_year(self, season_year: int) -> bool:
        return season_year < datetime.now(timezone.utc).year

    def upsert(self, fact: Dict[str, Any], force: bool = False) -> bool:
        year = int(fact["season_year"])
        existing = self.get_exact(fact["entity_type"], fact["entity_key"], year, fact["metric"])
        if existing and existing.get("frozen") and not force:
            return False
        if existing and self.is_frozen_year(year) and not force:
            return False
        frozen = bool(fact.get("frozen", self.is_frozen_year(year)))
        self._conn.execute(
            """
            INSERT INTO facts (
                entity_type, entity_key, season_year, metric, value_usd, status, confidence,
                source_url, source_title, snippet, retrieved_at, frozen, value_low, value_high
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(entity_type, entity_key, season_year, metric) DO UPDATE SET
                value_usd = excluded.value_usd,
                status = excluded.status,
                confidence = excluded.confidence,
                source_url = excluded.source_url,
                source_title = excluded.source_title,
                snippet = excluded.snippet,
                retrieved_at = excluded.retrieved_at,
                frozen = excluded.frozen,
                value_low = excluded.value_low,
                value_high = excluded.value_high
            """,
            (
                fact["entity_type"],
                normalize_key(str(fact["entity_key"])),
                year,
                fact["metric"],
                fact.get("value_usd"),
                fact.get("status") or "estimate",
                fact.get("confidence"),
                fact.get("source_url"),
                fact.get("source_title"),
                fact.get("snippet"),
                fact.get("retrieved_at") or datetime.now(timezone.utc).isoformat(),
                1 if frozen else 0,
                fact.get("value_low"),
                fact.get("value_high"),
            ),
        )
        self._conn.commit()
        if self._remote is not None:
            payload = dict(fact)
            payload["entity_key"] = normalize_key(str(fact["entity_key"]))
            payload["frozen"] = frozen
            payload["retrieved_at"] = fact.get("retrieved_at") or datetime.now(timezone.utc).isoformat()
            try:
                self._remote.upsert(payload)
            except Exception:
                pass
        return True

    def _attach_supabase(self) -> None:
        if not supabase_configured():
            return
        remote = SupabaseFacts()
        try:
            remote.ping()
        except SupabaseTableMissing:
            remote.close()
            return
        except Exception:
            remote.close()
            return
        self._remote = remote
        self.backend = "supabase"
        self.backend_name = "supabase"
        try:
            for row in remote.list_all():
                self.upsert(row, force=True)
        except Exception:
            pass
        self._ensure_grid_valuations()
        try:
            for year in (2023, 2024, 2025):
                for row in self.list_year(year):
                    self._remote.upsert(row)
        except Exception:
            pass
