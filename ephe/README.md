# Swiss Ephemeris data files

`starcharts.ephemeris` uses the file-free Moshier analytical model by
default (valid ~3002 BCE to ~3003 CE). Outside that range, it
automatically falls back to the full Swiss Ephemeris data files in this
directory -- but only for whatever span you've actually downloaded here.

These `.se1` files are binary and not committed to the repo (see
`.gitignore`). Run `download.sh` to fetch the set this project currently
relies on: planet + moon files covering ~5400 BCE to ~2400 BCE, which
combined with Moshier's native range gives continuous real-ephemeris
coverage from ~5400 BCE through ~3003 CE.

## Naming convention

Each file covers a 600-year block. `sepl_XX.se1` / `semo_XX.se1` are the
planet/moon files for the CE block starting at year `XX * 100`; the `m`
variants (`seplmXX.se1` / `semomXX.se1`) are the BCE blocks starting at
year `-(XX * 100)`. E.g. `seplm54.se1` covers roughly 5400-4801 BCE.
(`seas`/`seasm` files are for numbered asteroids -- not needed here,
since this project only uses the seven classical grahas, Sun-Saturn.)

## Reaching further back than ~5400 BCE

Download more `m` files of the same kind from the public Swiss Ephemeris
repo (https://github.com/aloistr/swisseph/tree/master/ephe) for whatever
block you need, e.g. `seplm60.se1` + `semom60.se1` for ~6000-5401 BCE,
and add them to `download.sh` so the fetch stays reproducible.

## Where starcharts looks for them

This directory, when running from a source checkout or an editable
install (`pip install -e .`). With a regular install the package lives in
`site-packages`, so set `STARCHARTS_EPHE_DIR` to wherever you keep the
files; `download.sh` honours the same variable:

```bash
export STARCHARTS_EPHE_DIR=~/starcharts-ephe
bash ephe/download.sh
```

## License

The Swiss Ephemeris, including these data files, is AGPL/dual-licensed
by Astrodienst, and starcharts is AGPL-3.0-or-later accordingly. See
"Decisions" in `WORKPLAN.md` for the permissively licensed alternative
(`openephem` with JPL kernels) if that ever matters.
