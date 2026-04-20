import streamlit as st
import pandas as pd
import numpy as np
import os

css_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "style.css")
with open(css_path) as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
st.markdown('<style>section[data-testid="stSidebar"]{display:none !important;}</style>', unsafe_allow_html=True)

from components.auth import require_role, user_chip, current_role

require_role(allowed=["owner"])

from data.loader import load_sales_report, load_sales_order, load_delivery_report, get_data_freshness
from data.transformer import transform_sales_report, transform_sales_order, transform_delivery_report
from data.tooltips import REVENUE as TT
from data.risk_engine import compute_global_risks
from components.filters import render_top_filters, apply_filters_sr
from components.kpi_cards import render_kpi_row, kpi_spec_money, kpi_spec_pct, kpi_spec_count
from data.analytics import build_kpi_trends
from components.drawers import (
    section_header, insight_card, kpi_card, styled_table,
    concentration_bar, mini_card, top_bar, section_card_header, render_nav,
    empty_state, scroll_to_top_button, render_breadcrumb, global_alert_strip,
    hero_kpi, section_divider)
from data.constants import KPI_TARGETS
from components.charts import (
    bar_chart, horizontal_bar, donut_chart, line_bar_combo,
    stacked_bar, treemap_chart, area_chart, add_target_line)
from components.formatting import format_php, format_pct, format_number
from data.constants import AREA_COLORS, PRODUCT_COLORS
from datetime import datetime

sr_raw = load_sales_report()
so_raw = load_sales_order()
dr_raw = load_delivery_report()
sr = transform_sales_report(sr_raw)
so = transform_sales_order(so_raw)
dr = transform_delivery_report(dr_raw)

_risks = compute_global_risks(sr, so, dr)
render_nav(active_page="1_Revenue_Sales", risk_count=len(_risks), role=current_role())
render_breadcrumb([("Executive", "app"), ("Revenue & Sales", None)])
if _risks:
    global_alert_strip(_risks)
filters = render_top_filters(sr, so, page_key="revenue", expand_filters=True)
sr_f = apply_filters_sr(sr, filters)

data_end = sr_f["DATE"].max().strftime("%B %d, %Y") if ("DATE" in sr_f.columns and not sr_f.empty and pd.notna(sr_f["DATE"].max())) else "N/A"
top_bar(data_end, datetime.now().strftime("%a, %b %d, %Y  %I:%M:%S %p"), freshness_hours=get_data_freshness())
user_chip()

st.markdown('<div class="page-title">Revenue & Sales</div>', unsafe_allow_html=True)
st.markdown('<div class="page-subtitle">Sales Performance, Product Mix, Customer & Geographic Analysis</div>', unsafe_allow_html=True)

if sr_f.empty:
    empty_state()
    st.stop()

# --- Metrics ---
total_net = sr_f["NET SALES"].sum()
total_gross = sr_f["GROSS SALES"].sum()
discount_pct = ((total_gross - total_net) / total_gross * 100) if total_gross > 0 else 0
active_clients = sr_f["CLIENT"].nunique() if "CLIENT" in sr_f.columns else 0
unique_inv = sr_f["INV NO."].nunique() if "INV NO." in sr_f.columns else max(len(sr_f), 1)
avg_tx = total_net / unique_inv if unique_inv > 0 else 0

# --- HERO: NET SALES ---
trends = build_kpi_trends(sr_f, so)

# MoM delta from the trend series if available
_net_trend = trends.get("net_sales") or []
_mom_label = None
if _net_trend and len(_net_trend) >= 2 and _net_trend[-2] > 0:
    _mom = (_net_trend[-1] - _net_trend[-2]) / _net_trend[-2] * 100
    _mom_label = f"{_mom:+.1f}% MoM"

hero_kpi(
    label="NET SALES",
    value=format_php(total_net),
    sub_value=f"{unique_inv:,} invoices · {active_clients:,} clients",
    trend=_net_trend,
    delta=(_mom if _mom_label else None),
    delta_label=_mom_label,
    tooltip=TT["net_sales"],
)

# --- SUPPORTING KPI ROW (4 cards — net sales lives in the hero) ---
render_kpi_row([
    kpi_spec_money("GROSS SALES", total_gross, tooltip=TT["gross_sales"],
                   trend_data=trends.get("gross_sales")),
    kpi_spec_pct("DISCOUNT RATE", discount_pct, thresholds=(10, 15),
                 lower_is_better=True,
                 tooltip=TT["discount_rate"], trend_data=trends.get("discount_pct"),
                 card_class="warning-glow" if discount_pct > 10 else ""),
    kpi_spec_count("ACTIVE CLIENTS", active_clients, tooltip=TT["active_clients"],
                   trend_data=trends.get("active_clients")),
    kpi_spec_money("AVG TXN", avg_tx, tooltip=TT["avg_transaction"],
                   trend_data=trends.get("avg_transaction")),
])

# === REVENUE TRENDS ===
st.markdown('<div class="section-gap"></div>', unsafe_allow_html=True)

if "YEAR_MONTH" in sr_f.columns:
    monthly = sr_f.groupby("YEAR_MONTH").agg(
        Net=("NET SALES", "sum"), Gross=("GROSS SALES", "sum")).sort_index().reset_index()
    monthly["Month"] = monthly["YEAR_MONTH"].dt.strftime("%b %y")

    col1, col2 = st.columns([2, 1])
    with col1:
        with st.container(border=True):
            section_card_header("Revenue Trends", "Net vs Gross monthly performance", tooltip=TT["revenue_trend"])
            fig = line_bar_combo(monthly, "Month", "Net", "Gross", "Net Sales", "Gross Sales",
                                 y_title="Revenue (PHP)")
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
    with col2:
        with st.container(border=True):
            section_card_header("Area Group Split", "Revenue by geographic region", tooltip=TT["area_split"])
            if "AREA GROUP" in sr_f.columns:
                area_data = sr_f.groupby("AREA GROUP")["NET SALES"].sum().sort_values(ascending=False)
                fig = donut_chart(
                    area_data.index.tolist(), area_data.values.tolist(),
                    colors=[AREA_COLORS.get(a, "#5A6069") for a in area_data.index])
                st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

# === CONCENTRATION RISK ===
st.markdown('<div class="section-gap"></div>', unsafe_allow_html=True)

if "ITEM" in sr_f.columns:
    top5 = sr_f.groupby("ITEM")["NET SALES"].sum().nlargest(5)
    top5_pct = (top5.sum() / total_net * 100) if total_net > 0 else 0
    glyph = sr_f[sr_f["ITEM"].str.contains("GLYPHOTEX", case=False, na=False)]["NET SALES"].sum()
    glyph_pct = (glyph / total_net * 100) if total_net > 0 else 0
    insight_card(
        f"Top 5 products = <strong>{top5_pct:.1f}%</strong> of revenue. "
        f"GLYPHOTEX 480 SL alone = <strong>{glyph_pct:.1f}%</strong> ({format_php(glyph)})",
        "warning" if top5_pct > 40 else "info")

col1, col2 = st.columns([1, 2])
with col1:
    with st.container(border=True):
        section_card_header("Product Categories", "Revenue by category", tooltip=TT["product_categories"])
        if "PRODUCT CATEGORY" in sr_f.columns:
            cat = sr_f.groupby("PRODUCT CATEGORY")["NET SALES"].sum().sort_values(ascending=False).reset_index()
            fig = bar_chart(cat, "PRODUCT CATEGORY", "NET SALES",
                            x_title="Category", y_title="Revenue (PHP)", height=320)
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

with col2:
    with st.container(border=True):
        section_card_header("Top 10 Products", "Highest revenue items", tooltip=TT["top_products"])
        if "ITEM" in sr_f.columns:
            top10 = sr_f.groupby("ITEM")["NET SALES"].sum().nlargest(10).sort_values(ascending=True).reset_index()
            fig = horizontal_bar(top10, "NET SALES", "ITEM", x_title="Revenue (PHP)", height=320)
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

# === TOP CUSTOMERS TABLE ===
st.markdown('<div class="section-gap"></div>', unsafe_allow_html=True)
with st.container(border=True):
    section_card_header("Top 10 Customers", "Ranked by net revenue", tooltip=TT["top_customers"])
    if "CLIENT" in sr_f.columns:
        top10_c = sr_f.groupby("CLIENT").agg(
            Revenue=("NET SALES", "sum"),
            Qty=("QTY IN L/KG", "sum") if "QTY IN L/KG" in sr_f.columns else ("NET SALES", "count"),
            Orders=("INV NO.", "nunique") if "INV NO." in sr_f.columns else ("NET SALES", "count")).nlargest(10, "Revenue")

        rows = []
        for i, (name, r) in enumerate(top10_c.iterrows()):
            share = (r["Revenue"] / total_net * 100) if total_net > 0 else 0
            rows.append([
                str(i + 1), name[:30], f"{r['Qty']:,.0f}", f"\u20B1{r['Revenue']:,.0f}",
                f"{r['Orders']:,.0f}", f"{share:.1f}%",
            ])
        styled_table(["#", "Customer", "Qty (L/KG)", "Revenue", "Orders", "Share"], rows,
                     green_cols=[3], num_cols=[0, 2, 3, 4, 5])

# === SALES REPS ===
st.markdown('<div class="section-gap"></div>', unsafe_allow_html=True)
col1, col2 = st.columns(2)

with col1:
    with st.container(border=True):
        section_card_header("Sales Representatives", "Revenue by sales rep", tooltip=TT["sales_reps"])
        if "SR" in sr_f.columns:
            top10_r = sr_f.groupby("SR")["NET SALES"].sum().nlargest(10).sort_values(ascending=True).reset_index()
            fig = horizontal_bar(top10_r, "NET SALES", "SR", x_title="Revenue (PHP)")
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

with col2:
    with st.container(border=True):
        section_card_header("Geographic Performance", "Revenue by area and cluster", tooltip=TT["geographic"])
        if "AREA GROUP" in sr_f.columns and "CLUSTER" in sr_f.columns:
            tm_data = sr_f.groupby(["AREA GROUP", "CLUSTER"])["NET SALES"].sum().reset_index()
            tm_data = tm_data[tm_data["NET SALES"] > 0]
            if not tm_data.empty:
                fig = treemap_chart(tm_data, path=["AREA GROUP", "CLUSTER"], values="NET SALES", height=300)
                st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

# === PAYMENT TERMS ===
st.markdown('<div class="section-gap"></div>', unsafe_allow_html=True)

col1, col2 = st.columns(2)
with col1:
    with st.container(border=True):
        section_card_header("Payment Terms", "Revenue split by terms", tooltip=TT["payment_dist"])
        if "TERMS" in sr_f.columns:
            terms = sr_f.groupby("TERMS")["NET SALES"].sum().sort_values(ascending=False)
            fig = donut_chart(terms.index.tolist(), terms.values.tolist())
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

with col2:
    with st.container(border=True):
        section_card_header("Terms by Area", "Payment terms across regions", tooltip=TT["terms_by_area"])
        if "TERMS" in sr_f.columns and "AREA GROUP" in sr_f.columns:
            ta = sr_f.groupby(["AREA GROUP", "TERMS"])["NET SALES"].sum().reset_index()
            fig = stacked_bar(ta, "AREA GROUP", "NET SALES", "TERMS", height=300,
                              y_title="Revenue (PHP)", x_title="Area")
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

scroll_to_top_button()
