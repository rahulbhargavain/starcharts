/* Lightweight sidereal ephemeris for the cosmic timeline demo.
 *
 * Planets: JPL "Approximate Positions of the Planets" Keplerian elements
 * (Standish, table 2a, valid 3000 BCE - 3000 CE). Moon: truncated Meeus
 * ch. 47 series. Nodes: mean node. Sidereal longitudes use a Lahiri offset
 * fixed at J2000 applied in the J2000 ecliptic frame, which keeps every
 * graha within ~1 degree of the Swiss Ephemeris over the whole range
 * (checked by tests/test_cosmic_timeline_astro.py). Good enough to watch the
 * sky move; not a substitute for the Python engine when dating anything.
 */
(function (root) {
  "use strict";

  const D2R = Math.PI / 180;
  const J2000 = 2451545.0;
  const LAHIRI_J2000 = 23.857092; // swisseph SIDM_LAHIRI at JD 2451545.0

  const norm = (x) => ((x % 360) + 360) % 360;

  // [a, e, I, L, varpi, Omega] and per-century rates; optional [b, c, s, f].
  const ELEMENTS = {
    Budha: [
      [0.38709843, 0.20563661, 7.00559432, 252.25166724, 77.45771895, 48.33961819],
      [0.0, 0.00002123, -0.00590158, 149472.67486623, 0.1594001, -0.12214182],
    ],
    Shukra: [
      [0.72332102, 0.00676399, 3.39777545, 181.9797085, 131.76755713, 76.67261496],
      [-0.00000026, -0.00005107, 0.00043494, 58517.8156026, 0.05679648, -0.27274174],
    ],
    Earth: [
      [1.00000018, 0.01673163, -0.00054346, 100.46691572, 102.93005885, -5.11260389],
      [-0.00000003, -0.00003661, -0.01337178, 35999.37306329, 0.3179526, -0.24123856],
    ],
    Mangala: [
      [1.52371243, 0.09336511, 1.85181869, -4.56813164, -23.91744784, 49.71320984],
      [0.00000097, 0.00009149, -0.00724757, 19140.29934243, 0.45223625, -0.26852431],
    ],
    Guru: [
      [5.20248019, 0.0485359, 1.29861416, 34.33479152, 14.27495244, 100.29282654],
      [-0.00002864, 0.00018026, -0.00322699, 3034.90371757, 0.18199196, 0.13024619],
      [-0.00012452, 0.0606406, -0.35635438, 38.35125],
    ],
    Shani: [
      [9.54149883, 0.05550825, 2.49424102, 50.07571329, 92.86136063, 113.63998702],
      [-0.00003065, -0.00032044, 0.00451969, 1222.11494724, 0.54179478, -0.25015002],
      [0.00025899, -0.13434469, 0.87320147, 38.35125],
    ],
  };

  function elements(name, T) {
    const [base, rate, extra] = ELEMENTS[name];
    const [a, e, I, L, varpi, Om] = base.map((v, i) => v + rate[i] * T);
    let M = L - varpi;
    if (extra) {
      const [b, c, s, f] = extra;
      M += b * T * T + c * Math.cos(f * T * D2R) + s * Math.sin(f * T * D2R);
    }
    return { a, e, I, varpi, Om, M: ((norm(M) + 180) % 360) - 180 };
  }

  // Position on the orbit at eccentric anomaly E (radians), J2000 ecliptic.
  function orbitPoint({ a, e, I, varpi, Om }, E) {
    const xp = a * (Math.cos(E) - e);
    const yp = a * Math.sqrt(1 - e * e) * Math.sin(E);
    const w = (varpi - Om) * D2R, O = Om * D2R, i = I * D2R;
    const cw = Math.cos(w), sw = Math.sin(w), cO = Math.cos(O), sO = Math.sin(O), ci = Math.cos(i), si = Math.sin(i);
    return [
      (cw * cO - sw * sO * ci) * xp + (-sw * cO - cw * sO * ci) * yp,
      (cw * sO + sw * cO * ci) * xp + (-sw * sO + cw * cO * ci) * yp,
      sw * si * xp + cw * si * yp,
    ];
  }

  function helio(name, T) {
    const el = elements(name, T);
    const Mr = el.M * D2R, e = el.e;
    let E = Mr + e * Math.sin(Mr);
    for (let k = 0; k < 8; k++) {
      const dE = (E - e * Math.sin(E) - Mr) / (1 - e * Math.cos(E));
      E -= dE;
      if (Math.abs(dE) < 1e-10) break;
    }
    return orbitPoint(el, E);
  }

  // Rotate a J2000-ecliptic vector so its longitude reads sidereal (Lahiri).
  const COS_AY = Math.cos(LAHIRI_J2000 * D2R), SIN_AY = Math.sin(LAHIRI_J2000 * D2R);
  const toSidereal = ([x, y, z]) => [x * COS_AY + y * SIN_AY, -x * SIN_AY + y * COS_AY, z];

  // General precession in longitude since J2000 (degrees).
  const precession = (T) => (5028.796195 * T + 1.1054348 * T * T) / 3600;

  // Meeus ch. 47 longitude terms: [D, M, M', F, coeff 1e-6 deg]
  const MOON_TERMS = [
    [0, 0, 1, 0, 6288774], [2, 0, -1, 0, 1274027], [2, 0, 0, 0, 658314], [0, 0, 2, 0, 213618],
    [0, 1, 0, 0, -185116], [0, 0, 0, 2, -114332], [2, 0, -2, 0, 58793], [2, -1, -1, 0, 57066],
    [2, 0, 1, 0, 53322], [2, -1, 0, 0, 45758], [0, 1, -1, 0, -40923], [1, 0, 0, 0, -34720],
    [0, 1, 1, 0, -30383], [2, 0, 0, -2, 15327], [0, 0, 1, 2, -12528], [0, 0, 1, -2, 10980],
    [4, 0, -1, 0, 10675], [0, 0, 3, 0, 10034], [4, 0, -2, 0, 8548], [2, 1, -1, 0, -7888],
    [2, 1, 0, 0, -6766], [1, 0, -1, 0, -5163], [1, 1, 0, 0, 4987], [2, -1, 1, 0, 4036],
    [2, 0, 2, 0, 3994], [4, 0, 0, 0, 3861], [2, 0, -3, 0, 3665], [0, 1, -2, 0, -2689],
  ];

  function moonTropical(T) {
    const T2 = T * T, T3 = T2 * T, T4 = T3 * T;
    const Lp = 218.3164477 + 481267.88123421 * T - 0.0015786 * T2 + T3 / 538841 - T4 / 65194000;
    const D = 297.8501921 + 445267.1114034 * T - 0.0018819 * T2 + T3 / 545868 - T4 / 113065000;
    const M = 357.5291092 + 35999.0502909 * T - 0.0001536 * T2 + T3 / 24490000;
    const Mp = 134.9633964 + 477198.8675055 * T + 0.0087414 * T2 + T3 / 69699 - T4 / 14712000;
    const F = 93.272095 + 483202.0175233 * T - 0.0036539 * T2 - T3 / 3526000 + T4 / 863310000;
    const E = 1 - 0.002516 * T - 0.0000074 * T2;
    let sum = 0;
    for (const [d, m, mp, f, coeff] of MOON_TERMS) {
      const eFactor = m === 0 ? 1 : Math.abs(m) === 1 ? E : E * E;
      sum += coeff * eFactor * Math.sin((d * D + m * M + mp * Mp + f * F) * D2R);
    }
    const A1 = 119.75 + 131.849 * T;
    sum += 3958 * Math.sin(A1 * D2R) + 1962 * Math.sin((Lp - F) * D2R);
    return norm(Lp + sum / 1e6);
  }

  const meanNodeTropical = (T) => norm(125.04452 - 1934.136261 * T + 0.0020708 * T * T);

  // Morrison & Stephenson long-term parabola; seconds. Hours in deep antiquity.
  function deltaTDays(jdUt) {
    const year = 2000 + (jdUt - J2000) / 365.25;
    const u = (year - 1820) / 100;
    return (-20 + 32 * u * u) / 86400;
  }

  function lonOf(v) {
    return norm(Math.atan2(v[1], v[0]) / D2R);
  }

  const GRAHA_ORDER = ["Surya", "Chandra", "Mangala", "Budha", "Guru", "Shukra", "Shani", "Rahu", "Ketu"];

  function siderealAtTT(jdTt) {
    const T = (jdTt - J2000) / 36525;
    const earth = helio("Earth", T);
    const out = { Surya: norm(lonOf(earth) + 180 - LAHIRI_J2000) };
    for (const name of ["Mangala", "Budha", "Guru", "Shukra", "Shani"]) {
      const p = helio(name, T);
      out[name] = norm(lonOf([p[0] - earth[0], p[1] - earth[1], p[2] - earth[2]]) - LAHIRI_J2000);
    }
    const p = precession(T);
    out.Chandra = norm(moonTropical(T) - p - LAHIRI_J2000);
    out.Rahu = norm(meanNodeTropical(T) - p - LAHIRI_J2000);
    out.Ketu = norm(out.Rahu + 180);
    return out;
  }

  /** Sidereal (Lahiri) longitudes of all nine grahas at a UT Julian day. */
  function grahas(jdUt) {
    return siderealAtTT(jdUt + deltaTDays(jdUt));
  }

  const HELIO_BODIES = ["Budha", "Shukra", "Earth", "Mangala", "Guru", "Shani"];

  /** Sun-centred positions (AU) in the sidereal ecliptic frame: x toward 0° Mesha, z to ecliptic north. */
  function heliocentric(jdUt) {
    const T = (jdUt + deltaTDays(jdUt) - J2000) / 36525;
    const out = {};
    for (const name of HELIO_BODIES) out[name] = toSidereal(helio(name, T));
    return out;
  }

  /** n points around a body's current orbital ellipse, same frame as heliocentric(). */
  function orbit(name, jdUt, n = 96) {
    const el = elements(name, (jdUt + deltaTDays(jdUt) - J2000) / 36525);
    const pts = [];
    for (let k = 0; k < n; k++) pts.push(toSidereal(orbitPoint(el, (k / n) * 2 * Math.PI)));
    return pts;
  }

  /** Lahiri ayanamsha (degrees) at a UT Julian day. */
  function ayanamsha(jdUt) {
    return LAHIRI_J2000 + precession((jdUt + deltaTDays(jdUt) - J2000) / 36525);
  }

  // --- calendar (proleptic Julian before 1582-10-15, Gregorian after) ---
  function jdToCalendar(jd) {
    const Z = Math.floor(jd + 0.5), F = jd + 0.5 - Z;
    let A = Z;
    if (Z >= 2299161) {
      const alpha = Math.floor((Z - 1867216.25) / 36524.25);
      A = Z + 1 + alpha - Math.floor(alpha / 4);
    }
    const B = A + 1524, C = Math.floor((B - 122.1) / 365.25), Dd = Math.floor(365.25 * C);
    const E = Math.floor((B - Dd) / 30.6001);
    const day = B - Dd - Math.floor(30.6001 * E) + F;
    const month = E < 14 ? E - 1 : E - 13;
    const year = month > 2 ? C - 4716 : C - 4715; // astronomical numbering
    return { year, month, day: Math.floor(day), frac: day - Math.floor(day) };
  }

  function calendarToJd(year, month, day) {
    let y = year, m = month;
    if (m <= 2) { y -= 1; m += 12; }
    let B = 0;
    if (year > 1582 || (year === 1582 && (month > 10 || (month === 10 && day >= 15)))) {
      const A = Math.floor(y / 100);
      B = 2 - A + Math.floor(A / 4);
    }
    return Math.floor(365.25 * (y + 4716)) + Math.floor(30.6001 * (m + 1)) + day + B - 1524.5;
  }

  /** Historical year (negative = BCE, no year zero) -> JD of 1 Jan (or given month/day). */
  function historicalToJd(y, month = 1, day = 1) {
    return calendarToJd(y < 0 ? y + 1 : y, month, day);
  }

  /** Fractional historical year (for timeline layout) from a JD. */
  function jdToYearFloat(jd) {
    return 2000 + (jd - J2000) / 365.2425;
  }
  function yearFloatToJd(y) {
    return J2000 + (y - 2000) * 365.2425;
  }

  const api = {
    GRAHA_ORDER, HELIO_BODIES, LAHIRI_J2000, grahas, heliocentric, orbit, ayanamsha, deltaTDays,
    jdToCalendar, calendarToJd, historicalToJd, jdToYearFloat, yearFloatToJd, norm,
  };
  if (typeof module !== "undefined" && module.exports) module.exports = api;
  else root.Astro = api;
})(typeof globalThis !== "undefined" ? globalThis : this);
