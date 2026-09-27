"""
Parse Monsoon Asia Drought Atlas (MADA), Great Eurasian Drought Atlas (GEDA),
and PAGES2k Global Temperature Anomaly (Neukom et al. 2019) datasets for the
Hindu Kush Himalaya (HKH) calendar timeline.

Produces mada_hkh.json containing:
1. Spatial MADA grid (1300-2005 CE) clipped to the HKH bounding box (15N-40N, 60E-105E).
2. Regional GEDA 0-2020 CE time-series (PDSI, 10-year spline, Drought Area Index (DAI), and DAI spline).
3. PAGES2k 1-2017 CE Global Mean Surface Temperature anomalies (ensemble median and 31-year filtered).
"""

import os
import json

def parse_paleoclimate(
    mada_txt="review/jja-mada.txt",
    xy_txt="review/jja-mada-xy.txt",
    geda_pdsi_txt="review/GEDA_Reconstructed_JJA_PDSI_0_2020.txt",
    geda_dai_txt="review/GEDA_Reconstructed_JJA_PDSI_0_2020 (1).txt",
    pages2k_txt="review/PAGES2k_Neukom2019_Full_ensemble.txt",
    output_files=None,
    lon_min=60.0,
    lon_max=105.0,
    lat_min=15.0,
    lat_max=40.0
):
    print("--- Parsing Paleoclimate & Thermal Datasets (MADA + GEDA + PAGES2k) ---")
    
    # 1. Parse coordinates & filter to HKH domain
    if not os.path.exists(xy_txt):
        raise FileNotFoundError(f"Missing coordinate file: {xy_txt}")
    
    with open(xy_txt, "r", encoding="utf-8", errors="replace") as f:
        all_pts = [list(map(float, line.strip().split())) for line in f if line.strip()]
    
    hkh_indices = [
        i for i, (lon, lat) in enumerate(all_pts)
        if lon_min <= lon <= lon_max and lat_min <= lat <= lat_max
    ]
    hkh_pts = [[round(all_pts[i][0], 2), round(all_pts[i][1], 2)] for i in hkh_indices]
    print(f"Filtered {len(hkh_pts)} HKH stations out of {len(all_pts)} Asian stations.")
    
    # 2. Parse spatial MADA PDSI table (1300 - 2005 CE)
    if not os.path.exists(mada_txt):
        raise FileNotFoundError(f"Missing MADA reconstruction file: {mada_txt}")
    
    mada_data = {}
    with open(mada_txt, "r", encoding="utf-8", errors="replace") as f:
        f.readline() # Header
        for line in f:
            parts = line.strip().split()
            if not parts:
                continue
            year = int(parts[0])
            row = []
            for idx in hkh_indices:
                val = float(parts[idx + 1])
                row.append(-99 if val < -90 else round(val, 1))
            mada_data[year] = row
            
    years_mada = sorted(list(mada_data.keys()))
    print(f"Parsed MADA spatial grid: {len(years_mada)} years ({years_mada[0]} to {years_mada[-1]} CE).")

    # 3. Parse GEDA regional mean PDSI (0 - 2020 CE)
    if not os.path.exists(geda_pdsi_txt):
        raise FileNotFoundError(f"Missing GEDA PDSI file: {geda_pdsi_txt}")
        
    geda_pdsi = {}
    with open(geda_pdsi_txt, "r", encoding="utf-8", errors="replace") as f:
        lines = [line.strip() for line in f if line.strip()][3:]
        for line in lines:
            parts = line.split("\t")
            if len(parts) >= 3:
                yr = int(parts[0])
                geda_pdsi[yr] = (round(float(parts[1]), 2), round(float(parts[2]), 2))
                
    # 4. Parse GEDA Drought Area Index (DAI, 0 - 2020 CE)
    if not os.path.exists(geda_dai_txt):
        raise FileNotFoundError(f"Missing GEDA DAI file: {geda_dai_txt}")
        
    geda_dai = {}
    with open(geda_dai_txt, "r", encoding="utf-8", errors="replace") as f:
        lines = [line.strip() for line in f if line.strip()][3:]
        for line in lines:
            parts = line.split("\t")
            if len(parts) >= 3:
                yr = int(parts[0])
                geda_dai[yr] = (round(float(parts[1]), 3), round(float(parts[2]), 3))

    years_geda = sorted(list(geda_pdsi.keys()))
    print(f"Parsed GEDA regional series: {len(years_geda)} years ({years_geda[0]} to {years_geda[-1]} CE).")

    # 5. Parse PAGES2k Global Temperature Anomaly (1 - 2017 CE)
    pages2k_payload = None
    if os.path.exists(pages2k_txt):
        with open(pages2k_txt, "r", encoding="utf-8", errors="replace") as f:
            p2k_lines = [line.strip().split("\t") for line in f if line.strip() and not line.startswith("##")]
        
        # p2k_lines[0] is column headers
        p2k_rows = p2k_lines[1:]
        p2k_years = []
        p2k_temp = []
        p2k_31yr = []
        for r in p2k_rows:
            yr = int(r[0])
            inst = float(r[1]) if r[1] != "NA" else None
            med = float(r[2]) if r[2] != "NA" else None
            med31 = float(r[6]) if len(r) > 6 and r[6] != "NA" else None
            
            # Reconstruction median when available; instrumental Cowtan & Way for modern extension
            t_val = med if med is not None else inst
            p2k_years.append(yr)
            p2k_temp.append(round(t_val, 2) if t_val is not None else None)
            p2k_31yr.append(round(med31, 2) if med31 is not None else None)
            
        pages2k_payload = {
            "startYear": p2k_years[0],
            "endYear": p2k_years[-1],
            "temp": p2k_temp,
            "temp31": p2k_31yr
        }
        print(f"Parsed PAGES2k temperature series: {len(p2k_years)} years ({p2k_years[0]} to {p2k_years[-1]} CE).")
    
    # 6. Assemble combined payload
    payload = {
        "points": hkh_pts,
        "years": years_mada,
        "data": mada_data,
        "geda": {
            "startYear": years_geda[0],
            "endYear": years_geda[-1],
            "pdsi": [geda_pdsi[y][0] for y in years_geda],
            "pdsiSpline": [geda_pdsi[y][1] for y in years_geda],
            "dai": [geda_dai[y][0] for y in years_geda],
            "daiSpline": [geda_dai[y][1] for y in years_geda]
        }
    }
    if pages2k_payload:
        payload["pages2k"] = pages2k_payload
    
    json_bytes = json.dumps(payload, separators=(',', ':'))
    print(f"Compiled JSON payload: {len(json_bytes) / 1024:.1f} KB")

    if output_files is None:
        output_files = [
            "starcharts/app/hkh-timeline/public/mada_hkh.json",
            "starcharts/demo/hkh_timeline/mada_hkh.json",
            "review/hkh_timeline/mada_hkh.json"
        ]
        
    for out_path in output_files:
        os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(json_bytes)
        print(f"Wrote {out_path} ({len(json_bytes) / 1024:.1f} KB)")

if __name__ == "__main__":
    script_dir = os.path.dirname(os.path.abspath(__file__))
    root_candidates = [
        os.getcwd(),
        os.path.abspath(os.path.join(script_dir, "..")),
        os.path.abspath(os.path.join(script_dir, "..", "..")),
    ]
    review_dir = None
    for r in root_candidates:
        cand = os.path.join(r, "review")
        if os.path.exists(os.path.join(cand, "jja-mada-xy.txt")):
            review_dir = cand
            break
            
    if not review_dir:
        raise FileNotFoundError("Could not locate review/ directory containing paleoclimate data.")
        
    mada_file = os.path.join(review_dir, "jja-mada.txt")
    xy_file = os.path.join(review_dir, "jja-mada-xy.txt")
    geda_file = os.path.join(review_dir, "GEDA_Reconstructed_JJA_PDSI_0_2020.txt")
    geda_dai_file = os.path.join(review_dir, "GEDA_Reconstructed_JJA_PDSI_0_2020 (1).txt")
    p2k_file = os.path.join(review_dir, "PAGES2k_Neukom2019_Full_ensemble.txt")
    
    # Locate starcharts repo root
    starcharts_dir = None
    for r in root_candidates:
        if os.path.exists(os.path.join(r, "app", "hkh-timeline")):
            starcharts_dir = r
            break
        if os.path.exists(os.path.join(r, "starcharts", "app", "hkh-timeline")):
            starcharts_dir = os.path.join(r, "starcharts")
            break

    output_destinations = []
    if starcharts_dir:
        output_destinations.append(os.path.join(starcharts_dir, "app", "hkh-timeline", "public", "mada_hkh.json"))
        output_destinations.append(os.path.join(starcharts_dir, "demo", "hkh_timeline", "mada_hkh.json"))
    output_destinations.append(os.path.join(review_dir, "hkh_timeline", "mada_hkh.json"))
    
    parse_paleoclimate(
        mada_txt=mada_file,
        xy_txt=xy_file,
        geda_pdsi_txt=geda_file,
        geda_dai_txt=geda_dai_file,
        pages2k_txt=p2k_file,
        output_files=output_destinations
    )
