(function () {
  "use strict";
  const A = window.Astro, H = window.HISTORY;
  const $ = (id) => document.getElementById(id);
  const TAU = Math.PI * 2, D2R = Math.PI / 180;

  const RASHIS = ["Mesha", "Vrishabha", "Mithuna", "Karka", "Simha", "Kanya", "Tula", "Vrischika", "Dhanu", "Makara", "Kumbha", "Meena"];
  const NAKS = ["Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra", "Punarvasu", "Pushya", "Ashlesha", "Magha",
    "Purva Phalguni", "Uttara Phalguni", "Hasta", "Chitra", "Swati", "Vishakha", "Anuradha", "Jyeshtha", "Mula",
    "Purva Ashadha", "Uttara Ashadha", "Shravana", "Dhanishta", "Shatabhisha", "Purva Bhadrapada", "Uttara Bhadrapada", "Revati"];
  const NAK_SHORT = NAKS.map((n) => n.replace("Purva ", "P.").replace("Uttara ", "U.").replace("Bhadrapada", "Bhadra").replace("Mrigashira", "Mriga").replace("Shatabhisha", "Shatabhi"));
  const MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];

  // r: orbit radius as a fraction of the wheel; mm: mean motion deg/day (for trail blur)
  const GRAHA = {
    Chandra: { label: "Chandra", abbr: "Mo", color: "#e9edff", r: 0.13, mm: 13.18, size: 5 },
    Budha: { label: "Budha", abbr: "Me", color: "#7fe0a0", r: 0.165, mm: 0.99, size: 3.5 },
    Shukra: { label: "Shukra", abbr: "Ve", color: "#fff0f8", r: 0.2, mm: 0.99, size: 4.5 },
    Surya: { label: "Surya", abbr: "Su", color: "#ffc94d", r: 0.235, mm: 0.986, size: 6.5 },
    Mangala: { label: "Mangala", abbr: "Ma", color: "#ff5b4a", r: 0.27, mm: 0.524, size: 4 },
    Guru: { label: "Guru", abbr: "Ju", color: "#ffb46b", r: 0.305, mm: 0.0831, size: 5.5 },
    Shani: { label: "Shani", abbr: "Sa", color: "#8fa6ff", r: 0.34, mm: 0.0335, size: 4.5 },
    Rahu: { label: "Rahu", abbr: "Ra", color: "#a68bff", r: 0.372, mm: 0.053, size: 3.5 },
    Ketu: { label: "Ketu", abbr: "Ke", color: "#c79a78", r: 0.372, mm: 0.053, size: 3.5 },
  };
  const TABLE_ORDER = ["Surya", "Chandra", "Mangala", "Budha", "Guru", "Shukra", "Shani", "Rahu", "Ketu"];
  const KIND_COLOR = { war: "#ff6b5b", culture: "#ffd27a", science: "#7fe0ff", faith: "#f6a6ff", sky: "#ffffff" };
  const KIND_LABEL = { war: "Power & war", culture: "Culture", science: "Science", faith: "Faith", sky: "Sky & astronomy" };

  const SPEEDS = [
    { label: "1 day/s", d: 1 },
    { label: "1 mo/s", d: 30.436875 },
    { label: "1 yr/s", d: 365.2425 },
    { label: "10 yr/s", d: 3652.425 },
    { label: "100 yr/s", d: 36524.25 },
  ];

  const toAstro = (h) => (h < 0 ? h + 1 : h);
  const histYearLabel = (astro) => (astro <= 0 ? `${1 - astro} BCE` : `${astro} CE`);
  const JD_MIN = A.historicalToJd(-3500, 1, 1);
  const JD_MAX = A.historicalToJd(2030, 12, 31);
  const Y_MIN = A.jdToYearFloat(JD_MIN), Y_MAX = A.jdToYearFloat(JD_MAX);

  function rgba(hex, a) {
    const n = parseInt(hex.slice(1), 16);
    return `rgba(${(n >> 16) & 255},${(n >> 8) & 255},${n & 255},${a})`;
  }
  const clamp = (x, lo, hi) => Math.max(lo, Math.min(hi, x));
  const smooth = (x) => x * x * (3 - 2 * x);
  const angDist = (a, b) => Math.abs(((a - b + 540) % 360) - 180);

  function fmtDate(jd) {
    const c = A.jdToCalendar(jd);
    return `${c.day} ${MONTHS[c.month - 1]} ${histYearLabel(c.year)}`;
  }
  function fmtDeg(lon) {
    const inSign = lon % 30;
    const d = Math.floor(inSign), m = Math.floor((inSign - d) * 60);
    return `${String(d).padStart(2, " ")}°${String(m).padStart(2, "0")}′`;
  }
  function nakOf(lon) {
    const span = 360 / 27;
    const i = Math.floor(lon / span);
    return { i, pada: Math.floor((lon - i * span) / (span / 4)) + 1 };
  }

  // ---------- data prep ----------
  const regionKeys = Object.keys(H.regions);
  const civs = H.civs.map((c) => {
    const f = toAstro(c.f), t = toAstro(c.t);
    return {
      name: c.n, region: c.r, color: H.regions[c.r].color, f, t, spanLabel: `${histYearLabel(f)} – ${c.t >= 2030 ? "present" : histYearLabel(t)}`,
      lobes: c.l.map(([lon, lat, r, lf, lt]) => ({ lon, lat, r, f: lf == null ? f : toAstro(lf), t: lt == null ? t : toAstro(lt), px: 0, py: 0, pr: 0 })),
    };
  });
  function spanIntensity(f, t, y) {
    if (y <= f || y >= t) return 0;
    const ramp = Math.min(80, (t - f) * 0.25);
    return smooth(Math.min(1, (y - f) / ramp, (t - y) / ramp));
  }
  const events = H.events.map((e) => {
    const exact = e.m != null;
    const jd = A.historicalToJd(e.y, e.m || 7, e.day || 1);
    return { ...e, jd, year: A.jdToYearFloat(jd), exact, when: exact ? fmtDate(jd) : (e.y < 0 ? `${-e.y} BCE` : `${e.y} CE`), px: 0, py: 0 };
  }).sort((a, b) => a.jd - b.jd);

  // ---------- state ----------
  const state = { jd: A.historicalToJd(-3300, 1, 1), playing: true, speed: 3, dir: 1, dragging: false, inertia: 0, view: "world" };
  const setJd = (jd) => { state.jd = clamp(jd, JD_MIN, JD_MAX); };

  // ---------- canvas helpers ----------
  function fitCanvas(cv, cssH) {
    const dpr = Math.min(window.devicePixelRatio || 1, 2);
    const w = cv.clientWidth, h = cssH == null ? cv.clientHeight : cssH;
    if (cssH != null) cv.style.height = cssH + "px";
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
  function blit(ctx, layer, w, h) {
    ctx.save(); ctx.setTransform(1, 0, 0, 1, 0, 0); ctx.drawImage(layer.c, 0, 0); ctx.restore();
  }
  function seeded(seed) {
    let s = seed >>> 0;
    return () => ((s = (s * 1664525 + 1013904223) >>> 0) / 4294967296);
  }

  // ---------- sky wheel ----------
  const sky = { cv: $("sky") };
  // longitude -> canvas angle; 0° Mesha at 9 o'clock, increasing counter-clockwise
  const skyXY = (lon, r) => [sky.c - r * Math.cos(lon * D2R), sky.c + r * Math.sin(lon * D2R)];

  function buildSky() {
    const { ctx, w, dpr } = fitCanvas(sky.cv);
    Object.assign(sky, { ctx, S: w, c: w / 2, dpr });
    const S = w, c = w / 2;
    const L = makeLayer(S, S, dpr), g = L.ctx;
    const rnd = seeded(7);
    for (let i = 0; i < 260; i++) {
      const a = rnd() * TAU, rr = Math.sqrt(rnd()) * S * 0.5;
      g.fillStyle = `rgba(220,225,255,${0.15 + rnd() * 0.5})`;
      g.beginPath(); g.arc(c + rr * Math.cos(a), c + rr * Math.sin(a), rnd() < 0.08 ? 1.2 : 0.6, 0, TAU); g.fill();
    }
    const glow = g.createRadialGradient(c, c, 0, c, c, S * 0.5);
    glow.addColorStop(0, "rgba(60,80,190,0.20)"); glow.addColorStop(0.7, "rgba(40,50,140,0.08)"); glow.addColorStop(1, "rgba(0,0,0,0)");
    g.fillStyle = glow; g.fillRect(0, 0, S, S);

    const rN0 = S * 0.445, rN1 = S * 0.49, rR0 = S * 0.395;
    // rings
    for (const [r, a] of [[rN1, 0.55], [rN0, 0.45], [rR0, 0.45]]) {
      g.strokeStyle = `rgba(150,165,240,${a})`; g.lineWidth = 1;
      g.beginPath(); g.arc(c, c, r, 0, TAU); g.stroke();
    }
    // rashi band fill, alternating
    for (let i = 0; i < 12; i++) {
      // canvas angle = 180° - longitude, so increasing longitude runs anticlockwise
      const a0 = Math.PI - (i * 30) * D2R, a1 = Math.PI - (i * 30 + 30) * D2R;
      g.beginPath(); g.arc(c, c, rN0, a0, a1, true); g.arc(c, c, rR0, a1, a0, false); g.closePath();
      g.fillStyle = i % 2 ? "rgba(120,140,255,0.05)" : "rgba(224,169,64,0.05)"; g.fill();
    }
    // spokes & labels
    g.textAlign = "center"; g.textBaseline = "middle";
    const tangentText = (text, lon, r, font, color, maxW) => {
      const [x, y] = skyXY(lon, r);
      g.save(); g.translate(x, y);
      const phi = Math.atan2(y - c, x - c);
      let rot = phi + Math.PI / 2;
      if (Math.sin(phi) > 0.001) rot += Math.PI;
      g.rotate(rot); g.font = font; g.fillStyle = color;
      const tw = g.measureText(text).width;
      if (maxW && tw > maxW) g.scale(maxW / tw, maxW / tw);
      g.fillText(text, 0, 0); g.restore();
    };
    for (let i = 0; i < 27; i++) {
      const lon = i * (360 / 27);
      const [x0, y0] = skyXY(lon, rN0), [x1, y1] = skyXY(lon, rN1);
      g.strokeStyle = "rgba(150,165,240,0.35)"; g.beginPath(); g.moveTo(x0, y0); g.lineTo(x1, y1); g.stroke();
      tangentText(NAK_SHORT[i], lon + 180 / 27, (rN0 + rN1) / 2, `400 ${Math.max(7, S * 0.019)}px "IBM Plex Sans"`, "rgba(185,195,240,0.75)", 2 * Math.PI * ((rN0 + rN1) / 2) / 27 * 0.88);
    }
    for (let i = 0; i < 12; i++) {
      const lon = i * 30;
      const [x0, y0] = skyXY(lon, S * 0.1), [x1, y1] = skyXY(lon, rN0);
      g.strokeStyle = "rgba(150,165,240,0.14)"; g.beginPath(); g.moveTo(x0, y0); g.lineTo(x1, y1); g.stroke();
      tangentText(RASHIS[i], lon + 15, (rR0 + rN0) / 2, `600 ${Math.max(9, S * 0.029)}px "Cormorant Garamond"`, "rgba(240,225,190,0.92)");
    }
    // orbit guides
    for (const k of ["Chandra", "Budha", "Shukra", "Surya", "Mangala", "Guru", "Shani", "Rahu"]) {
      g.strokeStyle = "rgba(150,165,240,0.10)"; g.setLineDash([2, 4]);
      g.beginPath(); g.arc(c, c, GRAHA[k].r * S, 0, TAU); g.stroke();
    }
    g.setLineDash([]);
    // reference stars (fixed in the sidereal frame)
    for (const st of H.stars) {
      const [x, y] = skyXY(st.lon, rR0 - 5);
      const sg = g.createRadialGradient(x, y, 0, x, y, 6);
      sg.addColorStop(0, "rgba(255,255,255,0.95)"); sg.addColorStop(1, "rgba(255,255,255,0)");
      g.fillStyle = sg; g.beginPath(); g.arc(x, y, 6, 0, TAU); g.fill();
    }
    // Earth
    const er = S * 0.055;
    const eg = g.createRadialGradient(c - er * 0.3, c - er * 0.3, er * 0.1, c, c, er);
    eg.addColorStop(0, "#7fc4ff"); eg.addColorStop(0.6, "#2c6fd1"); eg.addColorStop(1, "#0d2a66");
    g.shadowColor = "rgba(90,160,255,0.7)"; g.shadowBlur = 18;
    g.fillStyle = eg; g.beginPath(); g.arc(c, c, er, 0, TAU); g.fill();
    g.shadowBlur = 0;
    sky.base = L;
  }

  function trailDays() { return SPEEDS[state.speed].d * 0.9; }

  function drawSky(pos) {
    const { ctx, S, c } = sky;
    ctx.clearRect(0, 0, S, S);
    blit(ctx, sky.base);
    // precession: tropical 0° (vernal equinox) in the sidereal frame
    const ayan = A.ayanamsha(state.jd);
    const eqLon = A.norm(-ayan);
    for (const [off, label] of [[0, "♈︎ equinox"], [180, ""]]) {
      const [x0, y0] = skyXY(eqLon + off, S * 0.08), [x1, y1] = skyXY(eqLon + off, S * 0.5);
      const lg = ctx.createLinearGradient(x0, y0, x1, y1);
      lg.addColorStop(0, "rgba(127,224,255,0)"); lg.addColorStop(1, off ? "rgba(127,224,255,0.25)" : "rgba(127,224,255,0.85)");
      ctx.strokeStyle = lg; ctx.lineWidth = off ? 1 : 1.5;
      ctx.beginPath(); ctx.moveTo(x0, y0); ctx.lineTo(x1, y1); ctx.stroke();
      if (label) {
        const [lx, ly] = skyXY(eqLon, S * 0.5 - 2);
        ctx.fillStyle = "#7fe0ff"; ctx.beginPath(); ctx.arc(lx, ly, 3, 0, TAU); ctx.fill();
      }
    }
    // nodal axis
    {
      const [x0, y0] = skyXY(pos.Rahu, GRAHA.Rahu.r * S), [x1, y1] = skyXY(pos.Ketu, GRAHA.Ketu.r * S);
      ctx.strokeStyle = "rgba(166,139,255,0.18)"; ctx.lineWidth = 1;
      ctx.beginPath(); ctx.moveTo(x0, y0); ctx.lineTo(x1, y1); ctx.stroke();
    }
    // trails
    const span = trailDays(), N = 26;
    const samples = [];
    for (let k = N; k >= 1; k--) samples.push(A.grahas(state.jd - state.dir * span * (k / N)));
    ctx.lineCap = "round";
    for (const name of Object.keys(GRAHA)) {
      const G = GRAHA[name], r = G.r * S;
      const sweep = G.mm * span;
      if (sweep > 300) {
        ctx.strokeStyle = rgba(G.color, 0.28); ctx.lineWidth = G.size * 1.2;
        ctx.beginPath(); ctx.arc(c, c, r, 0, TAU); ctx.stroke();
        continue;
      }
      let prev = null;
      for (let k = 0; k <= N; k++) {
        const lon = k < N ? samples[k][name] : pos[name];
        if (prev != null && angDist(prev, lon) < 60) {
          const [x0, y0] = skyXY(prev, r), [x1, y1] = skyXY(lon, r);
          ctx.strokeStyle = rgba(G.color, 0.05 + 0.5 * (k / N) ** 2);
          ctx.lineWidth = G.size * (0.5 + 0.7 * k / N);
          ctx.beginPath(); ctx.moveTo(x0, y0); ctx.lineTo(x1, y1); ctx.stroke();
        }
        prev = lon;
      }
    }
    // bodies
    ctx.textAlign = "center"; ctx.textBaseline = "middle";
    for (const name of Object.keys(GRAHA)) {
      const G = GRAHA[name], [x, y] = skyXY(pos[name], G.r * S);
      const blurred = G.mm * span > 300;
      const s = G.size * (S / 440);
      const gl = ctx.createRadialGradient(x, y, 0, x, y, s * 3.2);
      gl.addColorStop(0, rgba(G.color, blurred ? 0.4 : 0.9)); gl.addColorStop(1, rgba(G.color, 0));
      ctx.fillStyle = gl; ctx.beginPath(); ctx.arc(x, y, s * 3.2, 0, TAU); ctx.fill();
      ctx.fillStyle = blurred ? rgba(G.color, 0.55) : G.color;
      ctx.beginPath(); ctx.arc(x, y, s, 0, TAU); ctx.fill();
      if (!blurred) {
        const [lx, ly] = skyXY(pos[name], G.r * S + (name === "Rahu" || name === "Ketu" ? -11 : 0));
        ctx.font = `500 ${Math.max(8, S * 0.022)}px "IBM Plex Mono"`;
        ctx.fillStyle = rgba(G.color, 0.9);
        ctx.fillText(G.abbr, lx + (name === "Rahu" || name === "Ketu" ? 0 : s + 9) * (lx < c ? -1 : 1) * (name === "Rahu" || name === "Ketu" ? 0 : 1), ly - (name === "Rahu" || name === "Ketu" ? 0 : s + 5));
      }
    }
  }

  // ---------- map ----------
  const map = { cv: $("map"), land: null };
  const VIEWS = {
    world: [-170, -50, 180, 72],
    oldworld: [-18, -8, 150, 62],
    americas: [-128, -45, -32, 52],
  };
  function bboxPoints([x0, y0, x1, y1]) {
    const pts = [];
    for (let i = 0; i <= 12; i++) {
      const lx = x0 + (x1 - x0) * i / 12, ly = y0 + (y1 - y0) * i / 12;
      pts.push([lx, y0], [lx, y1], [x0, ly], [x1, ly]);
    }
    return { type: "MultiPoint", coordinates: pts };
  }
  function makeProjection(w, h) {
    const box = VIEWS[state.view];
    if (window.d3 && d3.geoNaturalEarth1) {
      return d3.geoNaturalEarth1().fitExtent([[6, 6], [w - 6, h - 6]], bboxPoints(box));
    }
    // fallback: plain equirectangular if the CDN is unreachable
    const [x0, y0, x1, y1] = box, k = Math.min((w - 12) / (x1 - x0), (h - 12) / (y1 - y0));
    const ox = (w - k * (x1 - x0)) / 2, oy = (h - k * (y1 - y0)) / 2;
    const p = ([lon, lat]) => [ox + (lon - x0) * k, oy + (y1 - lat) * k];
    p.invert = ([x, y]) => [x0 + (x - ox) / k, y1 - (y - oy) / k];
    return p;
  }

  function buildMap() {
    const { ctx, w, h, dpr } = fitCanvas(map.cv);
    Object.assign(map, { ctx, w, h, dpr });
    const proj = makeProjection(w, h);
    map.proj = proj;
    const L = makeLayer(w, h, dpr), g = L.ctx;
    const bg = g.createRadialGradient(w * 0.5, h * 0.45, 0, w * 0.5, h * 0.45, Math.max(w, h) * 0.7);
    bg.addColorStop(0, "#0d1440"); bg.addColorStop(1, "#060920");
    g.fillStyle = bg; g.fillRect(0, 0, w, h);
    if (window.d3 && d3.geoPath) {
      const path = d3.geoPath(proj, g);
      g.beginPath(); path(d3.geoGraticule10()); g.strokeStyle = "rgba(120,140,230,0.09)"; g.lineWidth = 0.6; g.stroke();
      g.beginPath(); path({ type: "Sphere" }); g.strokeStyle = "rgba(120,140,230,0.25)"; g.lineWidth = 1; g.stroke();
      if (map.land) {
        g.save(); g.shadowColor = "rgba(90,120,255,0.35)"; g.shadowBlur = 10;
        g.beginPath(); path(map.land); g.fillStyle = "#151c48"; g.fill(); g.restore();
        g.beginPath(); path(map.land); g.strokeStyle = "rgba(130,150,255,0.45)"; g.lineWidth = 0.6; g.stroke();
      }
    }
    map.base = L;
    // cache projected lobes & events
    for (const cv of civs) for (const lb of cv.lobes) {
      const p = proj([lb.lon, lb.lat]), q0 = proj([lb.lon, lb.lat - 0.5]), q1 = proj([lb.lon, lb.lat + 0.5]);
      lb.px = p[0]; lb.py = p[1]; lb.pr = lb.r * Math.hypot(q1[0] - q0[0], q1[1] - q0[1]);
    }
    for (const e of events) { const p = proj(e.at); e.px = p[0]; e.py = p[1]; }
  }

  function eventWindowYears() { return Math.max(1.5, (SPEEDS[state.speed].d / 365.2425) * 4); }

  function drawMap(year) {
    const { ctx, w, h } = map;
    ctx.clearRect(0, 0, w, h);
    blit(ctx, map.base);
    ctx.save();
    ctx.globalCompositeOperation = "lighter";
    const labels = [];
    for (const cv of civs) {
      let best = null, bestScore = 0;
      for (const lb of cv.lobes) {
        const v = spanIntensity(lb.f, lb.t, year);
        if (!v) continue;
        const r = lb.pr * (0.7 + 0.4 * v);
        const gr = ctx.createRadialGradient(lb.px, lb.py, 0, lb.px, lb.py, r);
        gr.addColorStop(0, rgba(cv.color, 0.8 * v));
        gr.addColorStop(0.45, rgba(cv.color, 0.45 * v));
        gr.addColorStop(1, rgba(cv.color, 0));
        ctx.fillStyle = gr; ctx.beginPath(); ctx.arc(lb.px, lb.py, r, 0, TAU); ctx.fill();
        if (v * lb.pr > bestScore) { bestScore = v * lb.pr; best = { lb, v }; }
      }
      if (best && best.v > 0.3) labels.push({ cv, x: best.lb.px, y: best.lb.py, v: best.v, score: bestScore });
    }
    ctx.restore();
    // civ labels, largest first, skipping collisions
    labels.sort((a, b) => b.score - a.score);
    const placed = [];
    ctx.textAlign = "center"; ctx.textBaseline = "middle";
    const fs = Math.max(9.5, Math.min(12.5, w / 90));
    ctx.font = `500 ${fs}px "IBM Plex Sans"`;
    for (const lab of labels) {
      const tw = ctx.measureText(lab.cv.name).width;
      const rect = [lab.x - tw / 2 - 3, lab.y - fs / 2 - 2, tw + 6, fs + 4];
      if (placed.some((p) => rect[0] < p[0] + p[2] && p[0] < rect[0] + rect[2] && rect[1] < p[1] + p[3] && p[1] < rect[1] + rect[3])) continue;
      placed.push(rect);
      ctx.fillStyle = `rgba(6,9,32,${0.55 * lab.v})`;
      ctx.fillRect(...rect);
      ctx.fillStyle = rgba(lab.cv.color, 0.35 + 0.65 * lab.v);
      ctx.fillText(lab.cv.name, lab.x, lab.y);
    }
    // events: expanding rings after they happen
    const win = eventWindowYears();
    for (const e of events) {
      const ph = (year - e.year) / win;
      if (ph < -0.15 || ph > 1) continue;
      const col = KIND_COLOR[e.k];
      if (ph < 0) {
        ctx.fillStyle = rgba(col, 0.5 * (1 + ph / 0.15));
        ctx.beginPath(); ctx.arc(e.px, e.py, 2, 0, TAU); ctx.fill();
        continue;
      }
      const a = 1 - ph;
      ctx.strokeStyle = rgba(col, a * 0.9); ctx.lineWidth = 1.5;
      ctx.beginPath(); ctx.arc(e.px, e.py, 4 + 26 * Math.sqrt(ph), 0, TAU); ctx.stroke();
      ctx.fillStyle = rgba(col, Math.min(1, a * 1.5));
      ctx.beginPath(); ctx.arc(e.px, e.py, 3, 0, TAU); ctx.fill();
      ctx.font = `600 ${fs}px "IBM Plex Sans"`;
      ctx.textAlign = e.px > w * 0.75 ? "right" : "left";
      const tx = e.px + (e.px > w * 0.75 ? -9 : 9);
      ctx.fillStyle = `rgba(6,9,32,${0.7 * a})`;
      const tw = ctx.measureText(e.n).width;
      ctx.fillRect(ctx.textAlign === "right" ? tx - tw - 3 : tx - 3, e.py - 14 - fs / 2 - 2, tw + 6, fs + 4);
      ctx.fillStyle = rgba(col, Math.min(1, a * 1.6));
      ctx.fillText(e.n, tx, e.py - 14);
    }
  }

  // ---------- timeline ----------
  const tl = { cv: $("timeline") };
  function buildTimeline() {
    const w = tl.cv.clientWidth;
    const gutter = w > 700 ? 150 : 8;
    const rowH = 5, rowGap = 2, laneGap = 7, top = 22, axisH = 18;
    // pack civs of each region into rows
    const lanes = [];
    let y = top;
    for (const rk of regionKeys) {
      const list = civs.filter((c) => c.region === rk).sort((a, b) => a.f - b.f);
      const rowEnds = [];
      for (const c of list) {
        let row = rowEnds.findIndex((end) => end + 25 < c.f);
        if (row < 0) { row = rowEnds.length; rowEnds.push(0); }
        rowEnds[row] = c.t; c.row = row;
      }
      const hLane = Math.max(1, rowEnds.length) * (rowH + rowGap);
      for (const c of list) { c.y = y + c.row * (rowH + rowGap); c.h = rowH; }
      lanes.push({ rk, y, h: hLane });
      y += hLane + laneGap;
    }
    const H_ = y + axisH;
    const { ctx, dpr } = fitCanvas(tl.cv, H_);
    const X = (yr) => gutter + (yr - Y_MIN) / (Y_MAX - Y_MIN) * (w - gutter - 26);
    Object.assign(tl, { ctx, w, h: H_, gutter, X, lanes, top });
    const L = makeLayer(w, H_, dpr), g = L.ctx;
    // axis
    g.font = '400 10.5px "IBM Plex Mono"'; g.textBaseline = "top"; g.textAlign = "center";
    const step = w > 900 ? 500 : 1000;
    for (let hy = -3000; hy <= 2000; hy += step) {
      const x = X(toAstro(hy || 1));
      g.strokeStyle = "rgba(120,140,230,0.12)"; g.beginPath(); g.moveTo(x, top - 4); g.lineTo(x, H_ - axisH + 2); g.stroke();
      g.fillStyle = "rgba(152,161,204,0.8)";
      g.fillText(hy < 0 ? `${-hy} BCE` : hy === 0 ? "1 CE" : `${hy} CE`, x, H_ - axisH + 5);
    }
    // lanes
    for (const ln of lanes) {
      g.fillStyle = "rgba(255,255,255,0.02)"; g.fillRect(gutter, ln.y - 2, w - gutter - 26, ln.h + 2);
      if (gutter > 20) {
        g.textAlign = "right"; g.textBaseline = "middle"; g.font = '500 11px "IBM Plex Sans"';
        g.fillStyle = rgba(H.regions[ln.rk].color, 0.9);
        g.fillText(H.regions[ln.rk].name, gutter - 10, ln.y + ln.h / 2 - 1);
      }
    }
    for (const c of civs) {
      const x0 = X(c.f), x1 = X(c.t), span = c.t - c.f;
      const ramp = Math.min(80, span * 0.25) / span;
      const gr = g.createLinearGradient(x0, 0, x1, 0);
      gr.addColorStop(0, rgba(c.color, 0.08)); gr.addColorStop(ramp, rgba(c.color, 0.7));
      gr.addColorStop(1 - ramp, rgba(c.color, 0.7)); gr.addColorStop(1, rgba(c.color, 0.08));
      g.fillStyle = gr; g.fillRect(x0, c.y, Math.max(1.5, x1 - x0), c.h);
    }
    // event ticks
    for (const e of events) {
      const x = X(e.year);
      g.fillStyle = rgba(KIND_COLOR[e.k], 0.75);
      g.fillRect(x - 0.75, 4, 1.5, 11);
    }
    tl.base = L;
  }

  function drawTimeline(year) {
    const { ctx, w, h, X, top } = tl;
    ctx.clearRect(0, 0, w, h);
    blit(ctx, tl.base);
    for (const c of civs) {
      const v = spanIntensity(c.f, c.t, year);
      if (!v) continue;
      ctx.strokeStyle = rgba(c.color, 0.9 * v); ctx.lineWidth = 1;
      ctx.strokeRect(X(c.f) + 0.5, c.y - 0.5, Math.max(1.5, X(c.t) - X(c.f)) - 1, c.h + 1);
    }
    const x = X(year);
    const lg = ctx.createLinearGradient(x - 14, 0, x + 14, 0);
    lg.addColorStop(0, "rgba(224,169,64,0)"); lg.addColorStop(0.5, "rgba(224,169,64,0.18)"); lg.addColorStop(1, "rgba(224,169,64,0)");
    ctx.fillStyle = lg; ctx.fillRect(x - 14, 0, 28, h - 18);
    ctx.strokeStyle = "#e0a940"; ctx.lineWidth = 1.5;
    ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x, h - 18); ctx.stroke();
    ctx.fillStyle = "#e0a940"; ctx.beginPath(); ctx.moveTo(x - 5, 0); ctx.lineTo(x + 5, 0); ctx.lineTo(x, 6); ctx.fill();
  }

  // ---------- time tape (jog dial) ----------
  const tape = { cv: $("tape") };
  function buildTape() { Object.assign(tape, fitCanvas(tape.cv)); }
  function tapeSpanDays() { return SPEEDS[state.speed].d * 10; }
  function drawTape() {
    const { ctx, w, h } = tape;
    ctx.clearRect(0, 0, w, h);
    const bg = ctx.createLinearGradient(0, 0, w, 0);
    bg.addColorStop(0, "rgba(14,19,48,0)"); bg.addColorStop(0.5, "rgba(30,38,90,0.9)"); bg.addColorStop(1, "rgba(14,19,48,0)");
    ctx.fillStyle = bg; ctx.fillRect(0, 0, w, h);
    const span = tapeSpanDays(), ppd = w / span, jd0 = state.jd - span / 2;
    const steps = [1, 7, 30.436875, 91.310625, 365.2425, 3652.425, 36524.25, 365242.5];
    const minor = steps.find((s) => s * ppd >= 8) || steps[steps.length - 1];
    const major = steps.find((s) => s * ppd >= 64) || steps[steps.length - 1];
    const drawTicks = (step, len, alpha, label) => {
      const yearMode = step >= 365;
      const stepU = yearMode ? step / 365.2425 : step;
      const u0 = yearMode ? A.jdToYearFloat(jd0) : jd0;
      const first = Math.ceil(u0 / stepU) * stepU;
      ctx.font = '400 10.5px "IBM Plex Mono"'; ctx.textAlign = "center"; ctx.textBaseline = "top";
      for (let u = first; ; u += stepU) {
        const jd = yearMode ? A.yearFloatToJd(u) : u + 0.5;
        const x = (jd - jd0) * ppd;
        if (x > w) break;
        const fade = 1 - Math.abs(x - w / 2) / (w / 2);
        ctx.strokeStyle = `rgba(170,185,255,${alpha * fade})`; ctx.lineWidth = 1;
        ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x, len); ctx.stroke();
        if (label) {
          const c = A.jdToCalendar(jd);
          const txt = yearMode ? histYearLabel(Math.round(u)) : step < 30 ? `${c.day} ${MONTHS[c.month - 1]}` : `${MONTHS[c.month - 1]} ${histYearLabel(c.year)}`;
          ctx.fillStyle = `rgba(200,208,240,${0.9 * fade})`;
          ctx.fillText(txt, x, len + 4);
        }
      }
    };
    drawTicks(minor, 8, 0.45, false);
    drawTicks(major, 16, 0.9, true);
    const cx = w / 2;
    ctx.strokeStyle = "#e0a940"; ctx.lineWidth = 2;
    ctx.shadowColor = "#e0a940"; ctx.shadowBlur = 10;
    ctx.beginPath(); ctx.moveTo(cx, 0); ctx.lineTo(cx, h); ctx.stroke();
    ctx.shadowBlur = 0;
  }

  // ---------- text panels ----------
  const rows = {};
  (function buildTable() {
    const tb = $("graha-rows");
    for (const k of TABLE_ORDER) {
      const tr = document.createElement("tr");
      tr.innerHTML = `<td><span class="sw" style="background:${GRAHA[k].color};box-shadow:0 0 6px ${GRAHA[k].color}"></span>${GRAHA[k].label}</td><td class="rashi"></td><td class="deg"></td><td class="nak"></td><td class="retro"></td>`;
      tb.appendChild(tr);
      rows[k] = { rashi: tr.children[1], deg: tr.children[2], nak: tr.children[3], retro: tr.children[4] };
    }
  })();

  (function buildLegend() {
    const lg = $("legend");
    lg.innerHTML = regionKeys.map((k) => `<span><span class="sw" style="background:${H.regions[k].color}"></span>${H.regions[k].name}</span>`).join("")
      + Object.keys(KIND_COLOR).map((k) => `<span><span class="sw" style="background:transparent;border:1.5px solid ${KIND_COLOR[k]}"></span>${KIND_LABEL[k]}</span>`).join("");
  })();

  function setText(el, txt) { if (el.textContent !== txt) el.textContent = txt; }
  function setHTML(el, html) { if (el._html !== html) { el.innerHTML = html; el._html = html; } }

  function updatePanels(pos, year) {
    setText($("date"), fmtDate(state.jd));
    setText($("date-sub"), `${state.jd < 2299160.5 ? "Julian" : "Gregorian"} calendar · JD ${state.jd.toFixed(1)}`);

    const plus = A.grahas(state.jd + 0.5), minus = A.grahas(state.jd - 0.5);
    for (const k of TABLE_ORDER) {
      const lon = pos[k], nk = nakOf(lon), rr = rows[k];
      setText(rr.rashi, RASHIS[Math.floor(lon / 30)]);
      setText(rr.deg, fmtDeg(lon));
      setText(rr.nak, `${NAKS[nk.i]} ${nk.pada}`);
      const retro = k !== "Rahu" && k !== "Ketu" && ((plus[k] - minus[k] + 540) % 360) - 180 < 0;
      setText(rr.retro, retro ? "vakri ℞" : "");
    }

    const ayan = A.ayanamsha(state.jd), eq = A.norm(-ayan), eqNak = nakOf(eq);
    const facts = [
      `<span class="pill">Equinox in <b>${NAKS[eqNak.i]}</b> · ${RASHIS[Math.floor(eq / 30)]} ${fmtDeg(eq).trim()}</span>`,
      `<span class="pill">Ayanamsha <b>${ayan.toFixed(2)}°</b></span>`,
    ];
    if (state.speed <= 1) {
      const elong = A.norm(pos.Chandra - pos.Surya), t = Math.floor(elong / 12);
      facts.push(`<span class="pill">Tithi <b>${t < 15 ? "Shukla" : "Krishna"} ${(t % 15) + 1}</b></span>`);
      const nodeDist = Math.min(angDist(pos.Surya, pos.Rahu), angDist(pos.Surya, pos.Ketu));
      if (nodeDist < 15) {
        let kind = "Eclipse season";
        if (elong < 10 || elong > 350) kind = "Solar eclipse likely";
        else if (Math.abs(elong - 180) < 10) kind = "Lunar eclipse likely";
        facts.push(`<span class="pill hot">${kind}</span>`);
      }
    }
    setHTML($("sky-facts"), facts.join(""));

    // event card: latest event at or before now, plus the next one
    let prev = null, next = null;
    for (const e of events) { if (e.jd <= state.jd + 0.5) prev = e; else { next = e; break; } }
    const recent = prev && year - prev.year < Math.max(120, eventWindowYears() * 3);
    let html = `<div class="label">${recent ? "Latest event" : "Between events"}</div>`;
    if (recent) {
      html += `<div class="ev-title" style="color:${KIND_COLOR[prev.k]}">${prev.n}</div><div class="ev-meta">${prev.when} · ${KIND_LABEL[prev.k]}</div><div class="ev-desc">${prev.d}</div>`;
    } else {
      html += `<div class="ev-desc">No major event in the dataset for this stretch of time.</div>`;
    }
    if (next) {
      const dy = next.year - year;
      const inTxt = dy < 1 ? `in ${Math.max(1, Math.round(dy * 365))} days` : `in ${Math.round(dy)} years`;
      html += `<div class="next">Next: ${next.n}, ${inTxt}<button data-jump="${events.indexOf(next)}">Go</button></div>`;
    }
    setHTML($("event-card"), html);

    const active = civs.map((c) => ({ c, v: spanIntensity(c.f, c.t, year) })).filter((x) => x.v > 0).sort((a, b) => b.v - a.v);
    setText($("civ-count"), `${active.length} active`);
    setHTML($("active-civs"), active.length
      ? active.map(({ c, v }) => `<span class="chip" style="border-color:${rgba(c.color, 0.25 + 0.6 * v)};color:${rgba(c.color, 0.5 + 0.5 * v)}">${c.name}</span>`).join("")
      : `<span class="ev-desc" style="color:var(--text-faint)">None in the dataset.</span>`);
  }

  // ---------- controls ----------
  const playBtn = $("play");
  function setPlaying(p) {
    state.playing = p;
    playBtn.textContent = p ? "❚❚ Pause" : "▶ Play";
    playBtn.setAttribute("aria-label", p ? "Pause" : "Play");
  }
  playBtn.onclick = () => {
    if (!state.playing && ((state.dir > 0 && state.jd >= JD_MAX) || (state.dir < 0 && state.jd <= JD_MIN))) state.dir = -state.dir, syncReverse();
    setPlaying(!state.playing);
  };
  function syncReverse() { $("reverse").setAttribute("aria-pressed", String(state.dir < 0)); }
  $("reverse").onclick = () => { state.dir = -state.dir; syncReverse(); };
  const step = (n) => { setJd(state.jd + n * SPEEDS[state.speed].d); };
  $("step-back").onclick = () => step(-1);
  $("step-fwd").onclick = () => step(1);
  $("to-start").onclick = () => { setJd(JD_MIN); };

  const speedsEl = $("speeds");
  SPEEDS.forEach((s, i) => {
    const b = document.createElement("button");
    b.textContent = s.label; b.dataset.i = i;
    b.onclick = () => { state.speed = i; syncSpeeds(); };
    speedsEl.appendChild(b);
  });
  function syncSpeeds() { for (const b of speedsEl.children) b.setAttribute("aria-pressed", String(+b.dataset.i === state.speed)); }
  syncSpeeds();

  const jumpEl = $("jump");
  jumpEl.innerHTML = `<option value="">Jump to an event…</option>` + events.map((e, i) => `<option value="${i}">${e.when} — ${e.n}</option>`).join("");
  function jumpTo(i) {
    const e = events[i]; if (!e) return;
    setJd(e.jd - (e.exact ? 0 : 0));
    setPlaying(false);
    if (e.exact && state.speed > 1) state.speed = 0;
    if (!e.exact && state.speed < 2) state.speed = 2;
    syncSpeeds();
  }
  jumpEl.onchange = () => { jumpTo(+jumpEl.value); jumpEl.value = ""; };
  $("event-card").addEventListener("click", (ev) => { const b = ev.target.closest("[data-jump]"); if (b) jumpTo(+b.dataset.jump); });

  for (const b of $("views").children) {
    b.onclick = () => {
      state.view = b.dataset.view;
      for (const o of $("views").children) o.setAttribute("aria-pressed", String(o === b));
      buildMap();
    };
  }

  document.addEventListener("keydown", (e) => {
    if (e.target.tagName === "SELECT" || e.target.tagName === "INPUT") return;
    if (e.code === "Space") { e.preventDefault(); playBtn.click(); }
    else if (e.key === "ArrowRight") { e.preventDefault(); step(e.shiftKey ? 10 : 1); }
    else if (e.key === "ArrowLeft") { e.preventDefault(); step(e.shiftKey ? -10 : -1); }
    else if (e.key === "r" || e.key === "R") $("reverse").click();
  });

  // tape drag with inertia
  {
    let lastX = 0, lastT = 0, vel = 0;
    tape.cv.addEventListener("pointerdown", (e) => {
      tape.cv.setPointerCapture(e.pointerId); state.dragging = true; state.inertia = 0;
      lastX = e.clientX; lastT = performance.now(); vel = 0;
    });
    tape.cv.addEventListener("pointermove", (e) => {
      if (!state.dragging) return;
      const now = performance.now(), dx = e.clientX - lastX;
      const dDays = -dx * tapeSpanDays() / tape.w;
      setJd(state.jd + dDays);
      const dt = Math.max(1, now - lastT) / 1000;
      vel = 0.7 * vel + 0.3 * (dDays / dt);
      lastX = e.clientX; lastT = now;
    });
    const end = () => { if (state.dragging) { state.dragging = false; state.inertia = performance.now() - lastT < 80 ? vel : 0; } };
    tape.cv.addEventListener("pointerup", end);
    tape.cv.addEventListener("pointercancel", end);
    tape.cv.addEventListener("wheel", (e) => { e.preventDefault(); setJd(state.jd + (e.deltaY + e.deltaX) * tapeSpanDays() / tape.w); }, { passive: false });
  }

  // timeline scrub + hover
  const tip = $("tip");
  function showTip(e, html) { tip.innerHTML = html; tip.style.display = "block"; const x = Math.min(e.clientX + 14, window.innerWidth - 270); tip.style.left = x + "px"; tip.style.top = (e.clientY + 14) + "px"; }
  const hideTip = () => { tip.style.display = "none"; };
  {
    let down = false;
    const yearAt = (e) => { const r = tl.cv.getBoundingClientRect(); return Y_MIN + (e.clientX - r.left - tl.gutter) / (tl.w - tl.gutter - 26) * (Y_MAX - Y_MIN); };
    tl.cv.addEventListener("pointerdown", (e) => { down = true; tl.cv.setPointerCapture(e.pointerId); setJd(A.yearFloatToJd(yearAt(e))); });
    tl.cv.addEventListener("pointermove", (e) => {
      if (down) { setJd(A.yearFloatToJd(yearAt(e))); hideTip(); return; }
      const r = tl.cv.getBoundingClientRect(), mx = e.clientX - r.left, my = e.clientY - r.top;
      if (my < tl.top - 4) {
        let best = null, bd = 5;
        for (const ev of events) { const d = Math.abs(tl.X(ev.year) - mx); if (d < bd) { bd = d; best = ev; } }
        return best ? showTip(e, `<b>${best.n}</b><div class="m">${best.when}</div>`) : hideTip();
      }
      const c = civs.find((c) => my >= c.y - 1 && my <= c.y + c.h + 1 && mx >= tl.X(c.f) - 1 && mx <= tl.X(c.t) + 1);
      c ? showTip(e, `<b style="color:${c.color}">${c.name}</b><div class="m">${c.spanLabel}</div>`) : hideTip();
    });
    const up = () => { down = false; };
    tl.cv.addEventListener("pointerup", up);
    tl.cv.addEventListener("pointercancel", up);
    tl.cv.addEventListener("pointerleave", hideTip);
  }

  // map hover
  map.cv.addEventListener("pointermove", (e) => {
    const r = map.cv.getBoundingClientRect(), mx = e.clientX - r.left, my = e.clientY - r.top;
    const year = A.jdToYearFloat(state.jd);
    const hits = [];
    for (const c of civs) {
      if (!spanIntensity(c.f, c.t, year)) continue;
      if (c.lobes.some((lb) => spanIntensity(lb.f, lb.t, year) && Math.hypot(lb.px - mx, lb.py - my) < lb.pr * 0.8)) hits.push(c);
    }
    const win = eventWindowYears();
    const evs = events.filter((ev) => { const ph = (year - ev.year) / win; return ph >= 0 && ph <= 1 && Math.hypot(ev.px - mx, ev.py - my) < 12; });
    if (!hits.length && !evs.length) return hideTip();
    showTip(e, evs.map((ev) => `<b style="color:${KIND_COLOR[ev.k]}">${ev.n}</b><div class="m">${ev.when}</div><div>${ev.d}</div>`).join("")
      + hits.map((c) => `<div><b style="color:${c.color}">${c.name}</b> <span class="m">${c.spanLabel}</span></div>`).join(""));
  });
  map.cv.addEventListener("pointerleave", hideTip);

  // ---------- main loop ----------
  function buildAll() { buildSky(); buildMap(); buildTimeline(); buildTape(); }
  let resizeTimer = 0;
  window.addEventListener("resize", () => { clearTimeout(resizeTimer); resizeTimer = setTimeout(buildAll, 120); });

  let last = performance.now(), lastPanel = 0;
  function frame(now) {
    const dt = Math.min(0.1, (now - last) / 1000); last = now;
    if (state.dragging) {
      // scrubbing
    } else if (Math.abs(state.inertia) > 0.01) {
      setJd(state.jd + state.inertia * dt);
      state.inertia *= Math.pow(0.04, dt);
      if (Math.abs(state.inertia) < SPEEDS[state.speed].d * 0.02) state.inertia = 0;
    } else if (state.playing) {
      setJd(state.jd + SPEEDS[state.speed].d * dt * state.dir);
      if (state.jd >= JD_MAX || state.jd <= JD_MIN) setPlaying(false);
    }
    const pos = A.grahas(state.jd), year = A.jdToYearFloat(state.jd);
    drawSky(pos);
    drawMap(year);
    drawTimeline(year);
    drawTape();
    if (now - lastPanel > 90) { updatePanels(pos, year); lastPanel = now; }
    requestAnimationFrame(frame);
  }

  buildAll();
  setPlaying(state.playing);
  requestAnimationFrame(frame);

  // world land outline (optional; the page still works without it)
  if (window.topojson) {
    fetch("https://cdn.jsdelivr.net/npm/world-atlas@2/land-110m.json")
      .then((r) => r.json())
      .then((topo) => { map.land = topojson.feature(topo, topo.objects.land); buildMap(); })
      .catch((err) => console.warn("land outline unavailable", err));
  }
  document.fonts && document.fonts.ready.then(() => buildSky());
})();
