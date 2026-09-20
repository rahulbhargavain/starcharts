from datetime import datetime, timezone

from starcharts.ascendant import ascendant_position, local_noon_jd_ut
from starcharts.constraints import AscendantConstraint
from starcharts.ephemeris import to_julian_day_ut


def test_ascendant_position_is_well_formed():
    jd = to_julian_day_ut(datetime(2024, 1, 1, 6, 30, tzinfo=timezone.utc))
    position = ascendant_position(jd, 26.8, 82.2)
    assert 0.0 <= position.sidereal_longitude < 360.0
    assert 0.0 <= position.tropical_longitude < 360.0


def test_ascendant_changes_fast_across_a_few_hours():
    jd = to_julian_day_ut(datetime(2024, 1, 1, 0, 0, tzinfo=timezone.utc))
    p1 = ascendant_position(jd, 26.8, 82.2)
    p2 = ascendant_position(jd + 6.0 / 24.0, 26.8, 82.2)
    # In 6 hours the ascendant should have moved roughly 90 degrees
    # (~2h/rashi), nowhere near a graha's daily motion.
    diff = abs((p2.sidereal_longitude - p1.sidereal_longitude + 180.0) % 360.0 - 180.0)
    assert 60.0 < diff < 120.0


def test_local_noon_jd_ut_is_before_utc_noon_for_eastern_longitude():
    # East of Greenwich, local noon happens before UTC noon on the same
    # calendar date.
    jd_noon_east = local_noon_jd_ut(2024, 1, 1, longitude=82.2)
    jd_utc_noon = to_julian_day_ut(datetime(2024, 1, 1, 12, 0, tzinfo=timezone.utc))
    assert jd_noon_east < jd_utc_noon


def test_ascendant_constraint_matches_a_known_instant():
    jd = to_julian_day_ut(datetime(2024, 1, 1, 6, 30, tzinfo=timezone.utc))
    position = ascendant_position(jd, 26.8, 82.2)
    from starcharts.rashi import to_rashi

    rashi = to_rashi(position.sidereal_longitude)
    constraint = AscendantConstraint(26.8, 82.2, rashi.index, tolerance_degrees=0.1)
    from starcharts.ayanamsha import DEFAULT_AYANAMSHA

    assert constraint.is_satisfied(jd, DEFAULT_AYANAMSHA)
    assert constraint.score(jd, DEFAULT_AYANAMSHA) == 1.0
