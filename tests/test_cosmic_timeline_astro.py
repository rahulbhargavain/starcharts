"""Check the cosmic-timeline demo's in-browser ephemeris against swisseph.

The demo computes graha positions in JavaScript (demo/cosmic_timeline/astro.js)
so it can animate without shipping precomputed data. This pins its accuracy
to the Swiss Ephemeris over the Moshier range; skipped when node is absent.
"""

import json
import shutil
import subprocess
from pathlib import Path

import pytest
import swisseph as swe

ASTRO_JS = Path(__file__).resolve().parent.parent / "demo" / "cosmic_timeline" / "astro.js"

BODIES = {
    "Surya": swe.SUN,
    "Chandra": swe.MOON,
    "Mangala": swe.MARS,
    "Budha": swe.MERCURY,
    "Guru": swe.JUPITER,
    "Shukra": swe.VENUS,
    "Shani": swe.SATURN,
    "Rahu": swe.MEAN_NODE,
}
TOLERANCE_DEG = 0.75


@pytest.mark.skipif(shutil.which("node") is None, reason="node not installed")
def test_js_ephemeris_matches_swisseph_sidereal_lahiri():
    jds = [swe.julday(year, 3, 1, 12.0) for year in range(-3000, 2101, 125)]
    script = (
        "const A = require(process.argv[1]);"
        "const jds = JSON.parse(process.argv[2]);"
        "console.log(JSON.stringify(jds.map((j) => A.grahas(j))));"
    )
    out = subprocess.run(
        ["node", "-e", script, str(ASTRO_JS), json.dumps(jds)],
        capture_output=True, text=True, check=True,
    ).stdout
    js_positions = json.loads(out)

    swe.set_sid_mode(swe.SIDM_LAHIRI)
    for jd, js in zip(jds, js_positions, strict=True):
        for name, body in BODIES.items():
            xx, _ = swe.calc_ut(jd, body, swe.FLG_MOSEPH | swe.FLG_SIDEREAL)
            diff = abs((js[name] - xx[0] + 540) % 360 - 180)
            assert diff < TOLERANCE_DEG, f"{name} off by {diff:.2f} deg at JD {jd}"
        assert abs((js["Ketu"] - js["Rahu"]) % 360 - 180) < 1e-9


@pytest.mark.skipif(shutil.which("node") is None, reason="node not installed")
def test_js_calendar_round_trips_across_julian_gregorian_switch():
    script = (
        "const A = require(process.argv[1]);"
        "const cases = [[-3101, 2, 18], [-584, 5, 28], [1582, 10, 4], [1582, 10, 15], [1969, 7, 20]];"
        "console.log(JSON.stringify(cases.map(([y, m, d]) => {"
        "  const jd = A.calendarToJd(y, m, d); const c = A.jdToCalendar(jd);"
        "  return [jd, c.year, c.month, c.day]; })));"
    )
    out = subprocess.run(
        ["node", "-e", script, str(ASTRO_JS)], capture_output=True, text=True, check=True
    ).stdout
    results = json.loads(out)
    expected = [(-3101, 2, 18, swe.JUL_CAL), (-584, 5, 28, swe.JUL_CAL),
                (1582, 10, 4, swe.JUL_CAL), (1582, 10, 15, swe.GREG_CAL), (1969, 7, 20, swe.GREG_CAL)]
    for (jd, y, m, d), (ey, em, ed, cal) in zip(results, expected, strict=True):
        assert (y, m, d) == (ey, em, ed)
        assert jd == pytest.approx(swe.julday(ey, em, ed, 0.0, cal))
