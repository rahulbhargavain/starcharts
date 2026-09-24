from datetime import datetime, timezone

import pytest
import swisseph as swe

from starcharts.ayanamsha import Ayanamsha, ayanamsha_degrees
from starcharts.chart import compute_chart, compute_chart_astro
from starcharts.constants import GRAHAS, NAKSHATRAS, RASHIS
from starcharts.ephemeris import to_julian_day_ut


def test_ayanamsha_lahiri_is_in_expected_modern_range():
    # Lahiri ayanamsha for "now" is well documented to sit around 24 degrees.
    jd_now = to_julian_day_ut(datetime(2024, 1, 1, tzinfo=timezone.utc))
    value = ayanamsha_degrees(jd_now, Ayanamsha.LAHIRI)
    assert 23.0 < value < 25.0


def test_ayanamsha_grows_going_back_in_time():
    # Precession is monotonic on human timescales: further back, smaller
    # (eventually negative) ayanamsha for a fixed sidereal reference frame.
    jd_now = to_julian_day_ut(datetime(2024, 1, 1, tzinfo=timezone.utc))
    jd_past = to_julian_day_ut(datetime(1024, 1, 1, tzinfo=timezone.utc))
    now_value = ayanamsha_degrees(jd_now, Ayanamsha.LAHIRI)
    past_value = ayanamsha_degrees(jd_past, Ayanamsha.LAHIRI)
    assert past_value < now_value


def test_compute_chart_covers_all_seven_grahas():
    chart = compute_chart(datetime(2024, 1, 1, tzinfo=timezone.utc))
    assert set(chart.keys()) == set(GRAHAS.keys())


def test_rashi_and_nakshatra_placements_are_well_formed():
    chart = compute_chart(datetime(2024, 1, 1, tzinfo=timezone.utc))
    for placement in chart.values():
        assert placement.rashi.name in RASHIS
        assert 0.0 <= placement.rashi.degree_in_rashi < 30.0
        assert placement.nakshatra.name in NAKSHATRAS
        assert 1 <= placement.nakshatra.pada <= 4


def test_different_ayanamsha_choices_shift_the_rashi_boundary():
    dt = datetime(2024, 1, 1, tzinfo=timezone.utc)
    lahiri_chart = compute_chart(dt, ayanamsha=Ayanamsha.LAHIRI)
    raman_chart = compute_chart(dt, ayanamsha=Ayanamsha.RAMAN)
    lahiri_lon = lahiri_chart["Surya"].position.sidereal_longitude
    raman_lon = raman_chart["Surya"].position.sidereal_longitude
    assert lahiri_lon != pytest.approx(raman_lon, abs=1e-6)


def test_ancient_bce_date_within_moshier_range_does_not_crash():
    # Astronomical year -3000 (3001 BCE) sits inside Moshier's valid window
    # (~3002 BCE .. 3003 CE per swisseph's own reported bounds).
    chart = compute_chart_astro(-3000, 6, 1, proleptic_julian_calendar=True)
    assert len(chart) == 7


@pytest.mark.ephe_data
def test_dates_older_than_moshier_range_fall_back_to_swieph_data_files():
    # The traditional Kali Yuga epoch (3102 BCE, astronomical year -3101)
    # falls just outside Moshier's ~3002 BCE lower bound, but graha_position
    # auto-falls-back to the full Swiss Ephemeris data files in ephe/ for
    # any date those files actually cover (currently ~5400-2400 BCE).
    chart = compute_chart_astro(-3101, 1, 1, proleptic_julian_calendar=True)
    assert len(chart) == 7
    assert all(p.position.ephemeris_model == "swieph" for p in chart.values())


def test_dates_beyond_downloaded_swieph_files_raise_a_clear_error():
    # Nothing currently downloaded into ephe/ covers this far back (see
    # ephe/README.md) -- confirms the fallback doesn't silently swallow a
    # genuinely-out-of-range request.
    with pytest.raises(swe.Error):
        compute_chart_astro(-6500, 1, 1, proleptic_julian_calendar=True)
