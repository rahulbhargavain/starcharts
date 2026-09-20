from starcharts.eclipses import find_close_eclipse_pairs, find_eclipses_in_range
from starcharts.ephemeris import to_julian_day_ut_astro


def test_find_eclipses_in_range_returns_alternating_kinds_roughly():
    jd_start = to_julian_day_ut_astro(2020, 1, 1)
    jd_end = to_julian_day_ut_astro(2025, 1, 1)
    eclipses = find_eclipses_in_range(jd_start, jd_end)
    assert len(eclipses) > 5
    assert {"solar", "lunar"} <= {e.kind for e in eclipses}
    # chronologically sorted
    assert all(a.jd_max <= b.jd_max for a, b in zip(eclipses, eclipses[1:]))


def test_close_eclipse_pairs_never_fall_below_the_true_minimum_gap():
    # The minimum possible solar/lunar gap within one eclipse season is
    # ~13.9 days -- a literal "13 days" never occurs. Confirms this
    # isn't an artifact of one particular era.
    jd_start = to_julian_day_ut_astro(1900, 1, 1)
    jd_end = to_julian_day_ut_astro(2100, 1, 1)
    pairs = find_close_eclipse_pairs(jd_start, jd_end, min_gap_days=0.0, max_gap_days=20.0)
    assert min(p.gap_days for p in pairs) > 13.5


def test_close_eclipse_pairs_are_common_not_rare():
    # Roughly one such pair per eclipse season -- should show up most years.
    jd_start = to_julian_day_ut_astro(1700, 1, 1)
    jd_end = to_julian_day_ut_astro(1710, 1, 1)
    pairs = find_close_eclipse_pairs(jd_start, jd_end)
    assert len(pairs) >= 8  # ~10 years, close to one per year
