"""Ayanamsha (precession offset) selection.

Different Vedic astrology traditions assume different tropical->sidereal
offsets. This must stay a configurable parameter throughout the project:
picking a different ayanamsha shifts every downstream rashi/nakshatra result,
and shifts final dating answers by a non-trivial amount.
"""

from enum import Enum

import swisseph as swe


class Ayanamsha(Enum):
    LAHIRI = swe.SIDM_LAHIRI
    RAMAN = swe.SIDM_RAMAN
    KRISHNAMURTI = swe.SIDM_KRISHNAMURTI
    FAGAN_BRADLEY = swe.SIDM_FAGAN_BRADLEY
    # "True" star-anchored modes: these track a real fixed star's measured
    # position (with its own proper motion) rather than a polynomial/linear
    # precession-rate fit calibrated for the last few centuries. Prefer
    # these over LAHIRI/RAMAN/KRISHNAMURTI/FAGAN_BRADLEY for anything
    # earlier than ~1000 BCE -- see the ayanamsha caveat in WORKPLAN.md.
    TRUE_CITRA = swe.SIDM_TRUE_CITRA
    TRUE_REVATI = swe.SIDM_TRUE_REVATI
    TRUE_MULA = swe.SIDM_TRUE_MULA
    TRUE_PUSHYA = swe.SIDM_TRUE_PUSHYA


DEFAULT_AYANAMSHA = Ayanamsha.LAHIRI


def ayanamsha_degrees(jd_ut: float, mode: Ayanamsha = DEFAULT_AYANAMSHA) -> float:
    """Return the ayanamsha offset (degrees) for a given Julian day (UT)."""
    swe.set_sid_mode(mode.value)
    return swe.get_ayanamsa_ut(jd_ut)
