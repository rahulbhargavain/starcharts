"""Amanta lunar month (masa) lookup -- best-effort, modern-convention only.

CAVEAT (see WORKPLAN.md): this uses the *modern* amanta rule -- a masa
takes the name of the sidereal rashi the Sun enters during it (its
sankranti); it's "adhika" (intercalary) if the Sun doesn't change rashi
before the next Amavasya, and then takes the name of the month that
follows it; and it's "kshaya" if the Sun changes rashi twice. That rule postdates the Siddhantic calendrical
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
    # A kshaya month contains two sankrantis, so one month name has no
    # lunar month of its own. Conventions differ on which name the combined
    # month carries; `name` keeps the second sankranti's month and
    # `kshaya_other_name` records the first, so a caller can match either.
    is_kshaya: bool = False
    kshaya_other_name: str | None = None


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
    sankrantis = (end_rashi - start_rashi) % 12
    is_adhika = sankrantis == 0
    is_kshaya = sankrantis == 2

    # A regular masa is named after the rashi the Sun transits INTO during
    # this lunar month (the sankranti falling inside it), not the rashi it
    # starts in -- e.g. the 2024 lunar month from the Apr-9 new moon to
    # the May-8 new moon is Chaitra (Mesha) because the Sun enters Mesha
    # on Apr 14, even though it started the month in Meena.
    #
    # An adhika month has no sankranti inside, and takes the name of the
    # regular month that FOLLOWS it -- the one containing the Sun's entry
    # into the next rashi. E.g. 2023's Jul 18 - Aug 16 month (Sun in Karka
    # throughout) is Adhika Shravana, followed by Nija Shravana with the
    # Simha sankranti -- not "Adhika Ashadha".
    rashi_index = (end_rashi + 1) % 12 if is_adhika else end_rashi
    return Masa(
        name=MASA_NAMES[rashi_index],
        rashi_index=rashi_index,
        amavasya_start_jd=start_jd,
        amavasya_end_jd=end_jd,
        is_adhika=is_adhika,
        is_kshaya=is_kshaya,
        kshaya_other_name=MASA_NAMES[(start_rashi + 1) % 12] if is_kshaya else None,
    )
