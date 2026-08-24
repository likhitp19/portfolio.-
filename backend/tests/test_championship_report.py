from datetime import datetime, timezone

from app.agents.planning import _year, classify_intent
from app.services.championship_report import build_championship_report
from app.services.chat_layers import split_answer_layers


def test_this_year_means_calendar_year():
    state = {
        "user_query": "Who is projected to win the Championship this year, and what does the data say?",
        "season_year": 2025,
    }
    assert classify_intent(state) == "championship_projection"
    assert _year(state) == datetime.now(timezone.utc).year


def test_championship_report_from_live_payloads():
    grouped = {
        "get_championship_drivers": [
            {
                "preview": [
                    {"full_name": "Lando Norris", "team_name": "McLaren", "points": 350, "position": 1, "driver_number": 4},
                    {"full_name": "Oscar Piastri", "team_name": "McLaren", "points": 310, "position": 2, "driver_number": 81},
                    {"full_name": "Max Verstappen", "team_name": "Red Bull Racing", "points": 280, "position": 3, "driver_number": 1},
                ]
            }
        ],
        "get_championship_teams": [
            {
                "preview": [
                    {"team_name": "McLaren", "points": 660, "position": 1},
                    {"team_name": "Ferrari", "points": 400, "position": 2},
                ]
            }
        ],
        "list_sessions": [
            {
                "preview": [
                    {"session_name": "Race", "session_key": 1, "date_start": "2025-03-01T00:00:00+00:00", "circuit_short_name": "Melbourne"},
                    {"session_name": "Race", "session_key": 99, "date_start": "2025-12-01T00:00:00+00:00", "circuit_short_name": "Abu Dhabi"},
                ]
            }
        ],
        "get_session_result": [
            {
                "preview": [
                    {"driver_number": 4, "full_name": "Lando Norris", "position": 1, "dnf": False},
                    {"driver_number": 81, "full_name": "Oscar Piastri", "position": 2, "dnf": False},
                    {"driver_number": 1, "full_name": "Max Verstappen", "position": 99, "dnf": True},
                ]
            }
        ],
        "get_drivers": [
            {
                "preview": [
                    {
                        "driver_number": 4,
                        "full_name": "Lando Norris",
                        "headshot_url": "https://media.formula1.com/norris.png",
                    },
                    {"driver_number": 81, "full_name": "Oscar Piastri", "headshot_url": "https://media.formula1.com/piastri.png"},
                    {"driver_number": 1, "full_name": "Max Verstappen"},
                ]
            }
        ],
    }
    report = build_championship_report(grouped, 2025, now=datetime(2025, 8, 1, tzinfo=timezone.utc))
    assert report["predicted_winner"] == "Lando Norris"
    assert report["contenders"][0]["headshot_url"] == "https://media.formula1.com/norris.png"
    assert report["follow_ups"]
    assert report["confidence"] >= 0.51
    assert "Executive TL;DR" in report["answer"]
    assert "Pace & Trajectory" in report["answer"]
    assert "DNF" in report["answer"]
    layers = split_answer_layers(report["answer"])
    assert "Lando Norris" in layers.executive_summary
    assert "Teammate Delta" in layers.deep_dive
