"""Text calendar description -> candidate Julian day(s).

Scope note (see WORKPLAN.md "calendar layer" caveat): masa/paksha naming
is reconstructed using the *modern* amanta convention and is only
trustworthy corroborating evidence, not a hard filter, for dates before
~500 CE. Tithi and nakshatra are pure angular measurements (Moon-Sun
elongation; Moon's sidereal longitude) with no calendar-rule ambiguity, so
they stay reliable much further back and should be weighted as the
primary constraints in any search built on top of this module.
"""

from dataclasses import dataclass

from starcharts.ayanamsha import DEFAULT_AYANAMSHA, Ayanamsha
from starcharts.masa import masa_at
from starcharts.panchanga import tithi_at, tithi_number_for
from starcharts.search import SYNODIC_MONTH_DAYS, find_elongation_crossing


@dataclass(frozen=True)
class CalendarMatch:
    jd_ut: float
    masa_name: str
    is_adhika_masa: bool
    tithi_number: int


def find_tithi_jd_near(jd_guess: float, tithi_number: int) -> float:
    """Find a Julian day near jd_guess where the given tithi (1-30) is
    current: the instant the Moon-Sun elongation reaches the MIDDLE of the
    tithi's 12-degree arc. Targeting the arc's start instead landed on the
    boundary itself, where the root-finder's tolerance put the result
    just inside the previous tithi about half the time."""
    target_degrees = (tithi_number - 1) * 12.0 + 6.0
    return find_elongation_crossing(jd_guess, target_degrees)


def find_calendar_dates(
    masa_name: str,
    paksha: str,
    tithi_in_paksha: int,
    approx_jd: float,
    ayanamsha: Ayanamsha = DEFAULT_AYANAMSHA,
    window_days: float = 400.0,
    include_adhika: bool = True,
) -> list[CalendarMatch]:
    """Search within +/- window_days of approx_jd for Julian days whose
    amanta masa name matches masa_name and whose tithi matches
    paksha/tithi_in_paksha.

    Multiple matches are expected and correct: adhika (intercalary) months
    repeat a masa name within the same year, so this returns every
    candidate in the window rather than a single answer.
    """
    target_tithi = tithi_number_for(paksha, tithi_in_paksha)
    matches: list[CalendarMatch] = []

    jd = approx_jd - window_days
    end_jd = approx_jd + window_days
    while jd < end_jd:
        masa = masa_at(jd, ayanamsha=ayanamsha)
        names = (masa.name, masa.kshaya_other_name) if masa.is_kshaya else (masa.name,)
        if masa_name in names and (include_adhika or not masa.is_adhika):
            candidate_jd = find_tithi_jd_near(
                masa.amavasya_start_jd + (target_tithi - 1) * (SYNODIC_MONTH_DAYS / 30.0),
                target_tithi,
            )
            if masa.amavasya_start_jd <= candidate_jd < masa.amavasya_end_jd:
                confirmed_tithi = tithi_at(candidate_jd).number
                matches.append(
                    CalendarMatch(
                        jd_ut=candidate_jd,
                        masa_name=masa_name,
                        is_adhika_masa=masa.is_adhika,
                        tithi_number=confirmed_tithi,
                    )
                )
        # Step just past the boundary: landing exactly on the new-moon
        # instant is ambiguous between "end of this month" and "start of
        # the next", which otherwise stalls masa_at() on the same month.
        jd = masa.amavasya_end_jd + 0.5

    return matches
