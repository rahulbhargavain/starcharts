from datetime import datetime, timezone

from starcharts.chart import compute_chart
from starcharts.visualize import render_kundali_svg


def test_render_kundali_svg_places_all_seven_grahas():
    chart = compute_chart(datetime(2024, 1, 1, tzinfo=timezone.utc))
    svg = render_kundali_svg(chart, title="test chart")
    assert svg.startswith("<svg")
    assert svg.strip().endswith("</svg>")
    for abbr in ("Su", "Mo", "Ma", "Me", "Ju", "Ve", "Sa"):
        assert abbr in svg


def test_render_kundali_svg_respects_ascendant_rotation():
    chart = compute_chart(datetime(2024, 1, 1, tzinfo=timezone.utc))
    svg_mesha_rising = render_kundali_svg(chart, ascendant_rashi_index=0)
    svg_simha_rising = render_kundali_svg(chart, ascendant_rashi_index=4)
    assert svg_mesha_rising != svg_simha_rising
