"""Fixed reference data: grahas, rashis, nakshatras."""

import swisseph as swe

# The seven classical grahas (naked-eye bodies only; Rahu/Ketu are computed
# nodes, not physical bodies, and are handled separately when needed).
GRAHAS: dict[str, int] = {
    "Surya": swe.SUN,
    "Chandra": swe.MOON,
    "Mangala": swe.MARS,
    "Budha": swe.MERCURY,
    "Guru": swe.JUPITER,
    "Shukra": swe.VENUS,
    "Shani": swe.SATURN,
}

# Sidereal rashis (signs), 30 degrees each, starting at Mesha (Aries).
RASHIS: tuple[str, ...] = (
    "Mesha",
    "Vrishabha",
    "Mithuna",
    "Karka",
    "Simha",
    "Kanya",
    "Tula",
    "Vrischika",
    "Dhanu",
    "Makara",
    "Kumbha",
    "Meena",
)

# 27 nakshatras, 13d20m each, starting at Ashwini (0 degrees sidereal).
NAKSHATRAS: tuple[str, ...] = (
    "Ashwini",
    "Bharani",
    "Krittika",
    "Rohini",
    "Mrigashira",
    "Ardra",
    "Punarvasu",
    "Pushya",
    "Ashlesha",
    "Magha",
    "Purva Phalguni",
    "Uttara Phalguni",
    "Hasta",
    "Chitra",
    "Swati",
    "Vishakha",
    "Anuradha",
    "Jyeshtha",
    "Mula",
    "Purva Ashadha",
    "Uttara Ashadha",
    "Shravana",
    "Dhanishta",
    "Shatabhisha",
    "Purva Bhadrapada",
    "Uttara Bhadrapada",
    "Revati",
)

RASHI_ARC_DEGREES = 30.0
NAKSHATRA_ARC_DEGREES = 360.0 / 27.0
PADA_ARC_DEGREES = NAKSHATRA_ARC_DEGREES / 4.0
