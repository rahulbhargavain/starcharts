(function () {
  "use strict";
  const A = window.Astro, C = window.Calendars, H = window.HKH;
  const $ = (id) => document.getElementById(id);
  const TAU = Math.PI * 2;
  const MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
  const COUNTRY_ORDER = ["IN", "NP", "BT", "CN", "PK", "AF", "BD", "MM"];
  const SHORT = {
    "in-national": "Saka (national)", "in-vs": "Vikram Samvat", "in-shaka": "Shaka", "in-saptarishi": "Saptarishi",
    "in-bengali": "Bengali (India)", "in-tibetan": "Tibetan (Ladakh)", "np-bs": "Bikram Sambat", "np-ns": "Nepal Sambat",
    "bt-lunar": "Bhutanese", "cn-lunisolar": "Chinese", "cn-tibetan": "Tibetan", "pk-hijri": "Hijri", "af-sh": "Solar Hijri",
    "af-hijri": "Hijri", "bd-bangla": "Bangla", "bd-hijri": "Hijri", "mm-me": "Myanmar Era",
  };

  const toAstro = (h) => (h < 0 ? h + 1 : h);
  const histLabel = (astro) => (astro <= 0 ? `${1 - astro} BCE` : `${astro} CE`);
  const clamp = (x, lo, hi) => Math.max(lo, Math.min(hi, x));
  const smooth = (x) => x * x * (3 - 2 * x);
  function rgba(hex, a) {
    const n = parseInt(hex.slice(1), 16);
    return `rgba(${(n >> 16) & 255},${(n >> 8) & 255},${n & 255},${a})`;
  }
  const esc = (s) => String(s).replace(/[&<>"]/g, (ch) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" })[ch]);
  function fmtDate(jd) {
    const c = A.jdToCalendar(jd);
    return `${c.day} ${MONTHS[c.month - 1]} ${histLabel(c.year)}`;
  }

  // ---------- time scale: square root of years-before-2040, so recent centuries get room ----------
  const Y_END = 2040;
  const JD_MIN = A.historicalToJd(-7000, 1, 1), JD_MAX = A.historicalToJd(2030, 12, 31);
  const Y_MIN = A.jdToYearFloat(JD_MIN), Y_MAX = A.jdToYearFloat(JD_MAX);
  const U_MIN = Math.sqrt(Y_END - Y_MIN), U_MAX = Math.sqrt(Y_END - Y_MAX);
  const yearToT = (y) => (U_MIN - Math.sqrt(Y_END - y)) / (U_MIN - U_MAX);
  const tToYear = (t) => Y_END - (U_MIN - t * (U_MIN - U_MAX)) ** 2;

  // ---------- data ----------
  const countryColor = (k) => H.countries[k].color;
  const settlements = H.settlements.map((s) => ({ ...s, fa: toAstro(s.f), ta: s.t == null ? Infinity : toAstro(s.t), px: 0, py: 0 }));
  const polities = H.polities.map((p) => {
    const f = toAstro(p.f), t = toAstro(p.t);
    return { ...p, fa: f, ta: t, color: countryColor(p.k), span: `${histLabel(f)} – ${p.t >= 2030 ? "present" : histLabel(t)}`,
      lobes: p.l.map(([lon, lat, r, lf, lt]) => ({ lon, lat, r, f: lf == null ? f : toAstro(lf), t: lt == null ? t : toAstro(lt), px: 0, py: 0, pr: 0 })) };
  });
  function spanIntensity(f, t, y) {
    if (y <= f || y >= t) return 0;
    const ramp = Math.min(40, (t - f) * 0.2);
    return smooth(Math.min(1, (y - f) / ramp, (t - y) / ramp));
  }
  const paleoRivers = H.paleoRivers.map((r) => ({ ...r, ta: toAstro(r.dryBy), px: [] }));
  const events = H.events.map((e) => {
    const exact = e.m != null;
    const jd = exact ? A.historicalToJd(e.y, e.m, e.day) + 0.25 : A.historicalToJd(e.y, 7, 1);
    const when = exact ? fmtDate(jd) : `${e.c ? "c. " : ""}${e.y < 0 ? `${-e.y} BCE` : `${e.y} CE`}`;
    return { ...e, jd, exact, astroYear: toAstro(e.y), year: A.jdToYearFloat(jd), when, px: 0, py: 0 };
  }).sort((a, b) => a.jd - b.jd);

  // ---------- calendars ----------
  const inUse = (cal, astroYear) => astroYear >= cal.from;
  function eventCalendarText(cal, e) {
    if (e.exact) { const f = cal.full(e.jd); return f.note ? `${f.text} (${f.note})` : f.text; }
    return `${e.c ? "c. " : ""}${C.yearSpan(cal, e.astroYear)}`;
  }
  // collapse identical readings (e.g. the three Hijri entries) into one chip
  function eventChips(e, includePro) {
    const byKey = new Map();
    for (const cal of C.CALENDARS) {
      const on = inUse(cal, e.astroYear);
      if (!on && !includePro) continue;
      const text = eventCalendarText(cal, e);
      const key = SHORT[cal.id] + "|" + text;
      if (!byKey.has(key)) byKey.set(key, { name: SHORT[cal.id], text, on, countries: [] });
      byKey.get(key).countries.push(cal.country);
    }
    return [...byKey.values()].map((c) =>
      `<span class="chip" style="${c.on ? "" : "opacity:.5"}" title="${esc(c.countries.map((k) => C.COUNTRIES[k]).join(", "))}${c.on ? "" : " · not yet in use (proleptic)"}">${esc(c.name)}: <b>${esc(c.text)}</b></span>`).join("");
  }

  // ---------- state ----------
  const SPEEDS = [
    { label: "Even pace", auto: true },
    { label: "1 day/s", d: 1 },
    { label: "1 mo/s", d: 30.436875 },
    { label: "1 yr/s", d: 365.2425 },
    { label: "10 yr/s", d: 3652.425 },
  ];
  const AUTO_SECONDS = 150; // whole range, at an even pace along the timeline
  const state = { jd: JD_MIN, playing: true, speed: 0, view: "india", showPro: false, countries: new Set(COUNTRY_ORDER) };
  const setJd = (jd) => { state.jd = clamp(jd, JD_MIN, JD_MAX); };
  function daysPerSecond() {
    const s = SPEEDS[state.speed];
    if (!s.auto) return s.d;
    const u = Math.sqrt(Y_END - A.jdToYearFloat(state.jd));
    return 2 * u * ((U_MIN - U_MAX) / AUTO_SECONDS) * 365.2425;
  }

  // ---------- canvas helpers ----------
  function fitCanvas(cv, cssH) {
    const dpr = Math.min(window.devicePixelRatio || 1, 2);
    if (cssH != null) cv.style.height = cssH + "px";
    const w = cv.clientWidth, h = cssH == null ? cv.clientHeight : cssH;
    cv.width = Math.round(w * dpr); cv.height = Math.round(h * dpr);
    const ctx = cv.getContext("2d");
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    return { ctx, w, h, dpr };
  }
  function makeLayer(w, h, dpr) {
    const c = document.createElement("canvas");
    c.width = Math.round(w * dpr); c.height = Math.round(h * dpr);
    const ctx = c.getContext("2d");
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    return { c, ctx };
  }
  function blit(ctx, layer) { if (!layer.c.width || !layer.c.height) return; ctx.save(); ctx.setTransform(1, 0, 0, 1, 0, 0); ctx.drawImage(layer.c, 0, 0); ctx.restore(); }

  // ---------- map ----------
  const map = { cv: $("map"), countries: null };
  const VIEWS = { india: [71.2, 21.6, 98.2, 38.3], hkh: [60.5, 20.5, 105.5, 39.5] };
  const COUNTRY_LABELS = { IN: [79.5, 24.3], NP: [83.6, 28.0], BT: [90.5, 27.05], CN: [95.5, 34.8], PK: [70.2, 30.3], AF: [65.6, 33.4], BD: [90.2, 23.6], MM: [95.8, 22.6] };

  function bboxPoints([x0, y0, x1, y1]) {
    const pts = [];
    for (let i = 0; i <= 10; i++) {
      const lx = x0 + (x1 - x0) * i / 10, ly = y0 + (y1 - y0) * i / 10;
      pts.push([lx, y0], [lx, y1], [x0, ly], [x1, ly]);
    }
    return { type: "MultiPoint", coordinates: pts };
  }
  function makeProjection(w, h) {
    const box = VIEWS[state.view];
    if (window.d3 && d3.geoMercator) return d3.geoMercator().fitExtent([[4, 4], [w - 4, h - 4]], bboxPoints(box));
    const [x0, y0, x1, y1] = box, k = Math.min((w - 8) / (x1 - x0), (h - 8) / (y1 - y0));
    const ox = (w - k * (x1 - x0)) / 2, oy = (h - k * (y1 - y0)) / 2;
    const p = ([lon, lat]) => [ox + (lon - x0) * k, oy + (y1 - lat) * k];
    return p;
  }

  // ---- terrain: NASA Blue Marble shaded relief (public domain) via GIBS WMS ----
  // The image comes in plate carree; drawRelief re-maps it strip by strip onto the Mercator map.
  function visibleExtent(proj, w, h) {
    if (!proj.invert) return VIEWS[state.view];
    const [x0, y1] = proj.invert([0, 0]), [x1, y0] = proj.invert([w, h]);
    return [x0, y0, x1, y1].map((v) => Math.round(v * 100) / 100);
  }
  const reliefCache = new Map();
  function reliefFor([x0, y0, x1, y1], pxWide) {
    const width = Math.min(2048, Math.round(pxWide * 1.1));
    const height = Math.round(width * (y1 - y0) / (x1 - x0));
    const key = [x0, y0, x1, y1, width].join(",");
    if (reliefCache.has(key)) return reliefCache.get(key);
    const img = new Image();
    img.crossOrigin = "anonymous";
    img.onload = () => buildMap();
    img.src = "https://gibs.earthdata.nasa.gov/wms/epsg4326/best/wms.cgi?SERVICE=WMS&REQUEST=GetMap&VERSION=1.3.0"
      + `&LAYERS=BlueMarble_ShadedRelief_Bathymetry&STYLES=&FORMAT=image/jpeg&CRS=EPSG:4326&BBOX=${y0},${x0},${y1},${x1}&WIDTH=${width}&HEIGHT=${height}`;
    reliefCache.set(key, img);
    return img;
  }
  function drawRelief(g, proj, img, [x0, y0, x1, y1]) {
    const N = 80;
    for (let j = 0; j < N; j++) {
      const latTop = y1 - (y1 - y0) * j / N, latBottom = y1 - (y1 - y0) * (j + 1) / N;
      const [px0, py0] = proj([x0, latTop]), [px1, py1] = proj([x1, latBottom]);
      g.drawImage(img, 0, img.naturalHeight * j / N, img.naturalWidth, img.naturalHeight / N, px0, py0, px1 - px0, py1 - py0 + 0.6);
    }
  }

  function buildMap() {
    const { ctx, w, h, dpr } = fitCanvas(map.cv);
    Object.assign(map, { ctx, w, h, dpr });
    const proj = makeProjection(w, h);
    const L = makeLayer(w, h, dpr), g = L.ctx;
    const bg = g.createRadialGradient(w * 0.5, h * 0.4, 0, w * 0.5, h * 0.4, Math.max(w, h) * 0.75);
    bg.addColorStop(0, "#0d1440"); bg.addColorStop(1, "#060920");
    g.fillStyle = bg; g.fillRect(0, 0, w, h);
    const fs = Math.max(9, Math.min(12, w / 80));
    const extent = visibleExtent(proj, w, h);
    const relief = reliefFor(extent, w * dpr);
    if (relief && relief.complete && relief.naturalWidth) {
      drawRelief(g, proj, relief, extent);
      g.fillStyle = "rgba(6,9,32,0.32)"; g.fillRect(0, 0, w, h); // keep labels readable
    }
    if (window.d3 && d3.geoPath) {
      const path = d3.geoPath(proj, g);
      g.beginPath(); path(d3.geoGraticule().step([5, 5])()); g.strokeStyle = "rgba(120,140,230,0.08)"; g.lineWidth = 0.6; g.stroke();
      if (map.countries) {
        for (const f of map.countries.features) {
          const member = H.memberIds.includes(f.id);
          g.beginPath(); path(f);
          g.fillStyle = member ? "rgba(20,26,70,0.18)" : "rgba(6,8,26,0.55)"; g.fill();
          g.strokeStyle = member ? "rgba(170,185,255,0.45)" : "rgba(130,150,255,0.2)"; g.lineWidth = 0.6; g.stroke();
        }
      }
      if (map.rivers) {
        g.lineCap = "round"; g.lineJoin = "round";
        for (const f of map.rivers) {
          g.beginPath(); path(f);
          g.strokeStyle = "rgba(125,200,255,0.8)"; g.lineWidth = Math.max(0.6, 2.4 - 0.22 * (f.properties.scalerank || 6)); g.stroke();
        }
      }
      if (map.countries) {
        // India's outline drawn last so its full northern boundary reads clearly
        const india = map.countries.features.find((f) => f.id === "356");
        if (india) { g.beginPath(); path(india); g.strokeStyle = "rgba(255,157,61,0.6)"; g.lineWidth = 1.1; g.stroke(); }
      }
    }
    // mountain ranges and peaks
    g.textAlign = "center"; g.textBaseline = "middle";
    for (const r of H.ranges) {
      const [x, y] = proj(r.at);
      g.save(); g.translate(x, y); g.rotate(r.rot * Math.PI / 180);
      g.font = `italic 500 ${fs * 1.05}px "Cormorant Garamond"`; g.fillStyle = "rgba(200,210,255,0.22)";
      g.fillText(r.n.split("").join(" "), 0, 0); g.restore();
    }
    for (const p of H.peaks) {
      const [x, y] = proj(p.at);
      g.fillStyle = "rgba(235,240,255,0.75)";
      g.beginPath(); g.moveTo(x, y - 5); g.lineTo(x + 4, y + 2.5); g.lineTo(x - 4, y + 2.5); g.closePath(); g.fill();
      if (state.view === "india" || ["Everest", "K2", "Tirich Mir", "Namcha Barwa"].includes(p.s)) {
        g.font = `400 ${fs * 0.82}px "IBM Plex Sans"`; g.fillStyle = "rgba(210,218,250,0.5)"; g.fillText(p.s, x, y + 10);
      }
    }
    for (const [k, at] of Object.entries(COUNTRY_LABELS)) {
      const [x, y] = proj(at);
      g.font = `600 ${fs * 0.9}px "IBM Plex Sans"`; g.fillStyle = rgba(countryColor(k), 0.4);
      g.fillText(H.countries[k].name.toUpperCase().split("").join(" "), x, y);
    }
    map.base = L;
    const pxPerDeg = (lon, lat) => { const a = proj([lon, lat - 0.5]), b = proj([lon, lat + 0.5]); return Math.hypot(b[0] - a[0], b[1] - a[1]); };
    for (const p of polities) for (const lb of p.lobes) { [lb.px, lb.py] = proj([lb.lon, lb.lat]); lb.pr = lb.r * pxPerDeg(lb.lon, lb.lat); }
    for (const s of settlements) [s.px, s.py] = proj(s.at);
    for (const r of paleoRivers) r.px = r.path.map((p) => proj(p));
    for (const e of events) [e.px, e.py] = proj(e.at);
    map.fs = fs;
  }

  const eventWindowYears = () => Math.max(1.5, (daysPerSecond() / 365.2425) * 3);

  function drawMap(year) {
    const { ctx, w, h, fs } = map;
    ctx.clearRect(0, 0, w, h);
    blit(ctx, map.base);
    // polities
    ctx.save(); ctx.globalCompositeOperation = "lighter";
    const labels = [];
    for (const p of polities) {
      let best = null;
      for (const lb of p.lobes) {
        const v = spanIntensity(lb.f, lb.t, year);
        if (!v) continue;
        const r = lb.pr * (0.65 + 0.35 * v);
        const gr = ctx.createRadialGradient(lb.px, lb.py, 0, lb.px, lb.py, r);
        gr.addColorStop(0, rgba(p.color, 0.34 * v)); gr.addColorStop(0.5, rgba(p.color, 0.16 * v)); gr.addColorStop(1, rgba(p.color, 0));
        ctx.fillStyle = gr; ctx.beginPath(); ctx.arc(lb.px, lb.py, r, 0, TAU); ctx.fill();
        if (!best || v * lb.pr > best.s) best = { lb, v, s: v * lb.pr };
      }
      if (best && best.v > 0.3) labels.push({ p, x: best.lb.px, y: best.lb.py - best.lb.pr * 0.35, v: best.v, s: best.s });
    }
    ctx.restore();
    // rivers that dried up or lost their perennial flow: solid while flowing, dashed after
    for (const r of paleoRivers) {
      const flowing = year < r.ta;
      ctx.save();
      ctx.strokeStyle = flowing ? "rgba(125,200,255,0.85)" : "rgba(200,180,140,0.55)";
      ctx.lineWidth = flowing ? 2 : 1.4; ctx.setLineDash(flowing ? [] : [4, 4]);
      ctx.beginPath(); r.px.forEach(([x, y], i) => (i ? ctx.lineTo(x, y) : ctx.moveTo(x, y))); ctx.stroke();
      ctx.restore();
    }
    // settlements: live = dot, abandoned = hollow ring
    const win = eventWindowYears();
    for (const s of settlements) {
      if (year < s.fa) continue;
      const col = countryColor(s.k);
      if (year >= s.ta) {
        ctx.strokeStyle = "rgba(170,180,215,0.45)"; ctx.lineWidth = 1;
        ctx.beginPath(); ctx.arc(s.px, s.py, 3, 0, TAU); ctx.stroke();
        continue;
      }
      ctx.fillStyle = col; ctx.beginPath(); ctx.arc(s.px, s.py, 3, 0, TAU); ctx.fill();
      ctx.strokeStyle = "rgba(6,9,32,0.9)"; ctx.lineWidth = 1; ctx.stroke();
      const ph = (year - s.fa) / (win * 2);
      if (ph < 1) {
        ctx.strokeStyle = rgba(col, 1 - ph); ctx.beginPath(); ctx.arc(s.px, s.py, 3 + 14 * Math.sqrt(ph), 0, TAU); ctx.stroke();
      }
    }
    // polity labels, biggest first, skipping collisions
    labels.sort((a, b) => b.s - a.s);
    const placed = [];
    const overlaps = (r) => placed.some((p) => r[0] < p[0] + p[2] && p[0] < r[0] + r[2] && r[1] < p[1] + p[3] && p[1] < r[1] + r[3]);
    ctx.textAlign = "center"; ctx.textBaseline = "middle"; ctx.font = `500 ${fs}px "IBM Plex Sans"`;
    for (const lab of labels) {
      const tw = ctx.measureText(lab.p.n).width;
      const rect = [lab.x - tw / 2 - 3, lab.y - fs / 2 - 2, tw + 6, fs + 4];
      if (overlaps(rect)) continue;
      placed.push(rect);
      ctx.fillStyle = `rgba(6,9,32,${0.6 * lab.v})`; ctx.fillRect(...rect);
      ctx.fillStyle = rgba(lab.p.color, 0.4 + 0.6 * lab.v); ctx.fillText(lab.p.n, lab.x, lab.y);
    }
    // events and new settlements: expanding rings with a label
    const flashes = [];
    for (const e of events) {
      const ph = (year - e.year) / win;
      if (ph >= 0 && ph <= 1) flashes.push({ x: e.px, y: e.py, ph, text: e.n, col: H.kinds[e.kind].color, big: true });
    }
    for (const s of settlements) {
      const ph = (year - s.fa) / (win * 2);
      if (ph >= 0 && ph <= 1 && year < s.ta) flashes.push({ x: s.px, y: s.py, ph, text: s.n, col: countryColor(s.k), big: false });
    }
    ctx.font = `600 ${fs}px "IBM Plex Sans"`;
    for (const f of flashes) {
      const a = 1 - f.ph;
      if (f.big) {
        ctx.strokeStyle = rgba(f.col, a * 0.9); ctx.lineWidth = 1.5;
        ctx.beginPath(); ctx.arc(f.x, f.y, 4 + 24 * Math.sqrt(f.ph), 0, TAU); ctx.stroke();
        ctx.fillStyle = rgba(f.col, Math.min(1, a * 1.5)); ctx.beginPath(); ctx.arc(f.x, f.y, 3, 0, TAU); ctx.fill();
      }
      const right = f.x > w * 0.72;
      ctx.textAlign = right ? "right" : "left";
      const tx = f.x + (right ? -9 : 9), ty = f.y - 12;
      const tw = ctx.measureText(f.text).width;
      const rect = [right ? tx - tw - 3 : tx - 3, ty - fs / 2 - 2, tw + 6, fs + 4];
      if (!f.big && overlaps(rect)) continue;
      placed.push(rect);
      ctx.fillStyle = `rgba(6,9,32,${0.75 * a})`; ctx.fillRect(...rect);
      ctx.fillStyle = rgba(f.col, Math.min(1, a * 1.6)); ctx.fillText(f.text, tx, ty);
    }
  }

  // ---------- timeline ----------
  const tl = { cv: $("timeline") };
  function buildTimeline() {
    const w = tl.cv.clientWidth;
    const gutter = w > 700 ? 104 : 8, right = 18;
    const rowH = 5, rowGap = 2, tickH = 7, laneGap = 8, top = 6, axisH = 18;
    const lanes = [];
    let y = top;
    for (const k of COUNTRY_ORDER) {
      const list = polities.filter((p) => p.k === k).sort((a, b) => a.fa - b.fa);
      const rowEnds = [];
      for (const p of list) {
        const x0 = yearToT(p.fa);
        let row = rowEnds.findIndex((end) => end + 0.004 < x0);
        if (row < 0) { row = rowEnds.length; rowEnds.push(0); }
        rowEnds[row] = yearToT(p.ta); p.row = row;
      }
      const hLane = tickH + 2 + Math.max(1, rowEnds.length) * (rowH + rowGap);
      for (const p of list) { p.y = y + tickH + 2 + p.row * (rowH + rowGap); p.h = rowH; }
      lanes.push({ k, y, h: hLane });
      y += hLane + laneGap;
    }
    const H_ = y + axisH;
    const { ctx, dpr } = fitCanvas(tl.cv, H_);
    const X = (yr) => gutter + yearToT(yr) * (w - gutter - right);
    Object.assign(tl, { ctx, w, h: H_, gutter, right, X, lanes, tickH });
    const L = makeLayer(w, H_, dpr), g = L.ctx;
    g.font = '400 10.5px "IBM Plex Mono"'; g.textBaseline = "top"; g.textAlign = "center";
    const ticks = w > 900 ? [-7000, -5000, -3000, -2000, -1000, -500, 1, 500, 1000, 1500, 1750, 1900, 2000] : [-7000, -3000, -1000, 1, 1000, 1500, 1900];
    for (const hy of ticks) {
      const x = X(toAstro(hy));
      g.strokeStyle = "rgba(120,140,230,0.12)"; g.beginPath(); g.moveTo(x, 0); g.lineTo(x, H_ - axisH + 2); g.stroke();
      g.fillStyle = "rgba(152,161,204,0.8)"; g.fillText(hy < 0 ? `${-hy} BCE` : `${hy}${hy === 1 ? " CE" : ""}`, x, H_ - axisH + 5);
    }
    for (const ln of lanes) {
      const col = countryColor(ln.k);
      g.fillStyle = ln.k === "IN" ? "rgba(255,157,61,0.05)" : "rgba(255,255,255,0.02)";
      g.fillRect(gutter, ln.y - 2, w - gutter - right, ln.h + 2);
      if (gutter > 20) {
        g.textAlign = "right"; g.textBaseline = "middle"; g.font = `${ln.k === "IN" ? 600 : 500} 11px "IBM Plex Sans"`;
        g.fillStyle = rgba(col, 0.95); g.fillText(H.countries[ln.k].name, gutter - 10, ln.y + ln.h / 2);
      }
    }
    for (const p of polities) {
      const x0 = X(p.fa), x1 = X(Math.min(p.ta, Y_MAX));
      g.fillStyle = rgba(p.color, 0.55); g.fillRect(x0, p.y, Math.max(1.5, x1 - x0), p.h);
    }
    for (const e of events) {
      const ln = lanes.find((l) => l.k === e.k);
      g.fillStyle = rgba(H.kinds[e.kind].color, 0.85);
      g.fillRect(X(e.year) - 0.75, ln.y, 1.5, tl.tickH);
    }
    tl.base = L;
  }
  function drawTimeline(year) {
    const { ctx, w, h, X } = tl;
    ctx.clearRect(0, 0, w, h);
    blit(ctx, tl.base);
    for (const p of polities) {
      const v = spanIntensity(p.fa, p.ta, year);
      if (!v) continue;
      ctx.strokeStyle = rgba(p.color, 0.95 * v); ctx.lineWidth = 1;
      ctx.strokeRect(X(p.fa) + 0.5, p.y - 0.5, Math.max(1.5, X(Math.min(p.ta, Y_MAX)) - X(p.fa)) - 1, p.h + 1);
    }
    const x = X(year);
    const lg = ctx.createLinearGradient(x - 12, 0, x + 12, 0);
    lg.addColorStop(0, "rgba(224,169,64,0)"); lg.addColorStop(0.5, "rgba(224,169,64,0.18)"); lg.addColorStop(1, "rgba(224,169,64,0)");
    ctx.fillStyle = lg; ctx.fillRect(x - 12, 0, 24, h - 18);
    ctx.strokeStyle = "#e0a940"; ctx.lineWidth = 1.5; ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x, h - 18); ctx.stroke();
  }

  // ---------- panels ----------
  const setText = (el, t) => { if (el.textContent !== t) el.textContent = t; };
  const setHTML = (el, html) => { if (el._html !== html) { el.innerHTML = html; el._html = html; } };

  function calendarsHTML(jd) {
    const astroYear = A.jdToCalendar(jd).year;
    let html = "";
    for (const k of COUNTRY_ORDER) {
      const cals = C.CALENDARS.filter((c) => c.country === k);
      const shown = cals.filter((c) => state.showPro || inUse(c, astroYear));
      const hidden = cals.length - shown.length;
      html += `<div class="country${k === "IN" ? " focus" : ""}"><h3><span class="sw" style="background:${countryColor(k)}"></span>${H.countries[k].name}</h3>`;
      for (const cal of shown) {
        const f = cal.full(jd), on = inUse(cal, astroYear);
        html += `<div class="cal${on ? "" : " pro"}" title="${esc(cal.history)}"><div class="nm">${esc(cal.name)}</div><div class="val">${esc(f.text)}${on ? "" : '<span class="tag">not yet in use</span>'}${f.note ? `<div class="note">${esc(f.note)}</div>` : ""}</div></div>`;
      }
      if (hidden) html += `<div class="hidden-count">${hidden === cals.length ? "None of this country's calendars was in use yet." : `${hidden} more not yet in use.`}</div>`;
      html += "</div>";
    }
    return html;
  }

  function updatePanels(year) {
    setText($("date"), fmtDate(state.jd));
    setText($("date-sub"), `${state.jd < 2299160.5 ? "Julian" : "Gregorian"} calendar · JD ${state.jd.toFixed(1)}`);
    setHTML($("calendars"), calendarsHTML(state.jd));

    let prev = null, next = null;
    for (const e of events) { if (e.jd <= state.jd + 0.5) prev = e; else { next = e; break; } }
    const recent = prev && year - prev.year < Math.max(150, eventWindowYears() * 3);
    let html = `<div class="label">${recent ? "Latest event" : "Between events"}</div>`;
    if (recent) {
      html += `<div class="ev-title" style="color:${H.kinds[prev.kind].color}">${esc(prev.n)}</div>`
        + `<div class="ev-meta">${prev.when} · ${H.countries[prev.k].name} · ${H.kinds[prev.kind].name}</div>`
        + `<div class="ev-desc">${esc(prev.d)}</div><div class="ev-cals">${eventChips(prev, state.showPro)}</div>`;
    } else {
      html += `<div class="ev-desc">No event in the dataset for this stretch of time.</div>`;
    }
    if (next) {
      const dy = next.year - year;
      html += `<div class="next">Next: ${esc(next.n)}, ${dy < 1 ? `in ${Math.max(1, Math.round(dy * 365))} days` : `in ${Math.round(dy)} years`}<button data-jump="${events.indexOf(next)}">Go</button></div>`;
    }
    setHTML($("event-card"), html);

    const active = polities.map((p) => ({ p, v: spanIntensity(p.fa, p.ta, year) })).filter((x) => x.v > 0);
    const live = settlements.filter((s) => year >= s.fa && year < s.ta).length;
    setText($("counts"), `${live} settlements · ${active.length} states`);
    setHTML($("active"), active.length
      ? active.map(({ p, v }) => `<span class="chip" style="border-color:${rgba(p.color, 0.3 + 0.6 * v)};color:${rgba(p.color, 0.55 + 0.45 * v)}">${esc(p.n)}</span>`).join("")
      : `<span class="ev-desc" style="color:var(--text-faint)">None in the dataset yet.</span>`);
  }

  (function buildLegend() {
    $("legend").innerHTML = Object.values(H.kinds).map((k) => `<span><span class="sw" style="border:1.5px solid ${k.color}"></span>${k.name}</span>`).join("")
      + `<span><span class="sw" style="background:#7dc8ff;border-radius:1px;height:2px;width:14px"></span>River</span><span><span class="sw" style="border-top:1.5px dashed #c8b48c;border-radius:0;height:0;width:14px"></span>Dried-up river</span>`
      + `<span><span class="sw" style="background:#ff9d3d"></span>Settlement</span><span><span class="sw" style="border:1px solid #aab4d7"></span>Abandoned</span><span>▲ Peak</span>`;
  })();

  // ---------- table ----------
  function renderTable() {
    const rows = events.filter((e) => state.countries.has(e.k)).map((e, i) =>
      `<tr data-jump="${events.indexOf(e)}"><td class="when">${e.when}</td>`
      + `<td class="what"><b style="color:${H.kinds[e.kind].color}">${esc(e.n)}</b><div><span class="sw" style="background:${countryColor(e.k)};margin-right:5px"></span>${H.countries[e.k].name} · ${esc(e.d)}</div></td>`
      + `<td><div class="chips">${eventChips(e, state.showPro) || '<span class="ev-desc" style="color:var(--text-faint)">None of these calendars existed yet.</span>'}</div></td></tr>`);
    $("rows").innerHTML = rows.join("");
  }
  (function buildFilters() {
    $("filters").innerHTML = COUNTRY_ORDER.map((k) => `<button data-k="${k}" aria-pressed="true"><span class="sw" style="background:${countryColor(k)};margin-right:6px"></span>${H.countries[k].name}</button>`).join("");
    for (const b of $("filters").children) {
      b.onclick = () => {
        const k = b.dataset.k;
        state.countries.has(k) ? state.countries.delete(k) : state.countries.add(k);
        b.setAttribute("aria-pressed", String(state.countries.has(k)));
        renderTable();
      };
    }
  })();
  $("table-section").addEventListener("toggle", () => { if ($("table-section").open && !$("rows").children.length) renderTable(); });
  $("rows").addEventListener("click", (e) => { const tr = e.target.closest("[data-jump]"); if (tr) { jumpTo(+tr.dataset.jump); window.scrollTo({ top: 0, behavior: "smooth" }); } });

  // ---------- controls ----------
  const playBtn = $("play");
  function setPlaying(p) {
    state.playing = p;
    playBtn.textContent = p ? "❚❚ Pause" : "▶ Play";
    playBtn.setAttribute("aria-label", p ? "Pause" : "Play");
  }
  playBtn.onclick = () => { if (!state.playing && state.jd >= JD_MAX) setJd(JD_MIN); setPlaying(!state.playing); };
  const stepDays = () => (SPEEDS[state.speed].auto ? 365.2425 : SPEEDS[state.speed].d);
  $("step-back").onclick = () => setJd(state.jd - stepDays());
  $("step-fwd").onclick = () => setJd(state.jd + stepDays());
  SPEEDS.forEach((s, i) => {
    const b = document.createElement("button");
    b.textContent = s.label; b.dataset.i = i;
    b.onclick = () => { state.speed = i; syncSpeeds(); };
    $("speeds").appendChild(b);
  });
  function syncSpeeds() { for (const b of $("speeds").children) b.setAttribute("aria-pressed", String(+b.dataset.i === state.speed)); }
  syncSpeeds();
  $("jump").innerHTML = `<option value="">Jump to an event…</option>` + events.map((e, i) => `<option value="${i}">${e.when} — ${esc(e.n)}</option>`).join("");
  function jumpTo(i) {
    const e = events[i]; if (!e) return;
    setJd(e.jd); setPlaying(false);
    if (e.exact) state.speed = 1;
    syncSpeeds();
  }
  $("jump").onchange = () => { jumpTo(+$("jump").value); $("jump").value = ""; };
  $("event-card").addEventListener("click", (ev) => { const b = ev.target.closest("[data-jump]"); if (b) jumpTo(+b.dataset.jump); });
  $("show-pro").onchange = () => { state.showPro = $("show-pro").checked; if ($("rows").children.length) renderTable(); };
  for (const b of $("views").children) {
    b.onclick = () => {
      state.view = b.dataset.view;
      for (const o of $("views").children) o.setAttribute("aria-pressed", String(o === b));
      buildMap();
    };
  }
  document.addEventListener("keydown", (e) => {
    if (["SELECT", "INPUT", "SUMMARY"].includes(e.target.tagName)) return;
    if (e.code === "Space") { e.preventDefault(); playBtn.click(); }
    else if (e.key === "ArrowRight") { e.preventDefault(); $("step-fwd").click(); }
    else if (e.key === "ArrowLeft") { e.preventDefault(); $("step-back").click(); }
  });

  // timeline scrub + hover, map hover
  const tip = $("tip");
  const showTip = (e, html) => { tip.innerHTML = html; tip.style.display = "block"; tip.style.left = Math.min(e.clientX + 14, window.innerWidth - 290) + "px"; tip.style.top = e.clientY + 14 + "px"; };
  const hideTip = () => { tip.style.display = "none"; };
  {
    let down = false;
    const yearAt = (e) => { const r = tl.cv.getBoundingClientRect(); return tToYear(clamp((e.clientX - r.left - tl.gutter) / (tl.w - tl.gutter - tl.right), 0, 1)); };
    tl.cv.addEventListener("pointerdown", (e) => { down = true; tl.cv.setPointerCapture(e.pointerId); setJd(A.yearFloatToJd(yearAt(e))); });
    tl.cv.addEventListener("pointermove", (e) => {
      if (down) { setJd(A.yearFloatToJd(yearAt(e))); hideTip(); return; }
      const r = tl.cv.getBoundingClientRect(), mx = e.clientX - r.left, my = e.clientY - r.top;
      const ln = tl.lanes.find((l) => my >= l.y - 2 && my <= l.y + l.h);
      if (!ln) return hideTip();
      if (my <= ln.y + tl.tickH + 1) {
        let best = null, bd = 5;
        for (const ev of events) if (ev.k === ln.k) { const d = Math.abs(tl.X(ev.year) - mx); if (d < bd) { bd = d; best = ev; } }
        return best ? showTip(e, `<b>${esc(best.n)}</b><div class="m">${best.when}</div>`) : hideTip();
      }
      const p = polities.find((p) => p.k === ln.k && my >= p.y - 1 && my <= p.y + p.h + 1 && mx >= tl.X(p.fa) - 1 && mx <= tl.X(Math.min(p.ta, Y_MAX)) + 1);
      p ? showTip(e, `<b style="color:${p.color}">${esc(p.n)}</b><div class="m">${p.span}</div>`) : hideTip();
    });
    const up = () => { down = false; };
    tl.cv.addEventListener("pointerup", up); tl.cv.addEventListener("pointercancel", up);
    tl.cv.addEventListener("pointerleave", hideTip);
  }
  map.cv.addEventListener("pointermove", (e) => {
    const r = map.cv.getBoundingClientRect(), mx = e.clientX - r.left, my = e.clientY - r.top;
    const year = A.jdToYearFloat(state.jd);
    const parts = [];
    for (const s of settlements) {
      if (year >= s.fa && Math.hypot(s.px - mx, s.py - my) < 7) {
        parts.push(`<b style="color:${countryColor(s.k)}">${esc(s.n)}</b>${year >= s.ta ? " (abandoned)" : ""}<div class="m">${s.c ? "c. " : ""}${histLabel(s.fa)}${s.t == null ? "" : ` – ${histLabel(s.ta)}`}</div><div>${esc(s.d)}</div>`);
      }
    }
    for (const rv of paleoRivers) {
      if (rv.px.some(([x, y]) => Math.hypot(x - mx, y - my) < 8)) parts.push(`<b style="color:#7dc8ff">${esc(rv.n)}</b> <span class="m">${year < rv.ta ? "flowing" : "dry bed"}</span><div>${esc(rv.d)}</div>`);
    }
    const win = eventWindowYears();
    for (const ev of events) {
      const ph = (year - ev.year) / win;
      if (ph >= 0 && ph <= 1 && Math.hypot(ev.px - mx, ev.py - my) < 12) parts.push(`<b style="color:${H.kinds[ev.kind].color}">${esc(ev.n)}</b><div class="m">${ev.when}</div>`);
    }
    for (const p of polities) {
      if (p.lobes.some((lb) => spanIntensity(lb.f, lb.t, year) && Math.hypot(lb.px - mx, lb.py - my) < lb.pr * 0.75)) parts.push(`<div><b style="color:${p.color}">${esc(p.n)}</b> <span class="m">${p.span}</span></div>`);
    }
    parts.length ? showTip(e, parts.join("")) : hideTip();
  });
  map.cv.addEventListener("pointerleave", hideTip);

  // ---------- loop ----------
  function buildAll() { buildMap(); buildTimeline(); }
  let resizeTimer = 0;
  window.addEventListener("resize", () => { clearTimeout(resizeTimer); resizeTimer = setTimeout(buildAll, 120); });
  let last = performance.now(), lastPanel = 0;
  function frame(now) {
    const dt = Math.min(0.1, (now - last) / 1000); last = now;
    if (state.playing) {
      setJd(state.jd + daysPerSecond() * dt);
      if (state.jd >= JD_MAX) setPlaying(false);
    }
    const year = A.jdToYearFloat(state.jd);
    drawMap(year);
    drawTimeline(year);
    if (now - lastPanel > 200) { updatePanels(year); lastPanel = now; }
    requestAnimationFrame(frame);
  }
  buildAll();
  setPlaying(state.playing);
  requestAnimationFrame(frame);

  // Natural Earth 1:50m river centrelines, kept to the region
  fetch("https://cdn.jsdelivr.net/gh/nvkelso/natural-earth-vector@master/geojson/ne_50m_rivers_lake_centerlines.geojson")
    .then((r) => r.json())
    .then((fc) => {
      const inRegion = (c) => c[0] > 55 && c[0] < 110 && c[1] > 12 && c[1] < 46;
      map.rivers = fc.features.filter((f) => {
        const lines = f.geometry.type === "MultiLineString" ? f.geometry.coordinates : [f.geometry.coordinates];
        return lines.some((l) => l.some(inRegion));
      });
      buildMap();
    })
    .catch((err) => console.warn("rivers unavailable", err));

  // Country outlines as on the Government of India's official map (Natural
  // Earth's India worldview; see scripts/build_hkh_boundaries.py).
  fetch("boundaries_ind.json")
    .then((r) => r.json())
    .then((fc) => {
      // d3-geo wants clockwise outer rings; flip any polygon that would otherwise cover the globe
      if (window.d3 && d3.geoArea) {
        for (const f of fc.features) {
          f.geometry.coordinates = f.geometry.coordinates.map((poly) => {
            const single = { type: "Polygon", coordinates: poly };
            return d3.geoArea(single) > 2 * Math.PI ? poly.map((ring) => ring.slice().reverse()) : poly;
          });
        }
      }
      map.countries = fc; buildMap();
    })
    .catch((err) => console.warn("country outlines unavailable", err));
  document.fonts && document.fonts.ready.then(buildMap);
})();
