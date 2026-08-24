"""Stable constructor identities across rebrands (2014–present)."""

from typing import Dict, Optional

from app.services.commercial import canonical_team

# Ergast constructorId / display aliases → a single time-series key.
LINEAGE: Dict[str, str] = {
    "mercedes": "mercedes",
    "ferrari": "ferrari",
    "mclaren": "mclaren",
    "red_bull": "red_bull",
    "red_bull_racing": "red_bull",
    "red bull racing": "red_bull",
    "williams": "williams",
    "haas": "haas",
    "lotus_f1": "alpine",
    "renault": "alpine",
    "alpine": "alpine",
    "force_india": "aston_martin",
    "racing_point": "aston_martin",
    "aston_martin": "aston_martin",
    "aston martin": "aston_martin",
    "toro_rosso": "rb",
    "alphatauri": "rb",
    "rb": "rb",
    "sauber": "sauber",
    "alfa": "sauber",
    "alfa_romeo": "sauber",
    "kick_sauber": "sauber",
}

DISPLAY_NAME: Dict[str, str] = {
    "mercedes": "Mercedes",
    "ferrari": "Ferrari",
    "mclaren": "McLaren",
    "red_bull": "Red Bull",
    "williams": "Williams",
    "haas": "Haas",
    "alpine": "Alpine",
    "aston_martin": "Aston Martin",
    "rb": "Racing Bulls",
    "sauber": "Kick Sauber",
}

GRID_LINEAGE_IDS = (
    "mclaren",
    "ferrari",
    "red_bull",
    "mercedes",
    "aston_martin",
    "alpine",
    "williams",
    "haas",
    "rb",
    "sauber",
)


def constructor_lineage_id(constructor_id: Optional[str], team_name: Optional[str] = None) -> str:
    raw_id = str(constructor_id or "").strip().lower().replace(" ", "_").replace("-", "_")
    if raw_id in LINEAGE:
        return LINEAGE[raw_id]
    key = canonical_team(team_name or raw_id.replace("_", " ") or "")
    if key in LINEAGE:
        return LINEAGE[key]
    underscored = key.replace(" ", "_")
    return LINEAGE.get(underscored, underscored)


def display_name_for(lineage_id: str, fallback: str = "") -> str:
    return DISPLAY_NAME.get(lineage_id, fallback or lineage_id.replace("_", " ").title())
