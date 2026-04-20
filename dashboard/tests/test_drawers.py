"""Tests for components.drawers — pure HTML helpers only."""
from dashboard.components import drawers


def test_top_bar_html_includes_brand_and_toggle():
    html = drawers.top_bar_html(theme="light", role_label="Owner")
    assert "TEXICON" in html
    assert "tx-leaf" in html
    assert "tx-toggle" in html
    assert "Owner" in html
    assert "?theme=dark" in html  # toggle target


def test_top_bar_html_dark_toggles_to_light():
    html = drawers.top_bar_html(theme="dark", role_label="Sales")
    assert "?theme=light" in html


def test_render_nav_html_marks_active():
    html = drawers.render_nav_html(active="Revenue", role="owner")
    assert 'class="tx-tab on"' in html
    assert "Revenue" in html
    assert "Sales Home" in html


def test_render_nav_html_sales_subset():
    html = drawers.render_nav_html(active="Sales Home", role="sales")
    assert "Sales Home" in html
    assert "Reconnect" in html
    assert "Data" in html
    assert "Cash" not in html  # owner-only page hidden for sales


def test_badge_html_variants():
    assert "tx-badge gold" in drawers.badge_html("TOP", variant="gold")
    assert "tx-badge green" in drawers.badge_html("GROWING", variant="green")
    assert "tx-badge muted" in drawers.badge_html("INACTIVE", variant="muted")


def test_breadcrumb_html():
    html = drawers.breadcrumb_html(["Revenue", "Q1 2026"])
    assert "<b>Revenue</b>" in html
    assert "Q1 2026" in html
