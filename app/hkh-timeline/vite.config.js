import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// Builds straight into demo/hkh_timeline/, alongside calendars.js, history.js,
// and boundaries_ind.json -- those stay put because Python tests and
// scripts/build_hkh_boundaries.py reference them at that exact path.
// emptyOutDir is false so `vite build` never deletes them.
export default defineConfig({
  plugins: [react()],
  base: "./",
  build: {
    outDir: "../../demo/hkh_timeline",
    emptyOutDir: false,
    assetsDir: "assets",
    // Vite's default target ("modules") assumes native ES module support but
    // doesn't downlevel newer syntax (optional chaining, nullish coalescing)
    // for older engines within that range. es2017 is the widest baseline
    // that still covers async/await; esbuild lowers the rest for it,
    // covering older mobile Safari/WebView releases that otherwise show a
    // blank page on a parse error with no visible message.
    target: "es2017",
  },
  server: {
    fs: { allow: [".."] },
  },
});
