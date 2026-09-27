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
  },
  server: {
    fs: { allow: [".."] },
  },
});
