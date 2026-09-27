import { useEffect } from "react";
import { mountEngine } from "./lib/engine.js";

export default function App() {
  useEffect(() => {
    const unmount = mountEngine();
    return unmount;
  }, []);

  return (
    <div className="wrap">
      <header>
        <h1>Hindu Kush Himalaya · a calendar timeline</h1>
        <div className="tagline">
          Settlements, states and events of the mountains from Afghanistan to Myanmar, 7000 BCE to today, dated in
          the calendars of the eight ICIMOD member countries, with India in focus. Companion to the{" "}
          <a href="../cosmic_timeline/">Cosmic Timeline</a>.
        </div>
      </header>

      <div className="grid">
        <section className="panel" aria-label="Sky and date">
          <div className="head">
            <h2>Sky</h2>
            <div className="sky-controls">
              <div className="seg" id="sky-tabs" role="group" aria-label="Sky perspective">
                <button data-sky="sun" aria-pressed="true">Sun</button>
                <button data-sky="iso" aria-pressed="false">Isometric</button>
              </div>
              <div className="seg" id="sky-zooms" role="group" aria-label="Orbit zoom">
                <button data-zoom="inner" aria-pressed="false">Inner</button>
                <button data-zoom="full" aria-pressed="true">Full</button>
              </div>
              <button id="sky-reset" title="Reset tilt, zoom and pan">Reset</button>
            </div>
          </div>
          <div id="date">—</div>
          <div id="date-sub">—</div>
          <canvas
            id="moon-mini" role="img" tabIndex={0}
            aria-label="The Sun at centre with Mercury, Venus, Earth, Mars, Jupiter and Saturn on their real orbits, a month ring and a season ring framing Earth's path, and the Moon and lunar nodes beside Earth. Switch to Isometric and drag to tilt (shift-drag to pan); scroll to zoom; drag in Sun view to pan."
          />
          <div id="moon-label" className="moon-label">—</div>
          <div className="card" id="event-card" />
        </section>

        <section className="panel" aria-label="Map">
          <div className="head">
            <h2>
              Settlements &amp; states <small id="counts" />
            </h2>
            <div className="map-controls">
              <div className="seg" id="map-overlays" role="group" aria-label="Map overlays">
                <button data-overlay="climate" aria-pressed="true" title="Paleoclimate drought & pluvial reconstruction (MADA 1300–2005 CE)">Drought</button>
              </div>
              <div className="seg" id="views" role="group" aria-label="Map extent">
                <button data-view="india" aria-pressed="false">Indian Himalaya</button>
                <button data-view="hkh" aria-pressed="true">Whole HKH</button>
              </div>
            </div>
          </div>
          <canvas id="map" role="img" aria-label="Map of the Hindu Kush Himalaya at the current date" />
          <div className="legend" id="legend" />
          <div className="card">
            <div className="label">States at this date</div>
            <div className="chips" id="active" />
          </div>
        </section>
      </div>

      <section className="panel" aria-label="Calendars">
        <div className="head">
          <h2>
            Calendars
            <span className="seg mini-transport" role="group" aria-label="Time controls">
              <button id="step-back-mini" title="Step back" aria-label="Step back">&#9664;</button>
              <button id="play-mini" aria-label="Play">&#9654;</button>
              <button id="step-fwd-mini" title="Step forward" aria-label="Step forward">&#9654;</button>
            </span>
          </h2>
          <select id="cal-mode" aria-label="Group calendars by" defaultValue="type">
            <option value="type">By type (solar / lunisolar / lunar)</option>
            <option value="country">By country</option>
          </select>
        </div>
        <div className="cal-controls">
          <label className="cal-toggle">
            <input type="checkbox" id="show-pro" /> show calendars not yet in use
          </label>
        </div>
        <div className="cal-controls">
          <span className="cal-controls-label">Countries:</span>
          <div className="seg-check" id="cal-filters" />
        </div>
        <div id="calendars" aria-live="off" />
      </section>

      <section className="panel" aria-label="Time controls">
        <div className="controls">
          <button id="step-back" title="Step back" aria-label="Step back">&#9664;</button>
          <button id="play" aria-label="Play">&#9654; Play</button>
          <button id="step-fwd" title="Step forward" aria-label="Step forward">&#9654;</button>
          <div className="seg" id="speeds" role="group" aria-label="Playback speed" />
          <div className="spacer" />
          <select id="jump" aria-label="Jump to an event" />
        </div>
        <canvas id="timeline" aria-label="Timeline by country: states, settlements and events. Click or drag to set the date." />
      </section>

      <section className="panel">
        <details id="table-section">
          <summary>All events</summary>
          <div className="filters" id="filters" />
          <div className="table-wrap">
            <table className="events">
              <thead>
                <tr>
                  <th>Date</th>
                  <th>Event</th>
                  <th>Calendar</th>
                </tr>
              </thead>
              <tbody id="rows" />
            </table>
          </div>
        </details>
      </section>

      <footer>
        <p>
          <b>How dates are computed.</b> Every calendar is worked out in the browser. The Indian lunisolar, Nepal
          Sambat, Bikram Sambat, Bengali, Solar Hijri and Chinese dates come from the Sun and Moon (Lahiri ayanamsha,
          amanta months), checked against the project's Python engine and published new-year dates. The Indian
          national, Bangla, Hijri and Myanmar Era dates are arithmetic. Days are counted from local midnight, so
          dates within a day of a sankranti, new moon or equinox can differ by one from a printed almanac. Hijri
          dates are tabular: in practice months start on moon sighting. Tibetan and Bhutanese dates are given to the
          year only, and are marked ambiguous near Losar. A calendar tagged <i>not yet in use</i> is being counted
          backwards (proleptic). Indian lunisolar month names before c. 500 CE, and Chinese months before 1645,
          follow later rules than were in force at the time. By default, an event shows only its own country's
          calendar (alongside the Julian/Gregorian date already given) — tick "show correspondence with other
          calendars" on an event to see how every calendar in use at the time read that same day. The season band
          around Earth's orbit is drawn at fixed points in the tropical (Sun-relative) year. The map's Drought
          overlay is a reconstruction of actual past conditions (MADA, see below), not a seasonal schematic.
        </p>
        <p>
          <b>Dates and places.</b> Dates marked c. are approximate or traditional. Terrain is NASA's Blue Marble
          shaded relief (via NASA GIBS); rivers are Natural Earth 1:50m centrelines (hover a river for its name).
          The dried-up Ghaggar-Hakra and Chautang are traced by hand along their palaeochannels; both their drying
          date and their identification with the Vedic Sarasvati and Drishadvati are debated. The coloured areas for
          states are schematic, not borders. Country boundaries follow the Government of India's official map
          (Natural Earth's India worldview): all of Jammu &amp; Kashmir and Ladakh, including the areas administered
          by Pakistan and China, and Arunachal Pradesh are shown as India, and Tibet as part of China. Pakistan and
          China depict parts of these boundaries differently. Events are assigned to countries on the same basis.{" "}
          <kbd>Space</kbd> play/pause · <kbd>&#8592;</kbd>
          <kbd>&#8594;</kbd> step.
        </p>
        <p>
          <b>Paleoclimate &amp; thermal reconstructions.</b> Regional hydroclimate data across the Common Era (0–2020 CE) is from
          the <i>Great Eurasian Drought Atlas</i> (GEDA; Cook et al., NOAA NCEI Paleoclimatology / Lamont-Doherty Earth
          Observatory), providing reconstructed summer (June–July–August) Palmer Drought Severity Index (PDSI) and the
          Drought Area Index (DAI, proportion of the Himalayan-Indic domain experiencing drought). Spatially gridded
          drought and pluvial anomalies (1300–2005 CE) are from the <i>Monsoon Asia Drought Atlas</i> (MADA; Cook et al.
          2010, Science 328:486–489), based on tree-ring chronologies across Asia calibrated against instrumental
          PDSI. Continuous Common Era thermal anomaly spine (1–2000 CE proxy ensemble median, extended to 2017 CE with Cowtan &amp; Way instrumental)
          is from the <i>PAGES 2k Consortium</i> (Neukom et al. 2019, Nature Geoscience 12:643–649, NOAA NCEI Study 26804).
        </p>
      </footer>
      <div id="tip" />
    </div>
  );
}
