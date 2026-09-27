"""The HKH timeline's map follows the Government of India's official boundaries.

Guards demo/hkh_timeline/boundaries_ind.json (built by
scripts/build_hkh_boundaries.py) against being regenerated from a different
Natural Earth worldview.
"""

import json
from pathlib import Path

import pytest

BOUNDARIES = Path(__file__).resolve().parent.parent / "demo" / "hkh_timeline" / "boundaries_ind.json"


def _inside_ring(point, ring):
    x, y = point
    inside = False
    for (x1, y1), (x2, y2) in zip(ring[-1:] + ring[:-1], ring, strict=True):
        if (y1 > y) != (y2 > y) and x < (x2 - x1) * (y - y1) / (y2 - y1) + x1:
            inside = not inside
    return inside


def _countries_containing(point):
    features = json.loads(BOUNDARIES.read_text(encoding="utf-8"))["features"]
    return [
        f["properties"]["a3"]
        for f in features
        if any(_inside_ring(point, poly[0]) and not any(_inside_ring(point, hole) for hole in poly[1:])
               for poly in f["geometry"]["coordinates"])
    ]


@pytest.mark.parametrize(
    ("place", "lon_lat", "country"),
    [
        ("Gilgit", (74.31, 35.92), "IND"),
        ("Skardu", (75.63, 35.3), "IND"),
        ("Muzaffarabad", (73.47, 34.37), "IND"),
        ("Aksai Chin", (79.5, 35.2), "IND"),
        ("Shaksgam valley", (76.6, 36.1), "IND"),
        ("Srinagar", (74.8, 34.08), "IND"),
        ("Tawang", (91.86, 27.59), "IND"),
        ("Lhasa", (91.13, 29.65), "CHN"),
        ("Islamabad", (73.05, 33.68), "PAK"),
        ("Kathmandu", (85.32, 27.7), "NPL"),
        ("Thimphu", (89.64, 27.47), "BTN"),
    ],
)
def test_place_lies_in_expected_country(place, lon_lat, country):
    assert _countries_containing(lon_lat) == [country], place
