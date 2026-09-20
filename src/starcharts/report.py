"""Reporting layer: turn a raw CandidateMatch into a human-checkable report.

Every date this project produces needs three things attached before it's
fit to show anyone: what the sky actually looked like (full chart, not
just the constrained grahas), how well each constraint actually matched
(exact vs only-within-tolerance), and how much the answer would change
under a different ayanamsha. Skipping any of the three is exactly the
overclaiming this project has been trying not to do (see WORKPLAN.md).
"""

from dataclasses import dataclass

import swisseph as swe

from starcharts.ayanamsha import Ayanamsha
from starcharts.chart import GrahaPlacement, compute_chart_at_jd
from starcharts.constraints import Constraint
from starcharts.engine import CandidateMatch, SearchProfile
from starcharts.masa import Masa, masa_at
from starcharts.panchanga import Tithi, tithi_at

_WEEKDAYS = ("Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday")
_MONTHS = (
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
)


def format_astronomical_date(jd_ut: float) -> str:
    """Proleptic Gregorian date + weekday, with year given in astronomical
    numbering translated to BCE/CE (year 0 = 1 BCE)."""
    year, month, day, _hour = swe.revjul(jd_ut, swe.GREG_CAL)
    weekday = _WEEKDAYS[swe.day_of_week(jd_ut)]
    month_name = _MONTHS[month - 1]
    if year <= 0:
        return f"{weekday}, {day:02d} {month_name} {1 - year} BCE"
    return f"{weekday}, {day:02d} {month_name} {year} CE"


@dataclass(frozen=True)
class ConstraintMatchDetail:
    constraint: Constraint
    score: float
    exact_match: bool  # satisfied with zero tolerance, i.e. inside the arc itself
    within_tolerance: bool  # satisfied only once tolerance padding is applied


@dataclass(frozen=True)
class AyanamshaComparison:
    ayanamsha: Ayanamsha
    ayanamsha_degrees: float
    chart: dict[str, GrahaPlacement]


@dataclass(frozen=True)
class CandidateReport:
    jd_ut: float
    date_label: str
    chart: dict[str, GrahaPlacement]
    tithi: Tithi
    masa: Masa
    combined_score: float
    constraint_details: tuple[ConstraintMatchDetail, ...]
    ayanamsha_sensitivity: tuple[AyanamshaComparison, ...]


def _zero_tolerance_copy(constraint: Constraint) -> Constraint:
    """Same constraint with tolerance_degrees forced to 0, to test an
    exact (unpadded) match separately from a tolerance-assisted one."""
    if hasattr(constraint, "tolerance_degrees"):
        return constraint.__class__(
            **{**constraint.__dict__, "tolerance_degrees": 0.0}
        )
    return constraint


def _constraint_detail(
    constraint: Constraint, jd_ut: float, ayanamsha: Ayanamsha
) -> ConstraintMatchDetail:
    score = constraint.score(jd_ut, ayanamsha)
    within_tolerance = constraint.is_satisfied(jd_ut, ayanamsha)
    exact_constraint = _zero_tolerance_copy(constraint)
    exact_match = exact_constraint.is_satisfied(jd_ut, ayanamsha)
    return ConstraintMatchDetail(
        constraint=constraint,
        score=score,
        exact_match=exact_match,
        within_tolerance=within_tolerance,
    )


def generate_report(
    candidate: CandidateMatch,
    profile: SearchProfile,
    ayanamsha_comparisons: tuple[Ayanamsha, ...] = (
        Ayanamsha.LAHIRI,
        Ayanamsha.RAMAN,
        Ayanamsha.KRISHNAMURTI,
        Ayanamsha.FAGAN_BRADLEY,
        Ayanamsha.TRUE_CITRA,
    ),
) -> CandidateReport:
    """Build a full report for one candidate: complete chart, tithi/masa,
    per-constraint match detail, and cross-ayanamsha sensitivity."""
    jd_ut = candidate.jd_ut
    chart = compute_chart_at_jd(jd_ut, ayanamsha=profile.ayanamsha)
    tithi = tithi_at(jd_ut)
    masa = masa_at(jd_ut, ayanamsha=profile.ayanamsha)

    constraint_details = tuple(
        _constraint_detail(c, jd_ut, profile.ayanamsha) for c in profile.constraints
    )

    sensitivity = tuple(
        AyanamshaComparison(
            ayanamsha=ayanamsha,
            ayanamsha_degrees=_ayanamsha_degrees_for(jd_ut, ayanamsha),
            chart=compute_chart_at_jd(jd_ut, ayanamsha=ayanamsha),
        )
        for ayanamsha in ayanamsha_comparisons
    )

    return CandidateReport(
        jd_ut=jd_ut,
        date_label=format_astronomical_date(jd_ut),
        chart=chart,
        tithi=tithi,
        masa=masa,
        combined_score=candidate.score,
        constraint_details=constraint_details,
        ayanamsha_sensitivity=sensitivity,
    )


def _ayanamsha_degrees_for(jd_ut: float, ayanamsha: Ayanamsha) -> float:
    swe.set_sid_mode(ayanamsha.value)
    return swe.get_ayanamsa_ut(jd_ut)


def generate_reports(
    matches: list[CandidateMatch], profile: SearchProfile, top_n: int = 10
) -> list[CandidateReport]:
    """Reports for the top_n highest-scoring candidates (matches is assumed
    already sorted best-first, as engine.search() returns it)."""
    return [generate_report(candidate, profile) for candidate in matches[:top_n]]


def format_report_text(report: CandidateReport) -> str:
    """Render a CandidateReport as plain, human-readable text."""
    lines = [
        f"Candidate: {report.date_label}  (JD {report.jd_ut:.3f})",
        f"Combined score: {report.combined_score:.3f}",
        "",
        "Full chart:",
    ]
    for graha, placement in report.chart.items():
        retro = " (vakri/retrograde)" if placement.position.retrograde else ""
        lines.append(
            f"  {graha:8s} {placement.rashi.name:10s} {placement.rashi.degree_in_rashi:5.2f}deg  "
            f"{placement.nakshatra.name} pada {placement.nakshatra.pada}{retro}"
        )
    lines.append("")
    lines.append(
        f"Tithi: {report.tithi.paksha} {report.tithi.tithi_in_paksha} "
        f"(number {report.tithi.number})"
    )
    lines.append(
        f"Masa (best-effort, modern amanta convention -- see WORKPLAN.md): "
        f"{report.masa.name}{' (adhika)' if report.masa.is_adhika else ''}"
    )
    lines.append("")
    lines.append("Constraint match detail:")
    for detail in report.constraint_details:
        status = "exact" if detail.exact_match else (
            "within tolerance" if detail.within_tolerance else "NOT satisfied"
        )
        lines.append(f"  {detail.constraint}: score={detail.score:.3f} ({status})")
    lines.append("")
    lines.append("Ayanamsha sensitivity (same instant, different ayanamsha):")
    for comparison in report.ayanamsha_sensitivity:
        rashi_summary = ", ".join(
            f"{g}={p.rashi.name}" for g, p in comparison.chart.items()
        )
        lines.append(
            f"  {comparison.ayanamsha.name:14s} (offset {comparison.ayanamsha_degrees:6.2f} deg): "
            f"{rashi_summary}"
        )
    return "\n".join(lines)
