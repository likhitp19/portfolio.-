def progressionToChartRows(data):
    rows = []
    for index, circuit in enumerate(data["circuits"]):
        row = {"circuit": circuit["name"], "meeting_key": circuit["meeting_key"]}
        for series in data["series"]:
            points = series["points"]
            row[series["driver"]] = points[index] if index < len(points) else 0
        rows.append(row)
    return rows


def test_progression_chart_contract():
    data = {
        "circuits": [
            {"meeting_key": 1, "name": "Sakhir"},
            {"meeting_key": 2, "name": "Jeddah"},
        ],
        "series": [
            {"driver": "Max Verstappen", "points": [25, 43]},
            {"driver": "Lando Norris", "points": [18, 36]},
        ],
    }
    rows = progressionToChartRows(data)
    assert rows[0]["circuit"] == "Sakhir"
    assert rows[1]["Max Verstappen"] == 43
