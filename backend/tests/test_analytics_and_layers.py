from app.services.analytics import (
    classify_quadrant,
    pair_teammates,
    parse_lap_ms,
    quali_gaps_by_constructor,
    same_session_quali_ms,
    timeline_has_holes,
)
from app.services.chat_layers import split_answer_layers
from app.services.lineage import constructor_lineage_id


def test_parse_lap_ms_minutes():
    assert abs(parse_lap_ms("1:29.784") - 89784.0) < 0.01
    assert parse_lap_ms("") is None


def test_same_session_quali_prefers_shared_segment():
    left = {"Q1": "1:32.000", "Q2": "1:31.000", "Q3": "1:29.500"}
    right = {"Q1": "1:32.400", "Q2": "1:31.200"}
    pair = same_session_quali_ms(left, right)
    assert pair is not None
    assert abs(pair[0] - 91000.0) < 0.01
    assert abs(pair[1] - 91200.0) < 0.01


def test_lineage_maps_rebrands():
    assert constructor_lineage_id("alphatauri") == "rb"
    assert constructor_lineage_id("racing_point") == "aston_martin"
    assert constructor_lineage_id("lotus_f1") == "alpine"
    assert constructor_lineage_id("alfa", "Alfa Romeo") == "sauber"
    assert constructor_lineage_id("", "Red Bull Racing") == "red_bull"


def test_pair_teammates_takes_top_two_by_points():
    drivers = [
        {"full_name": "Lando Norris", "constructor_id": "mclaren", "team_name": "McLaren", "points": 300},
        {"full_name": "Oscar Piastri", "constructor_id": "mclaren", "team_name": "McLaren", "points": 250},
        {"full_name": "Reserve", "constructor_id": "mclaren", "team_name": "McLaren", "points": 0},
        {"full_name": "Solo", "constructor_id": "sauber", "team_name": "Kick Sauber", "points": 4},
    ]
    pairs = pair_teammates(drivers)
    assert len(pairs) == 1
    lead, second, lineage, team = pairs[0]
    assert lineage == "mclaren"
    assert team == "McLaren"
    assert lead["full_name"] == "Lando Norris"
    assert second["full_name"] == "Oscar Piastri"


def test_quali_gaps_and_quadrants():
    races = [
        {
            "round": "1",
            "QualifyingResults": [
                {"Driver": {"givenName": "Lando", "familyName": "Norris"}, "Constructor": {"constructorId": "mclaren", "name": "McLaren"}, "Q3": "1:29.000"},
                {"Driver": {"givenName": "Oscar", "familyName": "Piastri"}, "Constructor": {"constructorId": "mclaren", "name": "McLaren"}, "Q3": "1:29.250"},
            ],
        }
    ]
    gaps = quali_gaps_by_constructor(races)
    assert gaps["mclaren"][0] == 250.0
    assert classify_quadrant(80, 250) == "high_asset_risk"
    assert classify_quadrant(55, 80) == "balanced_portfolio"
    assert classify_quadrant(70, 80) == "watch"


def test_split_answer_layers_uses_opening_sentences():
    layers = split_answer_layers(
        "McLaren is the most efficient constructor in 2024. Cost per point is $202,703.\n\n"
        "| Team | USD / pt |\n| --- | --- |\n| McLaren | 202703 |\n\n"
        "Formula: budget_cap_usd / constructor_points."
    )
    assert "McLaren is the most efficient" in layers.executive_summary
    assert "Cost per point" in layers.executive_summary
    assert "USD / pt" in layers.deep_dive
    assert "Formula:" in layers.deep_dive


def test_timeline_holes_ignore_current_year():
    years = [2023, 2024, 2025, 2026]
    by_year = {2023: [{"points": 1}], 2024: [{"points": 1}], 2025: [{"points": 1}], 2026: []}
    assert timeline_has_holes(years, by_year, 2026) is False
    by_year[2024] = []
    assert timeline_has_holes(years, by_year, 2026) is True
