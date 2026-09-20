from datetime import datetime, timezone

from starcharts.chart import compute_chart
from starcharts.constraints import RashiConstraint, TithiConstraint
from starcharts.engine import SearchProfile, search
from starcharts.ephemeris import to_julian_day_ut
from starcharts.panchanga import tithi_at
from starcharts.report import format_astronomical_date, format_report_text, generate_reports


def _profile_for_known_date(dt):
    chart = compute_chart(dt)
    jd = to_julian_day_ut(dt)
    tithi = tithi_at(jd)
    constraints = tuple(
        RashiConstraint(graha, placement.rashi.index) for graha, placement in chart.items()
    ) + (TithiConstraint(tithi.number, tolerance_degrees=0.5),)
    return SearchProfile(2024, 2024, constraints), jd


def test_format_astronomical_date_handles_ce_and_bce():
    # 2000-01-01 12:00 UT is JD 2451545.0, a well-known reference instant.
    assert "2000 CE" in format_astronomical_date(2451545.0)
    # A date long before 1 CE should render as BCE, not a negative year.
    bce_label = format_astronomical_date(1000000.0)
    assert "BCE" in bce_label
    assert "-" not in bce_label.split("BCE")[0].split()[-1]


def test_generate_reports_covers_top_candidates_with_full_chart():
    dt = datetime(2024, 1, 1, tzinfo=timezone.utc)
    profile, true_jd = _profile_for_known_date(dt)
    matches = search(profile)
    reports = generate_reports(matches, profile, top_n=3)

    assert reports
    best = reports[0]
    assert abs(best.jd_ut - true_jd) < 1.0
    assert set(best.chart.keys()) == {"Surya", "Chandra", "Mangala", "Budha", "Guru", "Shukra", "Shani"}
    assert best.combined_score > 0.99


def test_constraint_details_flag_exact_vs_tolerance_only_matches():
    dt = datetime(2024, 1, 1, tzinfo=timezone.utc)
    chart = compute_chart(dt)
    jd = to_julian_day_ut(dt)
    tithi = tithi_at(jd)
    # One tight (zero-tolerance) constraint and one loose one, both true.
    constraints = (
        RashiConstraint("Surya", chart["Surya"].rashi.index, tolerance_degrees=0.0),
        TithiConstraint(tithi.number, tolerance_degrees=5.0),
    )
    profile = SearchProfile(2024, 2024, constraints)
    matches = search(profile)
    reports = generate_reports(matches, profile, top_n=1)
    details = reports[0].constraint_details
    assert any(d.exact_match for d in details)


def test_ayanamsha_sensitivity_shows_differing_offsets():
    dt = datetime(2024, 1, 1, tzinfo=timezone.utc)
    profile, _true_jd = _profile_for_known_date(dt)
    matches = search(profile)
    reports = generate_reports(matches, profile, top_n=1)
    sensitivity = reports[0].ayanamsha_sensitivity
    offsets = {c.ayanamsha_degrees for c in sensitivity}
    # Different ayanamshas must not all collapse to the same offset.
    assert len(offsets) > 1


def test_format_report_text_is_readable_and_mentions_masa_caveat():
    dt = datetime(2024, 1, 1, tzinfo=timezone.utc)
    profile, _true_jd = _profile_for_known_date(dt)
    matches = search(profile)
    reports = generate_reports(matches, profile, top_n=1)
    text = format_report_text(reports[0])
    assert "Combined score" in text
    assert "best-effort" in text
    assert "Ayanamsha sensitivity" in text
