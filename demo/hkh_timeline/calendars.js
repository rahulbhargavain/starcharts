/* Calendars of the eight ICIMOD member countries, computed in the browser.
 *
 * Astronomical calendars (Indian lunisolar, Bikram Sambat, Nepal Sambat,
 * Bengali solar, Solar Hijri, Chinese) run on astro.js's Sun and Moon, which
 * track the Swiss Ephemeris to ~0.1 degree; the amanta month rule mirrors
 * src/starcharts/masa.py and is checked against it (and against published
 * new-year dates) by tests/test_hkh_calendars.py. Arithmetic calendars
 * (Indian national, Bangla, tabular Hijri, Myanmar Era) are exact to their
 * rules. Day boundaries use each country's standard-time midnight, so a
 * date that falls near a sankranti, new moon or equinox can differ by a day
 * from a printed almanac that uses sunrise or a different ayanamsha.
 *
 * Every calendar carries `from`: the year (CE, astronomical) it came into
 * use. Dates before that are proleptic: counted backwards by rules that
 * nobody was using at the time.
 */
(function (root) {
  "use strict";
  const A = root.Astro || (typeof require !== "undefined" ? require("../cosmic_timeline/astro.js") : null);

  const SYN = 29.530588853;
  const wrap180 = (x) => ((((x % 360) + 540) % 360) - 180);
  const mod = (a, n) => ((a % n) + n) % n;

  // ---------- day numbers (JDN of the civil date at a UTC offset) ----------
  const dayNum = (jd, tz) => Math.floor(jd + 0.5 + tz / 24);
  const dayFrac = (jd, tz) => jd + 0.5 + tz / 24 - dayNum(jd, tz);

  function gregToJdn(y, m, d) {
    const a = Math.floor((14 - m) / 12), yy = y + 4800 - a, mm = m + 12 * a - 3;
    return d + Math.floor((153 * mm + 2) / 5) + 365 * yy + Math.floor(yy / 4) - Math.floor(yy / 100) + Math.floor(yy / 400) - 32045;
  }
  function jdnToGreg(n) {
    const a = n + 32044, b = Math.floor((4 * a + 3) / 146097), c = a - Math.floor((146097 * b) / 4);
    const d = Math.floor((4 * c + 3) / 1461), e = c - Math.floor((1461 * d) / 4), m = Math.floor((5 * e + 2) / 153);
    return { y: 100 * b + d - 4800 + Math.floor(m / 10), m: m + 3 - 12 * Math.floor(m / 10), d: e - Math.floor((153 * m + 2) / 5) + 1 };
  }
  const isGregLeap = (y) => (mod(y, 4) === 0 && mod(y, 100) !== 0) || mod(y, 400) === 0;
  const MONTHS_EN = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
  const ceYear = (y) => (y <= 0 ? `${1 - y} BCE` : `${y} CE`);
  function fmtJdn(n) {
    const c = A.jdToCalendar(n); // Julian before 1582, Gregorian after
    return `${c.day} ${MONTHS_EN[c.month - 1]} ${ceYear(c.year)}`;
  }

  // ---------- Sun, Moon and their events ----------
  const sunSid = (jd) => A.sunMoon(jd).sun;
  const sunTrop = (jd) => A.norm(A.sunMoon(jd).sun + A.ayanamsha(jd));
  function elong(jd) { const { sun, moon } = A.sunMoon(jd); return A.norm(moon - sun); }

  function newMoonNear(jd) {
    let t = jd;
    for (let i = 0; i < 10; i++) {
      const d = wrap180(elong(t));
      t -= d / 12.1907;
      if (Math.abs(d) < 1e-6) break;
    }
    return t;
  }
  function prevNewMoon(jd) {
    let t = newMoonNear(jd - elong(jd) / 12.1907);
    if (t > jd) t = newMoonNear(t - SYN);
    return t;
  }
  // last moment at or before jd when longitude fn(t) crossed `target`
  function lastCrossing(fn, jd, target) {
    let t = jd - A.norm(fn(jd) - target) / 0.98565;
    for (let i = 0; i < 8; i++) {
      const d = wrap180(fn(t) - target);
      t -= d / 0.98565;
      if (Math.abs(d) < 1e-7) break;
    }
    return t;
  }

  // ---------- amanta lunar months (mirrors starcharts.masa) ----------
  const MASA = ["Chaitra", "Vaishakha", "Jyeshtha", "Ashadha", "Shravana", "Bhadrapada", "Ashwin", "Kartika", "Margashirsha", "Pausha", "Magha", "Phalguna"];
  const monthMemo = new Map();
  function monthFromStart(start) {
    const key = Math.round(start * 24);
    let m = monthMemo.get(key);
    if (m) return m;
    const end = newMoonNear(start + SYN);
    const sr = Math.floor(sunSid(start) / 30), er = Math.floor(sunSid(end) / 30);
    const n = mod(er - sr, 12);
    const adhika = n === 0, kshaya = n === 2;
    m = { idx: adhika ? (er + 1) % 12 : er, adhika, kshaya, start, end, prev: null };
    if (monthMemo.size > 4000) monthMemo.clear();
    monthMemo.set(key, m);
    return m;
  }
  const monthAt = (jd) => monthFromStart(prevNewMoon(jd));
  function prevMonth(m) {
    if (!m.prev) m.prev = monthFromStart(newMoonNear(m.start - SYN));
    return m.prev;
  }
  /** Start of the lunisolar year containing jd, for a year beginning with month `firstIdx`. */
  function lunarYearStart(jd, firstIdx) {
    const pos = (m) => mod(m.idx - firstIdx, 12);
    let cur = monthAt(jd);
    for (let i = 0; i < 15; i++) {
      const prev = prevMonth(cur);
      if (pos(prev) > pos(cur)) return cur.start;
      cur = prev;
    }
    return cur.start;
  }
  function tithiAt(jd) {
    const n = Math.floor(elong(jd) / 12) + 1;
    return n <= 15 ? { paksha: "Shukla", n, inPaksha: n } : { paksha: "Krishna", n, inPaksha: n - 15 };
  }
  function lunisolar(jd, firstIdx) {
    const m = monthAt(jd);
    const start = lunarYearStart(jd, firstIdx);
    const year = A.jdToCalendar(start).year; // CE (astronomical) year the lunisolar year began in
    return { month: m, tithi: tithiAt(jd), ceYear: year };
  }

  // ---------- sidereal solar months (Bikram Sambat, Bengali) ----------
  // dayOneOffset 0 (Nepal): the month starts on the civil day containing the
  // sankranti, so look at the Sun at the end of today. 1 (Bengal): it starts
  // the following day, so look at the Sun at the start of today.
  function solarSidereal(jd, tz, dayOneOffset) {
    const today = dayNum(jd, tz);
    const probe = today - 0.5 - tz / 24 + (dayOneOffset === 0 ? 1 - 1e-6 : 0);
    const idx = Math.floor(sunSid(probe) / 30);
    const start = lastCrossing(sunSid, probe, idx * 30);
    const first = dayNum(start, tz) + dayOneOffset;
    const mesha = A.jdToCalendar(start - idx * 30.44 + 3).year;
    return { idx, day: today - first + 1, ceYear: mesha };
  }

  // ---------- Solar Hijri (astronomical Nowruz, Tehran meridian) ----------
  function nowruzJdn(g) {
    const guess = gregToJdn(g, 3, 20);
    const eq = lastCrossing(sunTrop, guess + 3, 0);
    const n = dayNum(eq, 3.5);
    return dayFrac(eq, 3.5) < 0.5 ? n : n + 1;
  }
  const SH_MONTHS = ["Hamal", "Sawr", "Jawza", "Saratan", "Asad", "Sonbola", "Mizan", "Aqrab", "Qaws", "Jadi", "Dalw", "Hut"];
  function solarHijri(jd) {
    const n = dayNum(jd, 4.5), g = jdnToGreg(n).y;
    let nr = nowruzJdn(g), year = g - 621;
    if (n < nr) { nr = nowruzJdn(g - 1); year = g - 622; }
    const doy = n - nr;
    const m = doy < 186 ? Math.floor(doy / 31) : 6 + Math.floor((doy - 186) / 30);
    const d = doy < 186 ? (doy % 31) + 1 : ((doy - 186) % 30) + 1;
    return { year, m, d };
  }

  // ---------- Hijri (tabular civil; real months follow moon sighting) ----------
  const HIJRI_EPOCH = 1948440; // 1 Muharram 1 AH = 16 July 622 (Julian)
  const HIJRI_MONTHS = ["Muharram", "Safar", "Rabi' al-Awwal", "Rabi' al-Thani", "Jumada al-Ula", "Jumada al-Akhirah", "Rajab", "Sha'ban", "Ramadan", "Shawwal", "Dhu al-Qa'dah", "Dhu al-Hijjah"];
  const hijriToJdn = (y, m, d) => d + Math.ceil(29.5 * (m - 1)) + (y - 1) * 354 + Math.floor((3 + 11 * y) / 30) + HIJRI_EPOCH - 1;
  function hijri(jd, tz) {
    const n = dayNum(jd, tz);
    const y = Math.floor((30 * (n - HIJRI_EPOCH) + 10646) / 10631);
    const m = Math.min(12, Math.ceil((n - (29 + hijriToJdn(y, 1, 1))) / 29.5) + 1);
    return { y, m, d: n - hijriToJdn(y, m, 1) + 1 };
  }

  // ---------- Chinese lunisolar (modern rule: Beijing time, true new moons and zhongqi) ----------
  const CN_TZ = 8;
  const chineseMemo = new Map();
  function month11StartDay(g) {
    const ws = lastCrossing(sunTrop, gregToJdn(g, 12, 25), 270);
    const nm = prevNewMoon(ws - dayFrac(ws, CN_TZ) + 1 - 1e-6); // new moon on or before the end of the solstice's Beijing day
    return dayNum(nm, CN_TZ);
  }
  function chineseYearMonths(g) {
    // months from month 11 of Gregorian year g to (not including) month 11 of g+1
    if (chineseMemo.has(g)) return chineseMemo.get(g);
    const a = month11StartDay(g), b = month11StartDay(g + 1);
    const starts = [];
    let nm = newMoonNear(a - CN_TZ / 24); // the new moon that falls on Beijing day a
    for (let s = dayNum(nm, CN_TZ); s < b; ) {
      starts.push(s);
      nm = newMoonNear(nm + SYN);
      s = dayNum(nm, CN_TZ);
    }
    const dayStart = (n) => n - 0.5 - CN_TZ / 24;
    const hasZhongqi = (i) => {
      const s0 = starts[i], s1 = i + 1 < starts.length ? starts[i + 1] : b;
      return Math.floor(sunTrop(dayStart(s0)) / 30) !== Math.floor(sunTrop(dayStart(s1)) / 30);
    };
    const leapYear = starts.length === 13;
    let num = 11, leapUsed = false;
    const months = starts.map((s, i) => {
      if (i === 0) return { start: s, num: 11, leap: false };
      if (leapYear && !leapUsed && !hasZhongqi(i)) { leapUsed = true; return { start: s, num, leap: true }; }
      num = num === 12 ? 1 : num + 1;
      return { start: s, num, leap: false };
    });
    const out = { months, end: b, gYear: jdnToGreg(a).y };
    if (chineseMemo.size > 400) chineseMemo.clear();
    chineseMemo.set(g, out);
    return out;
  }
  const STEMS = ["Jia", "Yi", "Bing", "Ding", "Wu", "Ji", "Geng", "Xin", "Ren", "Gui"];
  const BRANCHES = ["Zi", "Chou", "Yin", "Mao", "Chen", "Si", "Wu", "Wei", "Shen", "You", "Xu", "Hai"];
  const ELEMENTS_CN = ["Wood", "Fire", "Earth", "Metal", "Water"];
  const ANIMALS_CN = ["Rat", "Ox", "Tiger", "Rabbit", "Dragon", "Snake", "Horse", "Goat", "Monkey", "Rooster", "Dog", "Pig"];
  function chinese(jd) {
    const n = dayNum(jd, CN_TZ);
    let g = jdnToGreg(n).y;
    if (n < month11StartDay(g)) g -= 1;
    const yr = chineseYearMonths(g);
    let i = yr.months.length - 1;
    while (i > 0 && yr.months[i].start > n) i--;
    const k1 = yr.months.findIndex((m) => m.num === 1 && !m.leap);
    const cyear = yr.gYear + (k1 >= 0 && i >= k1 ? 1 : 0);
    return { cyear, month: yr.months[i], day: n - yr.months[i].start + 1, newYearJdn: k1 >= 0 ? yr.months[k1].start : null };
  }
  const ganzhi = (y) => ({ stem: mod(y - 4, 10), branch: mod(y - 4, 12) });

  // ---------- Tibetan / Bhutanese years (year-level only) ----------
  // Losar under the Phugpa rules falls between late January and mid-March;
  // month-level Phugpa arithmetic isn't implemented, so dates in that window
  // are reported as ambiguous between the two years.
  const ELEMENTS_BO = ["Wood", "Fire", "Earth", "Iron", "Water"];
  const ANIMALS_BO = ["Mouse", "Ox", "Tiger", "Rabbit", "Dragon", "Snake", "Horse", "Sheep", "Monkey", "Bird", "Dog", "Pig"];
  function tibetanYears(jd) {
    const g = jdnToGreg(dayNum(jd, 6));
    const md = g.m * 100 + g.d;
    return md < 125 ? [g.y - 1] : md > 315 ? [g.y] : [g.y - 1, g.y];
  }
  function tibetanYearName(y) {
    const { stem, branch } = ganzhi(y);
    return `${ELEMENTS_BO[Math.floor(stem / 2)]}-${stem % 2 ? "Female" : "Male"}-${ANIMALS_BO[branch]}`;
  }
  function rabjung(y) {
    const k = y - 1027;
    return k < 0 ? null : { cycle: Math.floor(k / 60) + 1, year: mod(k, 60) + 1 };
  }

  // ---------- Myanmar Era (Thandeikta new-year instants) ----------
  const MM_EPOCH = 1954168.050623, MM_SY = 1577917828 / 4320000;
  const myanmarEra = (jd) => Math.floor((jd - MM_EPOCH) / MM_SY);
  const myanmarNewYear = (me) => MM_EPOCH + me * MM_SY;

  // ---------- Bangla (Bangladesh, revised 2019) and Indian national ----------
  const BANGLA_MONTHS = ["Boishakh", "Joishtho", "Asharh", "Srabon", "Bhadro", "Ashwin", "Kartik", "Ogrohayon", "Poush", "Magh", "Falgun", "Choitro"];
  function bangla(jd) {
    const n = dayNum(jd, 6), g = jdnToGreg(n).y;
    let y0 = n >= gregToJdn(g, 4, 14) ? g : g - 1;
    let doy = n - gregToJdn(y0, 4, 14);
    const lens = [31, 31, 31, 31, 31, 31, 30, 30, 30, 30, isGregLeap(y0 + 1) ? 30 : 29, 30];
    let m = 0;
    while (doy >= lens[m]) { doy -= lens[m]; m++; }
    return { year: y0 - 593, m, d: doy + 1 };
  }
  const NATIONAL_MONTHS = ["Chaitra", "Vaishakha", "Jyaishtha", "Ashadha", "Shravana", "Bhadra", "Ashvina", "Kartika", "Agrahayana", "Pausha", "Magha", "Phalguna"];
  function indianNational(jd) {
    const n = dayNum(jd, 5.5), g = jdnToGreg(n).y;
    const startOf = (y) => gregToJdn(y, 3, isGregLeap(y) ? 21 : 22);
    const y0 = n >= startOf(g) ? g : g - 1;
    let doy = n - startOf(y0);
    const lens = [isGregLeap(y0) ? 31 : 30, 31, 31, 31, 31, 31, 30, 30, 30, 30, 30, 30];
    let m = 0;
    while (doy >= lens[m]) { doy -= lens[m]; m++; }
    return { year: y0 - 78, m, d: doy + 1 };
  }

  // ---------- calendar registry ----------
  const BS_MONTHS = ["Baishakh", "Jestha", "Asar", "Shrawan", "Bhadra", "Asoj", "Kartik", "Mangsir", "Poush", "Magh", "Falgun", "Chaitra"];
  const NS_MONTHS = { 7: "Kachhala", 8: "Thinla", 9: "Pohela", 10: "Sila", 11: "Chilla", 0: "Chaula", 1: "Bachhala", 2: "Tachhala", 3: "Dilla", 4: "Gunla", 5: "Yanla", 6: "Kaula" };
  const BENGALI_IN_MONTHS = ["Boishakh", "Jyoishtho", "Asharh", "Shrabon", "Bhadro", "Ashshin", "Kartik", "Ogrohayon", "Poush", "Magh", "Falgun", "Choitro"];
  const signed = (y, suffix, before) => (y >= 1 ? `${y} ${suffix}` : `${1 - y} ${before}`);

  const lunarLabel = (ls) => `${ls.month.adhika ? "Adhika " : ""}${MASA[ls.month.idx]} ${ls.tithi.paksha} ${ls.tithi.inPaksha}`;

  // Each entry: year(jd) -> year label; full(jd) -> {text, note?}
  const CALENDARS = [
    {
      id: "in-national", country: "IN", name: "Indian national calendar", from: 1957,
      history: "Adopted in 1957; fixed to the Gregorian year. Counts Shaka years.",
      year: (jd) => `Saka ${indianNational(jd).year}`,
      full: (jd) => { const c = indianNational(jd); return { text: `${c.d} ${NATIONAL_MONTHS[c.m]} ${c.year} Saka` }; },
    },
    {
      id: "in-vs", country: "IN", name: "Vikram Samvat (lunisolar)", from: 400, lunar: true,
      history: "Counted as the Krita/Malava era from c. 4th century; called Vikrama from c. 9th. Year starts at Chaitra Shukla 1. Month names amanta.",
      year: (jd) => `VS ${lunisolar(jd, 0).ceYear + 57}`,
      full: (jd) => { const l = lunisolar(jd, 0); return { text: `${lunarLabel(l)}, VS ${l.ceYear + 57}` }; },
    },
    {
      id: "in-shaka", country: "IN", name: "Shaka era (lunisolar)", from: 130, lunar: true,
      history: "In inscriptions from c. 130 CE (Western Kshatrapas); the era of the Siddhantic astronomers.",
      year: (jd) => `Shaka ${lunisolar(jd, 0).ceYear - 78}`,
      full: (jd) => { const l = lunisolar(jd, 0); return { text: `${lunarLabel(l)}, Shaka ${l.ceYear - 78}` }; },
    },
    {
      id: "in-saptarishi", country: "IN", name: "Saptarishi / Laukika (Kashmir)", from: 1148, lunar: true,
      history: "Kashmir's era, used by Kalhana in the Rajatarangini (1148). Year starts at Navreh, Chaitra Shukla 1.",
      year: (jd) => `Saptarishi ${lunisolar(jd, 0).ceYear + 3076}`,
      full: (jd) => { const l = lunisolar(jd, 0); return { text: `${lunarLabel(l)}, Saptarishi ${l.ceYear + 3076}` }; },
    },
    {
      id: "in-bengali", country: "IN", name: "Bengali solar (Darjeeling, NE India)", from: 1584,
      history: "Sidereal solar months; Pohela Boishakh is the day after Mesha sankranti. Bangabda era, dated to Akbar's revenue reform (1584).",
      year: (jd) => `${solarSidereal(jd, 5.5, 1).ceYear - 593} BS (Bangabda)`,
      full: (jd) => { const s = solarSidereal(jd, 5.5, 1); return { text: `${s.day} ${BENGALI_IN_MONTHS[s.idx]} ${s.ceYear - 593} Bangabda`, note: "±1 day" }; },
    },
    {
      id: "in-tibetan", country: "IN", name: "Tibetan (Ladakh, Sikkim, Arunachal)", from: 1027,
      history: "Phugpa calendar; 60-year rabjung cycles counted from 1027.",
      year: (jd) => tibetanYears(jd).map((y) => `${tibetanYearName(y)}`).join(" / "),
      full: (jd) => ({ text: tibetanYears(jd).map((y) => { const r = rabjung(y); return `${tibetanYearName(y)}${r ? ` (rabjung ${r.cycle}.${r.year})` : ""}`; }).join(" or "), note: tibetanYears(jd).length > 1 ? "near Losar" : "" }),
    },
    {
      id: "np-bs", country: "NP", name: "Bikram Sambat (solar)", from: 1901,
      history: "Nepal's official calendar since 1901: sidereal solar months, year from Mesha sankranti.",
      year: (jd) => `${solarSidereal(jd, 5.75, 0).ceYear + 57} BS`,
      full: (jd) => { const s = solarSidereal(jd, 5.75, 0); return { text: `${s.day} ${BS_MONTHS[s.idx]} ${s.ceYear + 57} BS`, note: "±1 day" }; },
    },
    {
      id: "np-ns", country: "NP", name: "Nepal Sambat", from: 879, lunar: true,
      history: "Lunisolar era of the Kathmandu valley from 20 Oct 879; a national calendar again since 2008. Year starts at Kartika Shukla 1.",
      year: (jd) => `NS ${lunisolar(jd, 7).ceYear - 879}`,
      full: (jd) => { const l = lunisolar(jd, 7); return { text: `${l.month.adhika ? "Analā " : ""}${NS_MONTHS[l.month.idx]} ${l.tithi.paksha === "Shukla" ? "Thwa" : "Gā"} ${l.tithi.inPaksha}, NS ${l.ceYear - 879}` }; },
    },
    {
      id: "bt-lunar", country: "BT", name: "Bhutanese lunar calendar", from: 1027,
      history: "Tibetan-derived; years named in the 60-year rabjung cycle counted from 1027.",
      year: (jd) => tibetanYears(jd).map(tibetanYearName).join(" / "),
      full: (jd) => ({ text: tibetanYears(jd).map((y) => { const r = rabjung(y); return `${tibetanYearName(y)}${r ? ` (rabjung ${r.cycle}.${r.year})` : ""}`; }).join(" or "), note: tibetanYears(jd).length > 1 ? "near Losar" : "" }),
    },
    {
      id: "cn-lunisolar", country: "CN", name: "Chinese lunisolar", from: -103,
      history: "Month structure from the Taichu reform (104 BCE); computed with the modern astronomical rules adopted in 1645.",
      year: (jd) => { const c = chinese(jd), g = ganzhi(c.cyear); return `${STEMS[g.stem]}${BRANCHES[g.branch].toLowerCase()} (${ELEMENTS_CN[Math.floor(g.stem / 2)]} ${ANIMALS_CN[g.branch]})`; },
      full: (jd) => { const c = chinese(jd), g = ganzhi(c.cyear); return { text: `${c.month.leap ? "Leap month " : "Month "}${c.month.num}, day ${c.day}, ${STEMS[g.stem]}${BRANCHES[g.branch].toLowerCase()} (${ELEMENTS_CN[Math.floor(g.stem / 2)]} ${ANIMALS_CN[g.branch]}) year` }; },
    },
    {
      id: "cn-tibetan", country: "CN", name: "Tibetan (Bod lo)", from: 1027,
      history: "Tibet's calendar; royal year = CE + 127, rabjung cycles from 1027.",
      year: (jd) => tibetanYears(jd).map((y) => `${y + 127}`).join(" / ") + " Bod lo",
      full: (jd) => ({ text: tibetanYears(jd).map((y) => `${y + 127} (${tibetanYearName(y)})`).join(" or "), note: tibetanYears(jd).length > 1 ? "near Losar" : "" }),
    },
    {
      id: "pk-hijri", country: "PK", name: "Hijri (lunar)", from: 638,
      history: "Islamic lunar calendar, instituted 638. Tabular form; actual months begin on moon sighting and can differ by a day or two.",
      year: (jd) => signed(hijri(jd, 5).y, "AH", "BH"),
      full: (jd) => { const h = hijri(jd, 5); return h.y >= 1 ? { text: `${h.d} ${HIJRI_MONTHS[h.m - 1]} ${h.y} AH`, note: "±1–2 days" } : { text: `${1 - h.y} years before the Hijra` }; },
    },
    {
      id: "af-sh", country: "AF", name: "Solar Hijri", from: 1922,
      history: "Afghanistan's official calendar from 1922, built on the Persian Jalali calendar (1079). Year starts at the March equinox.",
      year: (jd) => signed(solarHijri(jd).year, "SH", "before SH 1"),
      full: (jd) => { const s = solarHijri(jd); return s.year >= 1 ? { text: `${s.d} ${SH_MONTHS[s.m]} ${s.year} SH` } : { text: `${1 - s.year} years before SH 1` }; },
    },
    {
      id: "af-hijri", country: "AF", name: "Hijri (lunar)", from: 638,
      history: "Islamic lunar calendar, instituted 638; tabular form.",
      year: (jd) => signed(hijri(jd, 4.5).y, "AH", "BH"),
      full: (jd) => { const h = hijri(jd, 4.5); return h.y >= 1 ? { text: `${h.d} ${HIJRI_MONTHS[h.m - 1]} ${h.y} AH`, note: "±1–2 days" } : { text: `${1 - h.y} years before the Hijra` }; },
    },
    {
      id: "bd-bangla", country: "BD", name: "Bangla (Bangabda)", from: 1584,
      history: "Bangabda era from 1584; Bangladesh fixed Pohela Boishakh to 14 April (1987, revised 2019).",
      year: (jd) => `${bangla(jd).year} Bangabda`,
      full: (jd) => { const b = bangla(jd); return { text: `${b.d} ${BANGLA_MONTHS[b.m]} ${b.year} Bangabda` }; },
    },
    {
      id: "bd-hijri", country: "BD", name: "Hijri (lunar)", from: 638,
      history: "Islamic lunar calendar, instituted 638; tabular form.",
      year: (jd) => signed(hijri(jd, 6).y, "AH", "BH"),
      full: (jd) => { const h = hijri(jd, 6); return h.y >= 1 ? { text: `${h.d} ${HIJRI_MONTHS[h.m - 1]} ${h.y} AH`, note: "±1–2 days" } : { text: `${1 - h.y} years before the Hijra` }; },
    },
    {
      id: "mm-me", country: "MM", name: "Myanmar calendar (ME)", from: 638,
      history: "Myanmar Era from 638; each year begins at the Thingyan new-year instant in mid-April. Months not computed.",
      year: (jd) => `ME ${myanmarEra(jd)}`,
      full: (jd) => { const me = myanmarEra(jd); return { text: `ME ${me}`, note: `began at Thingyan, ${fmtJdn(dayNum(myanmarNewYear(me), 6.5))}` }; },
    },
  ];

  const COUNTRIES = {
    IN: "India", NP: "Nepal", BT: "Bhutan", CN: "China", PK: "Pakistan", AF: "Afghanistan", BD: "Bangladesh", MM: "Myanmar",
  };

  /** Year label for a whole calendar year (CE astronomical): "a" or "a – b" if it straddles a new year. */
  function yearSpan(cal, ceYearAstro) {
    const j0 = A.calendarToJd(ceYearAstro, 1, 1) + 0.25, j1 = A.calendarToJd(ceYearAstro, 12, 31) + 0.25;
    const a = cal.year(j0), b = cal.year(j1);
    return a === b ? a : `${a} – ${b}`;
  }

  const api = {
    CALENDARS, COUNTRIES, yearSpan, fmtJdn,
    // exposed for tests
    lunisolar, monthAt, tithiAt, solarSidereal, solarHijri, nowruzJdn, hijri, chinese, bangla, indianNational,
    myanmarEra, myanmarNewYear, tibetanYears, tibetanYearName, rabjung, gregToJdn, jdnToGreg, dayNum,
    MASA,
  };
  if (typeof module !== "undefined" && module.exports) module.exports = api;
  else root.Calendars = api;
})(typeof globalThis !== "undefined" ? globalThis : this);
