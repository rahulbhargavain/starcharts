"""Amanta lunar month (masa) lookup -- best-effort, modern-convention only.

CAVEAT (see WORKPLAN.md): this uses the *modern* amanta rule -- a masa
takes the name of the sidereal rashi the Sun occupies at the Amavasya that
starts it, and it's "adhika" (intercalary) if the Sun doesn't change rashi
before the next Amavasya. That rule postdates the Siddhantic calendrical
reforms (~5th century CE, Aryabhata/Varahamihira). Earlier intercalation
(e.g. Vedanga Jyotisha's 5-year yuga cycle) used different, mean-motion-
based rules. Treat a masa/paksha name match on a pre-500 CE candidate as
corroborating evidence only, never as a hard filter -- tithi and nakshatra
are the geometric constraints worth trusting that far back, because they
are direct angular measurements with no calendar-rule ambiguity.
"""

from dataclasses import dataclass

from starcharts.ayanamsha import DEFAULT_AYANAMSHA, Ayanamsha
from starcharts.constants import GRAHAS
from starcharts.ephemeris import graha_position
from starcharts.panchanga import moon_sun_elongation
from starcharts.search import SYNODIC_MONTH_DAYS, find_elongation_crossing

MASA_NAMES = (
    "Chaitra",  # Mesha
    "Vaishakha",  # Vrishabha
    "Jyeshtha",  # Mithuna
    "Ashadha",  # Karka
    "Shravana",  # Simha
    "Bhadrapada",  # Kanya
    "Ashwin",  # Tula
    "Kartika",  # Vrischika
    "Margashirsha",  # Dhanu
    "Pausha",  # Makara
    "Magha",  # Kumbha
    "Phalguna",  # Meena
)


@dataclass(frozen=True)
class Masa:
    name: str
    rashi_index: int
    amavasya_start_jd: float
    amavasya_end_jd: float
    is_adhika: bool


def _sun_rashi_index(jd_ut: float, ayanamsha: Ayanamsha) -> int:
    position = graha_position(jd_ut, GRAHAS["Surya"], ayanamsha=ayanamsha)
    return int(position.sidereal_longitude // 30.0) % 12


def _previous_new_moon(jd_ut: float) -> float:
    elongation = moon_sun_elongation(jd_ut)
    days_since_new = elongation / (360.0 / SYNODIC_MONTH_DAYS)
    return find_elongation_crossing(jd_ut - days_since_new, 0.0)


def masa_at(jd_ut: float, ayanamsha: Ayanamsha = DEFAULT_AYANAMSHA) -> Masa:
    """Determine the amanta lunar month containing jd_ut (modern convention;
    see module caveat above)."""
    start_jd = _previous_new_moon(jd_ut)
    end_jd = find_elongation_crossing(start_jd + SYNODIC_MONTH_DAYS, 0.0)

    start_rashi = _sun_rashi_index(start_jd, ayanamsha)
    end_rashi = _sun_rashi_index(end_jd, ayanamsha)
    is_adhika = start_rashi == end_rashi

    # The masa is named after the rashi the Sun transits INTO during this
    # lunar month (the sankranti falling inside it), not the rashi it
    # starts in -- e.g. the 2024 lunar month from the Apr-9 new moon to
    # the May-8 new moon is Chaitra (Mesha) because the Sun enters Mesha
    # on Apr 14, even though it started the month in Meena. When adhika
    # (no sankranti inside), start_rashi == end_rashi so this is the same
    # either way.
    return Masa(
        name=MASA_NAMES[end_rashi],
        rashi_index=end_rashi,
        amavasya_start_jd=start_jd,
        amavasya_end_jd=end_jd,
        is_adhika=is_adhika,
    )
