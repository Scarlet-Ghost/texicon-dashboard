import streamlit as st
import pandas as pd
import numpy as np
import os
from datetime import datetime

css_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "style.css")
with open(css_path) as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

from data.loader import load_sales_report, load_sales_order, load_delivery_report
from data.transformer import transform_sales_report, transform_sales_order, transform_delivery_report
from components.filters import render_top_filters, apply_filters_sr, apply_filters_so, apply_filters_dr
from components.drawers import (
    section_header, insight_card, kpi_card, styled_table, top_bar, risk_card,
    section_card_header,
)
from components.charts import (
    bar_chart, horizontal_bar, donut_chart, line_bar_combo,
    stacked_bar, histogram_chart, box_chart, funnel_chart,
)
from components.formatting import format_php, format_pct, format_number, format_days

st.markdown('<style>section[data-testid="stSidebar"]{display:none !important;}</style>', unsafe_allow_html=True)

sr_raw = load_sales_report()
so_raw = load_sales_order()
dr_raw = load_delivery_report()
sr = transform_sales_report(sr_raw)
so = transform_sales_order(so_raw)
dr = transform_delivery_report(dr_raw)

filters = render_top_filters(sr, so, dr, page_key="ops")
sr_f = apply_filters_sr(sr, filters)
so_f = apply_filters_so(so, filters)
dr_f = apply_filters_dr(dr, filters)

data_end = dr_f["Delivery Date"].max().strftime("%B %d, %Y") if ("Delivery Date" in dr_f.columns and not dr_f.empty and pd.notna(dr_f["Delivery Date"].max())) else "N/A"
top_bar(data_end, datetime.now().strftime("%a, %b %d, %Y  %I:%M:%S %p"))

st.markdown('<div class="page-title">Operations & Delivery</div>', unsafe_allow_html=True)
st.markdown('<div class="page-subtitle">Fulfillment, Warehouse Performance & Service Levels</div>', unsafe_allow_html=True)

if so_f.empty and dr_f.empty:
    st.warning("No data matches the current filters.")
    st.stop()

# --- Metrics ---
total_bookings = so_f["Booking Amount"].sum()
total_delivered = dr_f["Delivered Amount"].sum()
total_net = sr_f["NET SALES"].sum()
total_deliveries = dr_f["Delivery No"].nunique() if "Delivery No" in dr_f.columns else len(dr_f)
total_orders = so_f["SO#"].nunique() if "SO#" in so_f.columns else len(so_f)

fulfillment = (total_delivered / total_bookings * 100) if total_bookings > 0 else 0
gap = total_bookings - total_net
gap_pct = (gap / total_bookings * 100) if total_bookings > 0 else 0

_cycle_vals = so_f["CYCLE_DAYS"].dropna() if "CYCLE_DAYS" in so_f.columns else pd.Series(dtype=float)
avg_cycle = _cycle_vals.mean() if not _cycle_vals.empty else 0
med_cycle = _cycle_vals.median() if not _cycle_vals.empty else 0

if "CYCLE_DAYS" in so_f.columns:
    valid = so_f[so_f["CYCLE_DAYS"].notna()]
    on_time = (len(valid[valid["CYCLE_DAYS"] <= 7]) / len(valid) * 100) if len(valid) > 0 else 0
    w3d = (len(valid[valid["CYCLE_DAYS"] <= 3]) / len(valid) * 100) if len(valid) > 0 else 0
else:
    on_time, w3d = 0, 0

# --- KPI Row ---
kpi_cols = st.columns(5)
with kpi_cols[0]:
    kpi_card("FULFILLMENT RATE", format_pct(fulfillment),
             value_class="" if fulfillment >= 90 else "warning" if fulfillment >= 80 else "danger",
             sub_text=f"{format_php(total_delivered)} / {format_php(total_bookings)}",
             icon="\u2705")
with kpi_cols[1]:
    kpi_card("ON-TIME DELIVERY", format_pct(on_time),
             value_class="" if on_time >= 80 else "danger",
             sub_text=f"Within 7d \u2022 {w3d:.0f}% within 3d",
             icon="\u23F0", icon_class="danger" if on_time < 80 else "")
with kpi_cols[2]:
    kpi_card("AVG LEAD TIME", f"{avg_cycle:.1f} days", value_class="neutral",
             sub_text=f"Median: {med_cycle:.0f} days", icon="\u23F1", icon_class="neutral")
with kpi_cols[3]:
    kpi_card("TOTAL DELIVERIES", format_number(total_deliveries), value_class="neutral",
             icon="\U0001F69A", icon_class="neutral")
with kpi_cols[4]:
    kpi_card("BOOKING GAP", f"{gap_pct:.1f}%",
             value_class="danger" if gap_pct > 15 else "warning" if gap_pct > 10 else "",
             sub_text=format_php(gap),
             icon="\u26A0", icon_class="danger" if gap_pct > 15 else "warning" if gap_pct > 10 else "")

# === FULFILLMENT FUNNEL ===
st.markdown('<div class="section-gap"></div>', unsafe_allow_html=True)
with st.container(border=True):
    section_card_header("Fulfillment Funnel", "Order-to-invoice conversion")
    stages = ["Booked", "Delivered", "Invoiced"]
    values = [total_bookings, total_delivered, total_net]
    fig = funnel_chart(stages, values, height=260)
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

# === DELIVERY TRENDS ===
st.markdown('<div class="section-gap"></div>', unsafe_allow_html=True)
col1, col2 = st.columns([2, 1])

with col1:
    with st.container(border=True):
        section_card_header("Monthly Delivery Trend", "Volume and value over time")
        if "DEL_MONTH" in dr_f.columns:
            dm = dr_f.groupby("DEL_MONTH").agg(
                Count=("Delivered Amount", "count"), Value=("Delivered Amount", "sum"),
            ).sort_index().reset_index()
            dm["Month"] = dm["DEL_MONTH"].dt.strftime("%b %y")
            fig = line_bar_combo(dm, "Month", "Value", "Count", "Value", "Count", height=280)
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

with col2:
    with st.container(border=True):
        section_card_header("Warehouse Split", "Revenue by warehouse")
        if "Warehouse" in dr_f.columns:
            wh = dr_f.groupby("Warehouse")["Delivered Amount"].sum().sort_values(ascending=False)
            fig = donut_chart(wh.index.tolist(), wh.values.tolist(), height=280,
                              center_text=f"{len(wh)}\nWH")
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

# === CYCLE TIME ===
st.markdown('<div class="section-gap"></div>', unsafe_allow_html=True)

col1, col2 = st.columns(2)
with col1:
    with st.container(border=True):
        section_card_header("Cycle Time Distribution", "Days from order to delivery")
        if "CYCLE_DAYS" in so_f.columns:
            cd = so_f[so_f["CYCLE_DAYS"].notna() & (so_f["CYCLE_DAYS"] <= 90)]
            if not cd.empty:
                fig = histogram_chart(cd, "CYCLE_DAYS", nbins=30, height=280)
                st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

with col2:
    with st.container(border=True):
        section_card_header("Cycle Time by Warehouse", "Delivery speed comparison")
        if "CYCLE_DAYS" in so_f.columns and "Warehouse" in so_f.columns:
            cd = so_f[so_f["CYCLE_DAYS"].notna() & (so_f["CYCLE_DAYS"] <= 90)]
            if not cd.empty:
                fig = box_chart(cd, "Warehouse", "CYCLE_DAYS", height=280)
                st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

# === WAREHOUSE THROUGHPUT ===
st.markdown('<div class="section-gap"></div>', unsafe_allow_html=True)
with st.expander("Warehouse Throughput Over Time", expanded=True):
    if "Warehouse" in dr_f.columns and "DEL_MONTH" in dr_f.columns:
        wm = dr_f.groupby(["DEL_MONTH", "Warehouse"])["Delivered Amount"].sum().reset_index()
        wm["Month"] = wm["DEL_MONTH"].dt.strftime("%b %y")
        fig = stacked_bar(wm, "Month", "Delivered Amount", "Warehouse", height=300)
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

# === TOP CUSTOMERS ===
st.markdown('<div class="section-gap"></div>', unsafe_allow_html=True)
col1, col2 = st.columns(2)

with col1:
    with st.container(border=True):
        section_card_header("Top Customers by Delivery", "Highest delivery volume")
        if "Customer" in dr_f.columns:
            top_c = dr_f.groupby("Customer")["Delivered Amount"].sum().nlargest(10).sort_values(ascending=True).reset_index()
            fig = horizontal_bar(top_c, "Delivered Amount", "Customer", height=300)
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

with col2:
    with st.container(border=True):
        section_card_header("Deliveries by Day of Week", "Operational scheduling patterns")
        if "DEL_DOW" in dr_f.columns:
            dow_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
            dd = dr_f.groupby("DEL_DOW")["Delivered Amount"].count().reset_index()
            dd.columns = ["Day", "Count"]
            dd["Day"] = pd.Categorical(dd["Day"], categories=dow_order, ordered=True)
            dd = dd.sort_values("Day").dropna(subset=["Day"])
            fig = bar_chart(dd, "Day", "Count", height=300)
            fig.update_traces(hovertemplate="%{x}: %{y:,} deliveries<extra></extra>")
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

# === CHANNEL & BACKLOG ===
st.markdown('<div class="section-gap"></div>', unsafe_allow_html=True)
with st.expander("Channel Mix & Backlog", expanded=False):
    col1, col2 = st.columns(2)
    with col1:
        if "Group Name" in so_f.columns:
            ch = so_f.groupby("Group Name")["Booking Amount"].sum().sort_values(ascending=True).reset_index()
            fig = horizontal_bar(ch, "Booking Amount", "Group Name", height=250)
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    with col2:
        if "Delivery Date" in so_f.columns and "SO Date" in so_f.columns:
            ref = so_f["SO Date"].max()
            if pd.notna(ref):
                future = so_f[so_f["Delivery Date"] > ref].copy()
                if not future.empty:
                    future["Days Out"] = (future["Delivery Date"] - ref).dt.days
                    bins = [0, 30, 60, 90, 9999]
                    labels = ["0-30d", "31-60d", "61-90d", "90+d"]
                    future["Horizon"] = pd.cut(future["Days Out"], bins=bins, labels=labels, right=True)
                    bl = future.groupby("Horizon", observed=True)["Booking Amount"].sum().reset_index()
                    bl.columns = ["Horizon", "Value"]
                    fig = bar_chart(bl, "Horizon", "Value", height=250)
                    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
                else:
                    st.info("No future delivery backlog.")
