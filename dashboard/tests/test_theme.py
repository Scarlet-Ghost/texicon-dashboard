"""Tests for components.theme — token contract + CSS string generation."""
import pytest
from dashboard.components import theme


def test_get_theme_light_returns_required_keys():
    t = theme.get_theme("light")
    for key in ("bg_page", "bg_surface", "border", "text_primary",
                "text_muted", "brand_gold", "brand_green", "danger",
                "tab_active_bg", "tab_active_fg"):
        assert key in t, f"missing token: {key}"


def test_get_theme_dark_returns_required_keys():
    t = theme.get_theme("dark")
    for key in ("bg_page", "bg_surface", "border", "text_primary",
                "text_muted", "brand_gold", "brand_green", "danger",
                "tab_active_bg", "tab_active_fg"):
        assert key in t, f"missing token: {key}"


def test_brand_colors_constant_across_modes():
    light = theme.get_theme("light")
    dark = theme.get_theme("dark")
    assert light["brand_gold"] == "#FFC907"
    assert dark["brand_gold"] == "#FFC907"
    assert light["brand_green"] == "#2d8a3e"
    assert dark["brand_green"] == "#2d8a3e"


def test_get_theme_invalid_mode_raises():
    with pytest.raises(ValueError):
        theme.get_theme("solarized")


@pytest.mark.parametrize("mode", ["light", "dark"])
def test_inject_css_contains_brand_hexes(mode):
    css = theme.inject_css(mode)
    assert "#FFC907" in css
    assert "#2d8a3e" in css


@pytest.mark.parametrize("mode", ["light", "dark"])
def test_inject_css_includes_reduced_motion_guard(mode):
    css = theme.inject_css(mode)
    assert "prefers-reduced-motion: reduce" in css


@pytest.mark.parametrize("mode", ["light", "dark"])
def test_inject_css_returns_str_starting_with_style_tag(mode):
    css = theme.inject_css(mode)
    assert css.startswith("<style>")
    assert css.endswith("</style>")
