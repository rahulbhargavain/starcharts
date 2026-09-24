"""EPHE_DIR override, thread safety, SVG escaping, and results staying
inside the requested range."""

import os
import subprocess
import sys
import threading
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone

import pytest
import swisseph as swe

from starcharts.ayanamsha import Ayanamsha
from starcharts import ephemeris
from starcharts.chart import compute_chart
from starcharts.constraints import RashiConstraint, TithiConstraint
from starcharts.eclipses import find_eclipses_in_range
from starcharts.engine import SearchProfile, search
from starcharts.ephemeris import graha_position, to_julian_day_ut_astro
from starcharts.visualize import render_kundali_svg


def test_ephe_dir_can_be_overridden_by_environment(tmp_path):
    """A regular (non-editable) install can't find ephe/ relative to the
    source tree, so STARCHARTS_EPHE_DIR must win -- including for swisseph."""
    env = {**os.environ, "STARCHARTS_EPHE_DIR": str(tmp_path)}
    code = "from starcharts.ephemeris import EPHE_DIR; print(EPHE_DIR)"
    out = subprocess.run([sys.executable, "-c", code], env=env, capture_output=True, text=True, check=True)
    assert out.stdout.strip() == str(tmp_path.resolve())


def test_concurrent_calls_with_different_ayanamshas_match_serial_results():
    """Many threads, mixed ayanamshas: results must equal serial ones."""
    jobs = [
        (swe.julday(1900 + i, 1 + i % 12, 1 + i % 28), body, ayanamsha)
        for i in range(60)
        for body in (swe.SUN, swe.MARS, swe.SATURN)
        for ayanamsha in (Ayanamsha.LAHIRI, Ayanamsha.FAGAN_BRADLEY, Ayanamsha.TRUE_CITRA)
    ]

    def run(job):
        jd, body, ayanamsha = job
        return graha_position(jd, body, ayanamsha=ayanamsha).sidereal_longitude

    serial = [run(job) for job in jobs]
    with ThreadPoolExecutor(max_workers=8) as pool:
        assert list(pool.map(run, jobs)) == serial


def test_another_threads_ayanamsha_cannot_leak_into_a_computation(monkeypatch):
    """Thread A pauses between setting its sidereal mode and computing,
    while thread B runs a different ayanamsha. This is safe only because
    swisseph keeps its settings per thread (thread-local storage) -- within
    one thread the same interleaving would give A Fagan-Bradley's value,
    0.9 deg off. Guards that assumption, which the code relies on instead
    of a lock."""
    jd = swe.julday(2000, 1, 1)
    expected_a = graha_position(jd, swe.MARS, ayanamsha=Ayanamsha.LAHIRI).sidereal_longitude

    a_paused = threading.Event()
    b_done = threading.Event()
    original_calc = ephemeris._calc

    def pausing_calc(jd_ut, body, flags):
        if threading.current_thread().name == "A" and not a_paused.is_set():
            a_paused.set()
            b_done.wait(timeout=0.5)  # returns early only if B was not blocked
        return original_calc(jd_ut, body, flags)

    monkeypatch.setattr(ephemeris, "_calc", pausing_calc)
    result = {}

    def thread_a():
        result["a"] = graha_position(jd, swe.MARS, ayanamsha=Ayanamsha.LAHIRI).sidereal_longitude

    def thread_b():
        a_paused.wait(timeout=5)
        graha_position(jd + 1, swe.MARS, ayanamsha=Ayanamsha.FAGAN_BRADLEY)
        b_done.set()

    threads = [threading.Thread(target=thread_a, name="A"), threading.Thread(target=thread_b, name="B")]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=10)
    assert result["a"] == expected_a


@pytest.mark.ephe_data
def test_deep_history_works_in_worker_threads():
    """swisseph's data-file path is per thread too. Set only at import, it
    was missing in every other thread, so any date needing the data files
    (before ~3000 BCE) failed with "file not found" in a worker thread."""
    jds = [swe.julday(year, 1, 1) for year in (-5000, -4000, -3500)]

    def deep(jd):
        return (
            graha_position(jd, swe.SATURN).sidereal_longitude,
            find_eclipses_in_range(jd, jd + 200)[0].jd_max,
        )

    serial = [deep(jd) for jd in jds]
    with ThreadPoolExecutor(max_workers=3) as pool:
        assert list(pool.map(deep, jds)) == serial


def test_svg_title_is_escaped():
    chart = compute_chart(datetime(2024, 1, 1, tzinfo=timezone.utc))
    svg = render_kundali_svg(chart, title='Rama & Sita <birth> "test"')
    root = ET.fromstring(svg)  # raises if the SVG is not well-formed
    texts = ["".join(t.itertext()) for t in root.iter() if t.tag.endswith("text")]
    assert 'Rama & Sita <birth> "test"' in texts


def test_search_results_stay_inside_the_requested_range():
    """Windows are padded by one sampling step for ranking; the padding
    must not produce candidates outside the requested years."""
    profile = SearchProfile(2024, 2025, (RashiConstraint("Surya", 9, 2.0), TithiConstraint(1, 2.0)))
    matches = search(profile)
    lo = to_julian_day_ut_astro(2024, 1, 1)
    hi = to_julian_day_ut_astro(2025, 12, 31)
    assert matches
    assert all(lo <= m.jd_ut <= hi for m in matches)
