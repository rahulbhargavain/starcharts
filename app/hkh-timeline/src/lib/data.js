// astro.js / calendars.js / history.js are UMD-style scripts shared with the
// Python test suite (which `require()`s them directly from demo/hkh_timeline
// and demo/cosmic_timeline). They're loaded as classic <script> tags in
// index.html -- NOT imported here -- because Rollup's commonjs interop
// wraps a bare ES import of a UMD file in a module.exports shim that steals
// their own browser-vs-Node branch (their `typeof module !== "undefined"`
// check then sees Rollup's shim and never sets window.Astro/etc). Classic
// scripts execute before this deferred module script, so by the time this
// runs, window.Astro / window.Calendars / window.HKH are already set.
if (!window.Astro || !window.Calendars || !window.HKH) {
  throw new Error(
    "astro.js/calendars.js/history.js did not load -- check the <script> tags in index.html run before main.jsx"
  );
}

export const Astro = window.Astro;
export const Calendars = window.Calendars;
export const HKH = window.HKH;
