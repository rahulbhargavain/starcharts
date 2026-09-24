"""Regression tests for adhika/kshaya masa naming, find_tithi_jd_near
landing in the requested tithi, and ephemeris-model labelling -- checked
against published calendars and by brute force over many months/trials."""

import random

import pytest
import swisseph as swe

from starcharts.calendar import find_calendar_dates, find_tithi_jd_near
from starcharts.eclipses import find_eclipses_in_range
from starcharts.ephemeris import EPHE_DIR, graha_position, model_from_flags
from starcharts.masa import MASA_NAMES, masa_at
from starcharts.panchanga import tithi_at



def _months(start_year, end_year):
    """Every consecutive amanta month from start_year to end_year."""
    months = []
    jd, end = swe.julday(start_year, 1, 1), swe.julday(end_year, 1, 1)
    while jd < end:
        masa = masa_at(jd)
        months.append(masa)
        jd = masa.amavasya_end_jd + 0.5
    return months


# --- adhika / kshaya naming ----------------------------------------------------

@pytest.mark.parametrize(
    "date, published_name",
    [
        # Mid-month dates inside each year's adhika month, per published
        # Panchangs. The old code named each one after the PREVIOUS month.
        ((2015, 7, 1), "Ashadha"),
        ((2018, 5, 30), "Jyeshtha"),
        ((2020, 10, 1), "Ashwin"),
        ((2023, 8, 1), "Shravana"),
        ((2026, 6, 1), "Jyeshtha"),
    ],
)
def test_adhika_month_matches_published_panchang(date, published_name):
    masa = masa_at(swe.julday(*date))
    assert masa.is_adhika
    assert masa.name == published_name
    following = masa_at(masa.amavasya_end_jd + 1.0)
    assert not following.is_adhika
    assert following.name == published_name  # Adhika X is followed by Nija X


def test_month_names_follow_the_adhika_and_kshaya_rules_1900_2100():
    """Brute force over every lunar month for 200 years: an adhika month
    shares its name with the next month; otherwise each month advances the
    name by one, or by two after a kshaya month (one name is skipped)."""
    months = _months(1900, 2100)
    assert len(months) > 2400
    adhika = [m for m in months if m.is_adhika]
    assert 60 <= len(adhika) <= 85  # ~7 per 19 years
    for prev, nxt in zip(months, months[1:], strict=False):
        step = (MASA_NAMES.index(nxt.name) - MASA_NAMES.index(prev.name)) % 12
        if prev.is_adhika:
            # Shares its name with the following month -- the first of the
            # two names when that month is kshaya (as in 1963).
            following_names = (nxt.kshaya_other_name,) if nxt.is_kshaya else (nxt.name,)
            assert prev.name in following_names and not nxt.is_adhika, (
                swe.revjul(prev.amavasya_start_jd), prev.name, nxt.name)
        elif nxt.is_kshaya:
            assert step == 2, (swe.revjul(nxt.amavasya_start_jd), prev.name, nxt.name)
        else:
            assert step == 1, (swe.revjul(prev.amavasya_start_jd), prev.name, nxt.name)


def test_kshaya_months_are_flagged_with_both_names():
    kshaya = [m for m in _months(1900, 2200) if m.is_kshaya]
    assert [swe.revjul(m.amavasya_start_jd)[0] for m in kshaya] == [1963, 1983, 2123]
    for m in kshaya:
        other = MASA_NAMES.index(m.kshaya_other_name)
        assert MASA_NAMES[(other + 1) % 12] == m.name
        assert not m.is_adhika


def test_find_calendar_dates_matches_either_name_of_a_kshaya_month():
    kshaya = next(m for m in _months(1982, 1984) if m.is_kshaya)
    mid = (kshaya.amavasya_start_jd + kshaya.amavasya_end_jd) / 2
    for name in (kshaya.name, kshaya.kshaya_other_name):
        matches = find_calendar_dates(name, "Shukla", 5, mid, window_days=20.0)
        assert any(kshaya.amavasya_start_jd <= m.jd_ut < kshaya.amavasya_end_jd for m in matches), name
        assert all(m.masa_name == name for m in matches)


# --- find_tithi_jd_near --------------------------------------------------------

def test_find_tithi_jd_near_lands_in_the_requested_tithi_brute_force():
    """The old version targeted the tithi's exact start and landed in the
    previous tithi about half the time (205 of 400)."""
    rng = random.Random(0)
    for _ in range(3000):
        tithi = rng.randint(1, 30)
        jd = find_tithi_jd_near(swe.julday(-2900, 1, 1) + rng.uniform(0, 5800 * 365.25), tithi)
        assert tithi_at(jd).number == tithi


def test_find_calendar_dates_confirms_the_requested_tithi():
    for match in find_calendar_dates("Chaitra", "Shukla", 1, swe.julday(2024, 4, 9), window_days=400.0):
        assert match.tithi_number == 1


# --- ephemeris-model labels ----------------------------------------------------

@pytest.mark.skipif(
    any(EPHE_DIR.glob("sepl_*.se1")), reason="CE-era data files are installed, so no fallback happens"
)
def test_swieph_request_without_data_files_is_labelled_moshier():
    """swisseph silently substitutes Moshier when no data file covers the
    date; the old code labelled the result "swieph" regardless."""
    position = graha_position(swe.julday(2024, 1, 1), swe.MARS, use_moshier=False)
    assert position.ephemeris_model == "moshier"


@pytest.mark.parametrize("year", [pytest.param(-4000, marks=pytest.mark.ephe_data), -2500, 2024])
def test_position_label_matches_swisseph_return_flags(year):
    jd = swe.julday(year, 1, 1)
    for use_moshier in (True, False):
        position = graha_position(jd, swe.MARS, use_moshier=use_moshier)
        flag = swe.FLG_MOSEPH if (use_moshier and year > -3000) else swe.FLG_SWIEPH
        _xx, returned = swe.calc_ut(jd, swe.MARS, flag | swe.FLG_SPEED | swe.FLG_SIDEREAL)
        assert position.ephemeris_model == model_from_flags(returned)


def test_eclipses_report_the_model_actually_used():
    eclipses = find_eclipses_in_range(swe.julday(2024, 1, 1), swe.julday(2025, 1, 1))
    assert eclipses
    for eclipse in eclipses:
        _xx, returned = swe.calc_ut(eclipse.jd_max, swe.MOON, swe.FLG_SWIEPH)
        assert eclipse.ephemeris_model == model_from_flags(returned)
