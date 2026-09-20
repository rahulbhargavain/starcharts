from datetime import datetime, timezone

import pytest

from starcharts.calendar import find_calendar_dates, find_tithi_jd_near
from starcharts.ephemeris import to_julian_day_ut
from starcharts.masa import masa_at
from starcharts.panchanga import tithi_at, tithi_matches, tithi_number_for
from starcharts.rashi import nakshatra_matches, to_nakshatra
from starcharts.search import find_elongation_crossing


def test_tithi_number_for_round_trips_with_tithi_at():
    for paksha, tithi_in_paksha in [("Shukla", 1), ("Shukla", 15), ("Krishna", 1), ("Krishna", 15)]:
        number = tithi_number_for(paksha, tithi_in_paksha)
        # A JD placed exactly at the arc's center should read back the same tithi.
        target_degrees = (number - 1) * 12.0 + 6.0
        jd = find_elongation_crossing(2451545.0, target_degrees)
        tithi = tithi_at(jd)
        assert tithi.paksha == paksha
        assert tithi.tithi_in_paksha == tithi_in_paksha


def test_tithi_number_for_rejects_bad_input():
    with pytest.raises(ValueError):
        tithi_number_for("Shukla", 0)
    with pytest.raises(ValueError):
        tithi_number_for("Purnima", 1)


def test_new_moon_has_tithi_30_just_before_and_1_just_after():
    new_moon_jd = find_elongation_crossing(2451545.0, 0.0)
    before = tithi_at(new_moon_jd - 0.01)
    after = tithi_at(new_moon_jd + 0.01)
    assert before.number == 30
    assert after.number == 1


def test_tithi_matches_respects_tolerance():
    new_moon_jd = find_elongation_crossing(2451545.0, 0.0)
    # 1 degree past the tithi-1/tithi-2 boundary (12 deg) -> tithi 2, just
    # barely outside tithi 1's padded arc unless tolerance covers it.
    jd_past_boundary = find_elongation_crossing(new_moon_jd + 1.0, 13.0)
    assert not tithi_matches(jd_past_boundary, 1, tolerance_degrees=0.0)
    assert tithi_matches(jd_past_boundary, 1, tolerance_degrees=2.0)


def test_nakshatra_matches_respects_tolerance():
    # Ashwini spans sidereal 0-13.333 degrees; 14 degrees is just outside.
    assert not nakshatra_matches(14.0, 0, tolerance_degrees=0.0)
    assert nakshatra_matches(14.0, 0, tolerance_degrees=1.0)


def test_masa_at_matches_known_panchang_chaitra_shukla_pratipada_2024():
    # Ugadi/Chaitra Shukla Pratipada fell on 2024-04-09 in the published
    # Panchang, even though the Sun was still in Meena (not Mesha) at that
    # new moon -- the Mesha Sankranti didn't happen until 2024-04-14. This
    # is the case that catches the start-vs-end-rashi naming bug.
    jd = to_julian_day_ut(datetime(2024, 4, 9, tzinfo=timezone.utc))
    masa = masa_at(jd)
    tithi = tithi_at(jd)
    assert masa.name == "Chaitra"
    assert tithi.paksha == "Shukla"
    assert tithi.tithi_in_paksha == 1


def test_masa_at_returns_a_valid_month_bracketing_the_query_date():
    jd = to_julian_day_ut(datetime(2024, 4, 15, tzinfo=timezone.utc))
    masa = masa_at(jd)
    assert masa.amavasya_start_jd <= jd < masa.amavasya_end_jd
    assert masa.name in (
        "Chaitra",
        "Vaishakha",
        "Jyeshtha",
        "Ashadha",
        "Shravana",
        "Bhadrapada",
        "Ashwin",
        "Kartika",
        "Margashirsha",
        "Pausha",
        "Magha",
        "Phalguna",
    )


def test_find_calendar_dates_recovers_a_known_month_and_tithi():
    # Anchor near 2024-04-15 (within Chaitra/Vaishakha) and ask for
    # whichever masa/tithi actually occurs there, then confirm the search
    # finds it starting from a rough anchor a week off.
    jd = to_julian_day_ut(datetime(2024, 4, 15, tzinfo=timezone.utc))
    masa = masa_at(jd)
    tithi = tithi_at(jd)

    approx_jd = jd - 7.0  # deliberately imprecise anchor
    matches = find_calendar_dates(
        masa.name, tithi.paksha, tithi.tithi_in_paksha, approx_jd, window_days=45.0
    )
    assert any(abs(m.jd_ut - jd) < 1.0 for m in matches)


def test_find_tithi_jd_near_lands_on_the_requested_tithi():
    approx_jd = to_julian_day_ut(datetime(2024, 1, 1, tzinfo=timezone.utc))
    jd = find_tithi_jd_near(approx_jd, 10)
    assert tithi_at(jd).number == 10
