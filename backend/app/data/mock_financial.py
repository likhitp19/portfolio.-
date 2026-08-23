"""Cited-style commercial estimates for 2023/2024.

The data analyst must join these to OpenF1/Jolpica points. It must never invent
salaries or valuations outside this dictionary (or the SQLite fact store).
"""

from typing import Any, Dict, List, Optional

MOCK_FINANCIAL_DATA: Dict[int, Dict[str, Any]] = {
    2024: {
        "budget_cap_usd": 135_000_000,
        "teams": {
            "red bull racing": {"name": "Red Bull Racing", "valuation_usd": 2_600_000_000},
            "mclaren": {"name": "McLaren", "valuation_usd": 2_000_000_000},
            "ferrari": {"name": "Ferrari", "valuation_usd": 3_800_000_000},
            "mercedes": {"name": "Mercedes", "valuation_usd": 2_200_000_000},
            "aston martin": {"name": "Aston Martin", "valuation_usd": 900_000_000},
            "alpine": {"name": "Alpine", "valuation_usd": 650_000_000},
            "williams": {"name": "Williams", "valuation_usd": 800_000_000},
            "haas": {"name": "Haas", "valuation_usd": 400_000_000},
            "rb": {"name": "RB", "valuation_usd": 700_000_000},
            "sauber": {"name": "Sauber", "valuation_usd": 500_000_000},
        },
        "drivers": {
            "1": {"name": "Max Verstappen", "salary_usd": 55_000_000},
            "11": {"name": "Sergio Perez", "salary_usd": 10_000_000},
            "4": {"name": "Lando Norris", "salary_usd": 24_000_000},
            "81": {"name": "Oscar Piastri", "salary_usd": 3_000_000},
            "16": {"name": "Charles Leclerc", "salary_usd": 24_000_000},
            "55": {"name": "Carlos Sainz", "salary_usd": 12_000_000},
            "44": {"name": "Lewis Hamilton", "salary_usd": 40_000_000},
            "63": {"name": "George Russell", "salary_usd": 18_000_000},
        },
    },
    2023: {
        "budget_cap_usd": 135_000_000,
        "teams": {
            "red bull racing": {"name": "Red Bull Racing", "valuation_usd": 2_500_000_000},
            "mclaren": {"name": "McLaren", "valuation_usd": 1_500_000_000},
            "ferrari": {"name": "Ferrari", "valuation_usd": 3_500_000_000},
            "mercedes": {"name": "Mercedes", "valuation_usd": 2_000_000_000},
            "aston martin": {"name": "Aston Martin", "valuation_usd": 800_000_000},
            "alpine": {"name": "Alpine", "valuation_usd": 700_000_000},
            "williams": {"name": "Williams", "valuation_usd": 700_000_000},
            "haas": {"name": "Haas", "valuation_usd": 380_000_000},
            "rb": {"name": "AlphaTauri", "valuation_usd": 600_000_000},
            "sauber": {"name": "Alfa Romeo", "valuation_usd": 450_000_000},
        },
        "drivers": {
            "1": {"name": "Max Verstappen", "salary_usd": 55_000_000},
            "11": {"name": "Sergio Perez", "salary_usd": 10_000_000},
            "4": {"name": "Lando Norris", "salary_usd": 20_000_000},
            "81": {"name": "Oscar Piastri", "salary_usd": 2_000_000},
            "16": {"name": "Charles Leclerc", "salary_usd": 24_000_000},
            "55": {"name": "Carlos Sainz", "salary_usd": 12_000_000},
            "44": {"name": "Lewis Hamilton", "salary_usd": 40_000_000},
            "63": {"name": "George Russell", "salary_usd": 16_000_000},
        },
    },
}

SOURCE = {
    "source_title": "MOCK_FINANCIAL_DATA (public estimates)",
    "source_url": None,
    "snippet": "Local mock dictionary for 2023/2024 retainers and franchise values. Not audited payroll.",
    "status": "estimate",
}


def mock_year(year: Optional[int]) -> Optional[int]:
    if year in MOCK_FINANCIAL_DATA:
        return year
    if year and year >= 2025 and 2024 in MOCK_FINANCIAL_DATA:
        return 2024
    return None


def mock_facts_for_year(year: int) -> List[Dict[str, Any]]:
    key = mock_year(year)
    if key is None:
        return []
    block = MOCK_FINANCIAL_DATA[key]
    rows: List[Dict[str, Any]] = [
        {
            "entity_type": "regulation",
            "entity_key": "fia_cost_cap",
            "season_year": key,
            "metric": "budget_cap_usd",
            "value_usd": block["budget_cap_usd"],
            **SOURCE,
        }
    ]
    for team_key, team in block["teams"].items():
        rows.append(
            {
                "entity_type": "constructor",
                "entity_key": team_key,
                "season_year": key,
                "metric": "valuation_usd",
                "value_usd": team["valuation_usd"],
                **SOURCE,
            }
        )
    for number, driver in block["drivers"].items():
        rows.append(
            {
                "entity_type": "driver",
                "entity_key": str(number),
                "season_year": key,
                "metric": "salary_usd",
                "value_usd": driver["salary_usd"],
                "name": driver["name"],
                **SOURCE,
            }
        )
    return rows
