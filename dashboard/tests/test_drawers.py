"""Tests for components.drawers — pure HTML helpers only."""
from dashboard.components import drawers


def test_top_bar_html_includes_brand_and_role_only():
    html = drawers.top_bar_html(theme="light", role_label="Owner")
    assert "TEXICON" in html
    assert "tx-leaf" in html
    assert "Owner" in html
    # Theme toggle is rendered separately as an st.button by render_top_bar,
    # so the topbar HTML should not emit the raw <a href="?theme="> toggle.
    assert "?theme=" not in html
    assert "tx-toggle" not in html


def test_label_to_page_id_owner():
    # owner labels map to their page_id; session-preserving st.page_link uses these
    assert drawers._label_to_page_id("Revenue", "owner") == "1_Revenue_Sales"
    assert drawers._label_to_page_id("Executive", "owner") == "app"
    assert drawers._label_to_page_id("Data", "owner") == "6_Data_Explorer"


def test_label_to_page_id_sales_subset():
    # sales role gets a 3-page nav; owner-only labels fall through unchanged
    assert drawers._label_to_page_id("Reconnect", "sales") == "4_Customer_Reconnection"
    assert drawers._label_to_page_id("Intel", "sales") == "5_Sales_Intelligence"
    # "Cash" is owner-only; unknown-for-role labels return the label itself
    assert drawers._label_to_page_id("Cash", "sales") == "Cash"


def test_badge_html_variants():
    assert "tx-badge gold" in drawers.badge_html("TOP", variant="gold")
    assert "tx-badge green" in drawers.badge_html("GROWING", variant="green")
    assert "tx-badge muted" in drawers.badge_html("INACTIVE", variant="muted")


def test_breadcrumb_html():
    html = drawers.breadcrumb_html(["Revenue", "Q1 2026"])
    assert "<b>Revenue</b>" in html
    assert "Q1 2026" in html


import streamlit as st  # noqa: F401 (needed because styled_table imports streamlit internally)


def test_styled_table_num_cols_right_aligns_header_and_cells(monkeypatch):
    captured = {}
    def fake_markdown(html, **kwargs):
        captured["html"] = html
    monkeypatch.setattr("streamlit.markdown", fake_markdown)
    drawers.styled_table(
        headers=["Name", "Revenue"],
        rows=[["Globe", "892K"]],
        num_cols=[1],
    )
    h = captured["html"]
    assert "text-align:right" in h
    assert "tabular-nums" in h


def test_styled_table_green_and_red_cols(monkeypatch):
    captured = {}
    def fake_markdown(html, **kwargs):
        captured["html"] = html
    monkeypatch.setattr("streamlit.markdown", fake_markdown)
    drawers.styled_table(
        headers=["A", "B", "C"],
        rows=[["1", "2", "3"]],
        green_cols=[1],
        red_cols=[2],
    )
    h = captured["html"]
    assert "var(--brand-green)" in h
    assert "var(--danger)" in h


def test_styled_table_row_classes(monkeypatch):
    captured = {}
    def fake_markdown(html, **kwargs):
        captured["html"] = html
    monkeypatch.setattr("streamlit.markdown", fake_markdown)
    drawers.styled_table(
        headers=["A"],
        rows=[["one"], ["two"]],
        row_classes=["hilite", ""],
    )
    h = captured["html"]
    assert 'class="hilite"' in h
