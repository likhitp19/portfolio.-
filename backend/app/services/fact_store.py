from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from app.config import settings

SEED_PATH = Path(__file__).resolve().parent.parent / "data" / "commercial_facts.seed.json"

DEFAULT_CAP_USD = 135_000_000.0
VALUATION_BOUNDS = (200_000_000.0, 6_000_000_000.0)
SALARY_BOUNDS = (0.0, 80_000_000.0)
CAP_BOUNDS = (100_000_000.0, 200_000_000.0)


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


class FactStore:
    def __init__(self, db_path: Optional[str] = None) -> None:
        path = db_path or settings.commercial_facts_db
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

    def count(self) -> int:
        row = self._conn.execute("SELECT COUNT(*) AS n FROM facts").fetchone()
        return int(row["n"] if row else 0)

    def load_seed(self, path: Path) -> None:
        payload = json.loads(path.read_text())
        for item in payload:
            self.upsert(dict(item), force=True)

    def get(
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
        if row:
            return dict(row)
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
        existing = self.get(fact["entity_type"], fact["entity_key"], year, fact["metric"])
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
        return True
