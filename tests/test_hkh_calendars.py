"""Check the HKH timeline's in-browser calendars (demo/hkh_timeline/calendars.js).

The amanta month and tithi must agree with starcharts.masa / panchanga (the
JS runs on the lighter astro.js ephemeris, so samples within minutes of a
boundary are skipped), and each calendar's new year must land on the date
published by the authority that keeps it. Skipped when node is absent.
"""

import json
import random
import shutil
import subprocess
from pathlib import Path

import pytest
import swisseph as swe

from starcharts.constants import GRAHAS
from starcharts.ephemeris import graha_position
from starcharts.masa import masa_at
from starcharts.panchanga import moon_sun_elongation, tithi_at

CALENDARS_JS = Path(__file__).resolve().parent.parent / "demo" / "hkh_timeline" / "calendars.js"

pytestmark = pytest.mark.skipif(shutil.which("node") is None, reason="node not installed")


def run_js(body: str, *args) -> object:
    script = f"const C = require(process.argv[1]); const args = JSON.parse(process.argv[2]); {body}"
    out = subprocess.run(
        ["node", "-e", script, str(CALENDARS_JS), json.dumps(args)],
        capture_output=True, text=True, check=True,
    ).stdout
    return json.loads(out)


def _near_rashi_boundary(jd: float) -> bool:
    lon = graha_position(jd, GRAHAS["Surya"]).sidereal_longitude
    return min(lon % 30.0, 30.0 - lon % 30.0) < 0.05


def test_lunisolar_month_and_tithi_match_the_python_engine():
    rng = random.Random(1148)
    samples = []
    while len(samples) < 120:
        jd = swe.julday(rng.randint(600, 2100), rng.randint(1, 12), rng.randint(1, 28), rng.uniform(0, 24))
        elongation = moon_sun_elongation(jd)
        if min(elongation % 12.0, 12.0 - elongation % 12.0) < 0.3:
            continue  # within ~30 minutes of a tithi boundary
        masa = masa_at(jd)
        if jd - masa.amavasya_start_jd < 0.1 or masa.amavasya_end_jd - jd < 0.1:
            continue
        if _near_rashi_boundary(masa.amavasya_start_jd) or _near_rashi_boundary(masa.amavasya_end_jd):
            continue  # adhika/kshaya status hinges on minutes
        samples.append((jd, masa, tithi_at(jd)))

    js = run_js(
        "console.log(JSON.stringify(args.map((jd) => { const l = C.lunisolar(jd, 0);"
        " return [C.MASA[l.month.idx], l.month.adhika, l.month.kshaya, l.tithi.n]; })));",
        *[jd for jd, _, _ in samples],
    )
    for (jd, masa, tithi), (name, adhika, kshaya, tithi_number) in zip(samples, js, strict=True):
        assert (name, adhika, kshaya) == (masa.name, masa.is_adhika, masa.is_kshaya), f"JD {jd}"
        assert tithi_number == tithi.number, f"JD {jd}"


# (Gregorian date the year begins, expected year label, calendar id)
PUBLISHED_NEW_YEARS = [
    ((2023, 4, 14), "2080 BS", "np-bs"),
    ((2024, 4, 13), "2081 BS", "np-bs"),
    ((2025, 4, 14), "2082 BS", "np-bs"),
    ((2026, 4, 14), "2083 BS", "np-bs"),
    ((2023, 11, 14), "NS 1144", "np-ns"),
    ((2024, 11, 2), "NS 1145", "np-ns"),
    ((2025, 10, 22), "NS 1146", "np-ns"),
    ((2023, 3, 22), "VS 2080", "in-vs"),
    ((2024, 4, 9), "VS 2081", "in-vs"),
    ((2026, 3, 19), "VS 2083", "in-vs"),
    ((2023, 3, 21), "1402 SH", "af-sh"),
    ((2024, 3, 20), "1403 SH", "af-sh"),
    ((2025, 3, 21), "1404 SH", "af-sh"),
    ((2024, 3, 21), "Saka 1946", "in-national"),
    ((2026, 3, 22), "Saka 1948", "in-national"),
    ((2026, 4, 14), "1433 Bangabda", "bd-bangla"),
    ((2023, 4, 15), "1430 BS (Bangabda)", "in-bengali"),
    ((2024, 4, 14), "1431 BS (Bangabda)", "in-bengali"),
]


@pytest.mark.parametrize(("date", "label", "cal_id"), PUBLISHED_NEW_YEARS)
def test_new_year_falls_on_the_published_date(date, label, cal_id):
    y, m, d = date
    # 06:00 UT is late morning in every member country
    on_day = swe.julday(y, m, d, 6.0)
    js = run_js(
        "const cal = C.CALENDARS.find((c) => c.id === args[0]);"
        "console.log(JSON.stringify([cal.year(args[1]), cal.year(args[1] - 1)]));",
        cal_id, on_day,
    )
    assert js[0] == label
    assert js[1] != label, "the previous day should still be in the old year"


@pytest.mark.parametrize(
    ("date", "animal_year"),
    [((2023, 1, 22), 2023), ((2024, 2, 10), 2024), ((2025, 1, 29), 2025), ((2026, 2, 17), 2026), ((1985, 2, 20), 1985), ((2033, 1, 31), 2033)],
)
def test_chinese_new_year_dates(date, animal_year):
    y, m, d = date
    js = run_js("console.log(JSON.stringify(C.chinese(args[0])));", swe.julday(y, m, d, 6.0))
    assert js["cyear"] == animal_year
    assert (js["month"]["num"], js["month"]["leap"], js["day"]) == (1, False, 1)


def test_tabular_hijri_and_kalhana_synchronism():
    js = run_js(
        "const [ramadan, kalhana] = args;"
        "const sap = C.CALENDARS.find((c) => c.id === 'in-saptarishi'), sh = C.CALENDARS.find((c) => c.id === 'in-shaka');"
        "console.log(JSON.stringify([C.hijri(ramadan, 5), sap.year(kalhana), sh.year(kalhana)]));",
        swe.julday(2024, 3, 11, 6.0),
        swe.julday(1148, 7, 1, 6.0, swe.JUL_CAL),
    )
    assert js[0] == {"y": 1445, "m": 9, "d": 1}
    # Rajatarangini I.52: Laukika year 4224 = Shaka 1070
    assert js[1:] == ["Saptarishi 4224", "Shaka 1070"]
