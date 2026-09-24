"""Render a computed chart as a North-Indian-style diamond kundali (SVG).

Kept dependency-free (raw SVG string building) so visualization doesn't
force a heavyweight plotting library onto the core package.
"""

from html import escape

from starcharts.chart import GrahaPlacement
from starcharts.constants import RASHIS

_SIZE = 480
_GRAHA_ABBR = {
    "Surya": "Su",
    "Chandra": "Mo",
    "Mangala": "Ma",
    "Budha": "Me",
    "Guru": "Ju",
    "Shukra": "Ve",
    "Shani": "Sa",
}

# Label anchor points for the 12 houses of a standard North-Indian diamond
# chart, as fractions of the overall size. House 1 is the top diamond;
# houses 2-12 proceed anticlockwise (top -> left -> bottom -> right), the
# standard North-Indian layout.
_ANCHOR_FRACTIONS = [
    (0.50, 0.22),  # 1: top diamond
    (0.22, 0.14),  # 2
    (0.14, 0.22),  # 3
    (0.22, 0.50),  # 4: left diamond
    (0.14, 0.78),  # 5
    (0.22, 0.86),  # 6
    (0.50, 0.78),  # 7: bottom diamond
    (0.78, 0.86),  # 8
    (0.86, 0.78),  # 9
    (0.78, 0.50),  # 10: right diamond
    (0.86, 0.22),  # 11
    (0.78, 0.14),  # 12
]


def render_kundali_svg(
    chart: dict[str, GrahaPlacement],
    ascendant_rashi_index: int = 0,
    title: str | None = None,
) -> str:
    """Render a North-Indian diamond kundali as an SVG string.

    ascendant_rashi_index fixes which rashi (0=Mesha..11=Meena) sits in
    house 1 (the top diamond); houses 2-12 follow clockwise from there.
    """
    size = _SIZE
    c = size / 2
    top, right, bottom, left = (c, 0.0), (size, c), (c, size), (0.0, c)
    tl, tr, br, bl = (0.0, 0.0), (size, 0.0), (size, size), (0.0, size)

    def pts(*points):
        return " ".join(f"{x:.1f},{y:.1f}" for x, y in points)

    outer = pts(tl, tr, br, bl)
    diamond = pts(top, right, bottom, left)

    anchors = [(fx * size, fy * size) for fx, fy in _ANCHOR_FRACTIONS]
    rashi_by_house = [(ascendant_rashi_index + h) % 12 for h in range(12)]

    grahas_by_rashi: dict[int, list[str]] = {i: [] for i in range(12)}
    for placement in chart.values():
        grahas_by_rashi[placement.rashi.index].append(_GRAHA_ABBR[placement.graha])

    svg_parts = [
        f'<svg viewBox="0 0 {size} {size}" xmlns="http://www.w3.org/2000/svg" '
        f'font-family="sans-serif">',
        '<rect x="0" y="0" width="100%" height="100%" fill="var(--kundali-bg, #fff)" />',
        f'<polygon points="{outer}" fill="none" stroke="currentColor" stroke-width="2" />',
        f'<polygon points="{diamond}" fill="none" stroke="currentColor" stroke-width="2" />',
        f'<line x1="{tl[0]}" y1="{tl[1]}" x2="{br[0]}" y2="{br[1]}" '
        f'stroke="currentColor" stroke-width="2" />',
        f'<line x1="{tr[0]}" y1="{tr[1]}" x2="{bl[0]}" y2="{bl[1]}" '
        f'stroke="currentColor" stroke-width="2" />',
    ]

    for house, (ax, ay) in enumerate(anchors):
        rashi_index = rashi_by_house[house]
        rashi_name = RASHIS[rashi_index]
        occupants = grahas_by_rashi.get(rashi_index, [])
        svg_parts.append(
            f'<text x="{ax:.1f}" y="{ay - 10:.1f}" font-size="11" '
            f'text-anchor="middle" fill="currentColor" opacity="0.6">{rashi_name}</text>'
        )
        if occupants:
            svg_parts.append(
                f'<text x="{ax:.1f}" y="{ay + 10:.1f}" font-size="14" '
                f'text-anchor="middle" fill="currentColor" font-weight="bold">'
                f'{" ".join(occupants)}</text>'
            )

    if title:
        svg_parts.append(
            f'<text x="{c:.1f}" y="{size - 6}" font-size="12" '
            f'text-anchor="middle" fill="currentColor" opacity="0.7">{escape(title)}</text>'
        )

    svg_parts.append("</svg>")
    return "\n".join(svg_parts)
