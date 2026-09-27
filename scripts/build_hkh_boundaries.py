"""Build demo/hkh_timeline/boundaries_ind.json from Natural Earth's India worldview.

The HKH timeline draws country outlines as the Government of India's official
map shows them: all of Jammu & Kashmir and Ladakh (including the areas
administered by Pakistan and China) and Arunachal Pradesh as India, Tibet as
China. Natural Earth publishes that point of view only at 1:10m (~13 MB), so
this keeps the countries around the Hindu Kush Himalaya and simplifies them
to a size the page can load.

Usage:
    curl -L -o ne_ind.geojson https://cdn.jsdelivr.net/gh/nvkelso/natural-earth-vector@master/geojson/ne_10m_admin_0_countries_ind.geojson
    python scripts/build_hkh_boundaries.py ne_ind.geojson
"""

import json
import sys
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "demo" / "hkh_timeline" / "boundaries_ind.json"
BBOX = (50.0, 5.0, 115.0, 48.0)  # lon_min, lat_min, lon_max, lat_max
# the eight ICIMOD members and the neighbours that show inside the map
COUNTRIES = {"AFG", "BGD", "BTN", "CHN", "IND", "MMR", "NPL", "PAK",
             "IRN", "TKM", "UZB", "TJK", "KGZ", "KAZ", "MNG", "LAO", "THA", "VNM", "LKA"}
TOLERANCE_DEG = 0.015
MIN_RING_AREA = 0.02  # square degrees; drops specks of islands


def _perp_distance(p, a, b):
    (x, y), (x1, y1), (x2, y2) = p, a, b
    dx, dy = x2 - x1, y2 - y1
    if dx == dy == 0:
        return ((x - x1) ** 2 + (y - y1) ** 2) ** 0.5
    return abs(dy * x - dx * y + x2 * y1 - y2 * x1) / (dx * dx + dy * dy) ** 0.5


def simplify(points, tolerance):
    """Douglas-Peucker, iterative so long coastlines don't hit the recursion limit."""
    keep = [False] * len(points)
    keep[0] = keep[-1] = True
    stack = [(0, len(points) - 1)]
    while stack:
        i, j = stack.pop()
        best, index = 0.0, None
        for k in range(i + 1, j):
            d = _perp_distance(points[k], points[i], points[j])
            if d > best:
                best, index = d, k
        if index is not None and best > tolerance:
            keep[index] = True
            stack += [(i, index), (index, j)]
    return [p for p, kept in zip(points, keep, strict=True) if kept]


def ring_area(ring):
    return abs(sum(x1 * y2 - x2 * y1 for (x1, y1), (x2, y2) in zip(ring, ring[1:], strict=False))) / 2


def in_bbox(poly):
    xs = [x for x, _ in poly[0]]
    ys = [y for _, y in poly[0]]
    return min(xs) < BBOX[2] and max(xs) > BBOX[0] and min(ys) < BBOX[3] and max(ys) > BBOX[1]


def main(source: str) -> None:
    data = json.loads(Path(source).read_text(encoding="utf-8"))
    features = []
    for feature in data["features"]:
        props, geometry = feature["properties"], feature["geometry"]
        if props["ADM0_A3"] not in COUNTRIES:
            continue
        polys = geometry["coordinates"] if geometry["type"] == "MultiPolygon" else [geometry["coordinates"]]
        out_polys = []
        for poly in filter(in_bbox, polys):
            rings = []
            for ring in poly:
                if ring_area(ring) < MIN_RING_AREA:
                    continue
                simplified = [[round(x, 3), round(y, 3)] for x, y in simplify(ring, TOLERANCE_DEG)]
                if len(simplified) >= 4:
                    rings.append(simplified)
            if rings:
                out_polys.append(rings)
        if out_polys:
            features.append({
                "type": "Feature",
                "id": props["ISO_N3"],
                "properties": {"name": props["NAME"], "a3": props["ADM0_A3"]},
                "geometry": {"type": "MultiPolygon", "coordinates": out_polys},
            })
    OUT.write_text(json.dumps({"type": "FeatureCollection", "features": features}, separators=(",", ":")), encoding="utf-8")
    print(f"{len(features)} countries -> {OUT} ({OUT.stat().st_size / 1024:.0f} KB)")


if __name__ == "__main__":
    main(sys.argv[1])
