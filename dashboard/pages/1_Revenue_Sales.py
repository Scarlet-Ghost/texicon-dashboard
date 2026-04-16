import streamlit as st
import pandas as pd
import numpy as np
import os

css_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "style.css")
with open(css_path) as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
st.markdown('<style>section[data-testid="stSidebar"]{display:none !important;}</style>', unsafe_allow_html=True)

from data.loader import load_sales_report, load_sales_order
from data.transformer import transform_sales_report, transform_sales_order
from components.filters import render_top_filters, apply_filters_sr
from components.kpi_cards import render_kpi_row
from components.drawers import (
    section_header, insight_card, kpi_card, styled_table,
    concentration_bar, mini_card, top_bar, section_card_header,
)
from components.charts import (
    bar_chart, horizontal_bar, donut_chart, line_bar_combo,
    stacked_bar, treemap_chart, area_chart,
)
from components.formatting import format_php, format_pct, format_number
from data.constants import AREA_COLORS, PRODUCT_COLORS
from datetime import datetime

sr_raw = load_sales_report()
so_raw = load_sales_order()
sr = transform_sales_report(sr_raw)
so = transform_sales_order(so_raw)

filters = render_top_filters(sr, so, page_key="revenue")
sr_f = apply_filters_sr(sr, filters)

data_end = sr_f["DATE"].max().strftime("%B %d, %Y") if ("DATE" in sr_f.columns and not sr_f.empty and pd.notna(sr_f["DATE"].max())) else "N/A"
top_bar(data_end, datetime.now().strftime("%a, %b %d, %Y  %I:%M:%S %p"))

st.markdown('<div class="page-title">Revenue & Sales</div>', unsafe_allow_html=True)
st.markdown('<div class="page-subtitle">Sales Performance, Product Mix, Customer & Geographic Analysis</div>', unsafe_allow_html=True)

if sr_f.empty:
    st.warning("No data matches the current filters.")
    st.stop()

# --- Metrics ---
total_net = sr_f["NET SALES"].sum()
total_gross = sr_f["GROSS SALES"].sum()
discount_pct = ((total_gross - total_net) / total_gross * 100) if total_gross > 0 else 0
active_clients = sr_f["CLIENT"].nunique() if "CLIENT" in sr_f.columns else 0
unique_inv = sr_f["INV NO."].nunique() if "INV NO." in sr_f.columns else max(len(sr_f), 1)
avg_tx = total_net / unique_inv if unique_inv > 0 else 0

# --- KPI Row ---
kpi_cols = st.columns(5)
with kpi_cols[0]:
    kpi_card("NET SALES", format_php(total_net), icon="\U0001F4B0")
with kpi_cols[1]:
    kpi_card("GROSS SALES", format_php(total_gross), icon="\u20B1")
with kpi_cols[2]:
    kpi_card("DISCOUNT RATE", format_pct(discount_pct),
             value_class="warning" if discount_pct > 10 else "",
             icon="\u2199", icon_class="warning" if discount_pct > 10 else "")
with kpi_cols[3]:
    kpi_card("ACTIVE CLIENTS", format_number(active_clients), icon="\U0001F465")
with kpi_cols[4]:
    kpi_card("AVG TRANSACTION", format_php(avg_tx), icon="\U0001F4B5")

# === REVENUE TRENDS ===
st.markdown('<div class="section-gap"></div>', unsafe_allow_html=True)

if "YEAR_MONTH" in sr_f.columns:
    monthly = sr_f.groupby("YEAR_MONTH").agg(
        Net=("NET SALES", "sum"), Gross=("GROSS SALES", "sum"),
    ).sort_index().reset_index()
    monthly["Month"] = monthly["YEAR_MONTH"].dt.strftime("%b %y")

    col1, col2 = st.columns([2, 1])
    with col1:
        with st.container(border=True):
            section_card_header("Revenue Trends", "Net vs Gross monthly performance")
            fig = line_bar_combo(monthly, "Month", "Net", "Gross", "Net Sales", "Gross Sales")
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
    with col2:
        with st.container(border=True):
            section_card_header("Area Group Split", "Revenue by geographic region")
            if "AREA GROUP" in sr_f.columns:
                area_data = sr_f.groupby("AREA GROUP")["NET SALES"].sum().sort_values(ascending=False)
                fig = donut_chart(
                    area_data.index.tolist(), area_data.values.tolist(),
                    colors=[AREA_COLORS.get(a, "#78909C") for a in area_data.index],
                )
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
        "warning" if top5_pct > 40 else "info",
    )

col1, col2 = st.columns(2)
with col1:
    with st.container(border=True):
        section_card_header("Product Categories", "Revenue by category")
        if "PRODUCT CATEGORY" in sr_f.columns:
            cat = sr_f.groupby("PRODUCT CATEGORY")["NET SALES"].sum().sort_values(ascending=True).reset_index()
            fig = horizontal_bar(cat, "NET SALES", "PRODUCT CATEGORY", height=280)
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

with col2:
    with st.container(border=True):
        section_card_header("Top 10 Products", "Highest revenue items")
        if "ITEM" in sr_f.columns:
            top10 = sr_f.groupby("ITEM")["NET SALES"].sum().nlargest(10).sort_values(ascending=True).reset_index()
            fig = horizontal_bar(top10, "NET SALES", "ITEM", height=280)
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

# === TOP CUSTOMERS TABLE ===
st.markdown('<div class="section-gap"></div>', unsafe_allow_html=True)
with st.container(border=True):
    section_card_header("Top 10 Customers", "Ranked by net revenue")
    if "CLIENT" in sr_f.columns:
        top10_c = sr_f.groupby("CLIENT").agg(
            Revenue=("NET SALES", "sum"),
            Qty=("QTY IN L/KG", "sum") if "QTY IN L/KG" in sr_f.columns else ("NET SALES", "count"),
            Orders=("INV NO.", "nunique") if "INV NO." in sr_f.columns else ("NET SALES", "count"),
        ).nlargest(10, "Revenue")

        rows = []
        for i, (name, r) in enumerate(top10_c.iterrows()):
            share = (r["Revenue"] / total_net * 100) if total_net > 0 else 0
            rows.append([
                str(i + 1), name[:28], f"{r['Qty']:,.0f}", f"PHP {r['Revenue']:,.0f}",
                f"{r['Orders']:,.0f}", f"{share:.1f}%",
            ])
        styled_table(["#", "Customer", "Qty (L/KG)", "Revenue", "Orders", "Share"], rows, green_cols=[3])

# === SALES REPS ===
st.markdown('<div class="section-gap"></div>', unsafe_allow_html=True)
col1, col2 = st.columns(2)

with col1:
    with st.container(border=True):
        section_card_header("Sales Representatives", "Revenue by sales rep")
        if "SR" in sr_f.columns:
            top10_r = sr_f.groupby("SR")["NET SALES"].sum().nlargest(10).sort_values(ascending=True).reset_index()
            fig = horizontal_bar(top10_r, "NET SALES", "SR", height=300)
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

with col2:
    with st.container(border=True):
        section_card_header("Geographic Performance", "Revenue by area and cluster")
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
        section_card_header("Payment Terms", "Revenue split by terms")
        if "TERMS" in sr_f.columns:
            terms = sr_f.groupby("TERMS")["NET SALES"].sum().sort_values(ascending=False)
            fig = donut_chart(terms.index.tolist(), terms.values.tolist())
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

with col2:
    with st.container(border=True):
        section_card_header("Terms by Area", "Payment terms across regions")
        if "TERMS" in sr_f.columns and "AREA GROUP" in sr_f.columns:
            ta = sr_f.groupby(["AREA GROUP", "TERMS"])["NET SALES"].sum().reset_index()
            fig = stacked_bar(ta, "AREA GROUP", "NET SALES", "TERMS", height=300)
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
