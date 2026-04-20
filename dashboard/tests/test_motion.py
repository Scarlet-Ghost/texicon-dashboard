"""Tests for components.motion — pure HTML/JS string generators."""
from dashboard.components import motion


def test_loading_overlay_html_contains_brand_and_bar():
    html = motion.loading_overlay_html()
    assert "tx-loading-overlay" in html
    assert "TEXICON" in html
    assert "tx-loading-bar" in html


def test_skeleton_block_default_size():
    html = motion.skeleton_block()
    assert "tx-skeleton" in html
    assert "height" in html


def test_skeleton_block_custom_size():
    html = motion.skeleton_block(width="120px", height="20px")
    assert "120px" in html
    assert "20px" in html


def test_count_up_script_includes_target_value():
    html = motion.count_up_value(label="Revenue", value="₱4.82M",
                                 numeric_target=4_820_000, prefix="₱", suffix="")
    assert "Revenue" in html
    assert 'data-tx-count-target="4820000"' in html
    assert 'data-tx-count-prefix="₱"' in html


def test_count_up_emits_script_once_helper():
    snippet = motion.count_up_runtime_script()
    assert "<script>" in snippet
    assert "data-tx-count-target" in snippet
    assert "prefers-reduced-motion" in snippet
