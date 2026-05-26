import json

from vision_ops import (
    check_wcag_contrast,
    extract_color_analytics,
    get_color_name_hsv,
    psychology_for_color,
    rgb_to_hex,
)


def test_get_color_name_hsv_red():
    assert get_color_name_hsv(220, 30, 30) in ("Red", "Dark Red", "Pink")


def test_get_color_name_hsv_neutral_white():
    assert get_color_name_hsv(250, 250, 250) == "White"


def test_rgb_to_hex():
    assert rgb_to_hex(255, 128, 0) == "#FF8000"


def test_psychology_mapping():
    assert psychology_for_color("Blue") == "trust"
    assert psychology_for_color("Orange") == "energy"


def test_extract_color_analytics_structure(sample_image):
    colors = extract_color_analytics(sample_image, num_colors=3)
    assert isinstance(colors, list)
    if colors:
        c = colors[0]
        assert "hex" in c and c["hex"].startswith("#")
        assert "name" in c
        assert "coverage_pct" in c
        assert "psychology" in c
        assert c["coverage_pct"] >= 0


def test_check_wcag_no_text_regions(sample_image, monkeypatch):
    monkeypatch.setattr("vision_ops.extract_text_with_boxes", lambda _path: [])
    wcag = check_wcag_contrast(sample_image)
    assert wcag["wcag_aa_pass"] is True
    assert wcag["regions_checked"] == 0


def test_color_analytics_json_serializable(sample_image):
    colors = extract_color_analytics(sample_image)
    json.dumps(colors)
