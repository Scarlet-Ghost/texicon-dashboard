import streamlit as st
st.set_page_config(page_title="Operations & Delivery — Texicon", layout="wide",
                   initial_sidebar_state="collapsed")

try:
    from components.theme import inject_css, current_theme
    from components.drawers import render_top_bar
except ModuleNotFoundError:
    from dashboard.components.theme import inject_css, current_theme
    from dashboard.components.drawers import render_top_bar

st.markdown(inject_css(current_theme()), unsafe_allow_html=True)
render_top_bar(active_page="Operations")

import pandas as pd
import numpy as np
import os
from datetime import datetime

from components.auth import require_role, current_role

require_role(allowed=["owner"])

from data.loader import load_sales_report, load_sales_order, load_delivery_report, get_data_freshness
from data.transformer import transform_sales_report, transform_sales_order, transform_delivery_report
from data.tooltips import OPERATIONS as TT
from data.risk_engine import compute_global_risks
from data.constants import KPI_TARGETS, WAREHOUSE_LABELS
from data.analytics import build_kpi_trends
from components.kpi_cards import (
    render_kpi_row, kpi_spec_money, kpi_spec_pct, kpi_spec_days, kpi_spec_count)
from components.filters import render_top_filters, apply_filters_sr, apply_filters_so, apply_filters_dr
from components.drawers import (
    section_header, insight_card, kpi_card, styled_table, top_bar, risk_card,
    section_card_header, render_nav, empty_state, scroll_to_top_button, global_alert_strip,
    render_breadcrumb, hero_kpi, section_divider)
from components.charts import (
    bar_chart, horizontal_bar, donut_chart, line_bar_combo,
    stacked_bar, histogram_chart, funnel_chart)
from components.formatting import format_php, format_pct, format_number, format_days
from components.layout import GRID_WIDE_SIDEBAR

sr_raw = load_sales_report()
so_raw = load_sales_order()
dr_raw = load_delivery_report()
sr = transform_sales_report(sr_raw)
so = transform_sales_order(so_raw)
dr = transform_delivery_report(dr_raw)

_risks = compute_global_risks(sr, so, dr)
render_breadcrumb([("Executive", "app"), ("Operations & Delivery", None)])

if _risks:
    global_alert_strip(_risks)

filters = render_top_filters(sr, so, dr, page_key="ops", expand_filters=False)
sr_f = apply_filters_sr(sr, filters)
so_f = apply_filters_so(so, filters)
dr_f = apply_filters_dr(dr, filters)

data_end = dr_f["Delivery Date"].max().strftime("%B %d, %Y") if ("Delivery Date" in dr_f.columns and not dr_f.empty and pd.notna(dr_f["Delivery Date"].max())) else "N/A"

st.markdown('<div class="page-title">Operations & Delivery</div>', unsafe_allow_html=True)
st.markdown('<div class="page-subtitle">Fulfillment, Warehouse Performance & Service Levels</div>', unsafe_allow_html=True)

if so_f.empty and dr_f.empty:
    empty_state()
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

# === HERO: FULFILLMENT % ===
trends = build_kpi_trends(sr_f, so_f, dr_f)
fulfillment_class = "" if fulfillment >= 90 else "warning" if fulfillment >= 80 else "danger"
hero_kpi(
    label="FULFILLMENT RATE",
    value=format_pct(fulfillment),
    sub_value=f"{format_php(total_delivered)} of {format_php(total_bookings)} delivered",
    trend=trends.get("fulfillment_rate"),
    tooltip=TT["fulfillment_rate"],
    value_class=fulfillment_class,
)

# === SUPPORTING KPIs (4 cards) ===
render_kpi_row([
    kpi_spec_pct("ON-TIME", on_time,
                 value_class="" if on_time >= 80 else "danger",
                 sub_text=f"Within 7d \u2022 {w3d:.0f}% in 3d",
                 tooltip=TT["on_time"], trend_data=trends.get("on_time_pct"),
                 card_class="danger-glow" if on_time < 70 else ""),
    {"label": "LEAD TIME", "value": f"{avg_cycle:.1f} days", "value_class": "neutral",
     "sub_text": f"Median {med_cycle:.0f} days", "tooltip": TT["avg_lead_time"],
     "trend_data": trends.get("avg_lead_time"), "lower_is_better": True},
    kpi_spec_count("DELIVERIES", total_deliveries, tooltip=TT["total_deliveries"],
                   trend_data=trends.get("total_deliveries")),
    kpi_spec_pct("BOOKING GAP", gap_pct,
                 value_class="danger" if gap_pct > 15 else "warning" if gap_pct > 10 else "",
                 sub_text=format_php(gap), tooltip=TT["booking_gap"],
                 card_class="danger-glow" if gap_pct > 15 else ""),
])

# === FUNNEL STRIP (Order → Fulfill → Deliver narrative) ===
st.markdown('<div class="section-gap"></div>', unsafe_allow_html=True)
section_divider("Order → Fulfill → Deliver", eyebrow="STAGE 1 · FULFILLMENT FUNNEL")

# Stage-label strip above the funnel chart
_booked_pct = 100.0
_delivered_pct = (total_delivered / total_bookings * 100) if total_bookings > 0 else 0
_invoiced_pct = (total_net / total_bookings * 100) if total_bookings > 0 else 0
st.markdown(
    f'''<div style="display:grid; grid-template-columns:repeat(3,1fr); gap:8px; margin-bottom:12px;">
        <div class="kpi-card">
            <div class="kpi-label">BOOKED</div>
            <div class="kpi-value">{format_php(total_bookings)}</div>
            <div class="kpi-delta muted">{_booked_pct:.0f}% of bookings</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-label">DELIVERED</div>
            <div class="kpi-value">{format_php(total_delivered)}</div>
            <div class="kpi-delta muted">{_delivered_pct:.1f}% fulfilled</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-label">INVOICED</div>
            <div class="kpi-value">{format_php(total_net)}</div>
            <div class="kpi-delta muted">{_invoiced_pct:.1f}% of bookings</div>
        </div>
    </div>''',
    unsafe_allow_html=True,
)
_funnel_fig = funnel_chart(["Booked", "Delivered", "Invoiced"],
                           [total_bookings, total_delivered, total_net], height=220)
st.plotly_chart(_funnel_fig, use_container_width=True, config={"displayModeBar": False})

# === DELIVERY TRENDS ===
st.markdown('<div class="section-gap"></div>', unsafe_allow_html=True)
section_divider("Delivery Flow Over Time", eyebrow="STAGE 2 · DELIVERY TRENDS")
col1, col2 = st.columns(GRID_WIDE_SIDEBAR)

with col1:
    with st.container(border=True):
        section_card_header("Monthly Delivery Trend", "Volume and value over time", tooltip=TT["delivery_trend"])
        if "DEL_MONTH" in dr_f.columns:
            dm = dr_f.groupby("DEL_MONTH").agg(
                Count=("Delivered Amount", "count"), Value=("Delivered Amount", "sum")).sort_index().reset_index()
            dm["Month"] = dm["DEL_MONTH"].dt.strftime("%b %y")
            fig = line_bar_combo(dm, "Month", "Value", "Count", "Delivered Value", "Deliveries",
                                 height=420, y_title="Delivered Value (PHP)",
                                 line_on_secondary=True, line_currency=False,
                                 line_y_title="Deliveries (count)")
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

with col2:
    with st.container(border=True):
        section_card_header("Warehouse Split", "Share of delivered value", tooltip=TT["warehouse_split"])
        if "Warehouse" in dr_f.columns:
            wh = dr_f.groupby("Warehouse")["Delivered Amount"].sum().sort_values(ascending=False)
            wh_labels = [WAREHOUSE_LABELS.get(k, k) for k in wh.index]
            fig = donut_chart(wh_labels, wh.values.tolist(), height=420,
                              center_text=f"{len(wh)}\nWH")
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

# === CYCLE TIME (single violin/box by warehouse) ===
st.markdown('<div class="section-gap"></div>', unsafe_allow_html=True)
section_divider("Cycle Time by Warehouse", eyebrow="STAGE 3 · SPEED ANALYSIS")

with st.container(border=True):
    section_card_header("Days from Order to Delivery", "Distribution per warehouse; SLA target at 7 days",
                        tooltip=TT["cycle_by_warehouse"])
    if "CYCLE_DAYS" in so_f.columns and "Warehouse" in so_f.columns:
        cd = so_f[so_f["CYCLE_DAYS"].notna() & (so_f["CYCLE_DAYS"] <= 90)].copy()
        if not cd.empty:
            cd["Warehouse"] = cd["Warehouse"].map(lambda w: WAREHOUSE_LABELS.get(w, w))
            agg = cd.groupby("Warehouse").agg(
                median=("CYCLE_DAYS", "median"),
                within_sla=("CYCLE_DAYS", lambda s: (s <= 7).mean() * 100),
                p90=("CYCLE_DAYS", lambda s: s.quantile(0.9)),
                orders=("CYCLE_DAYS", "size"),
            ).reset_index().sort_values("within_sla")

            headers = ["Warehouse", "Median", "% \u2264 7d", "p90", "Orders"]
            rows = [
                [r["Warehouse"],
                 f"{r['median']:.0f}d",
                 f"{r['within_sla']:.0f}%",
                 f"{r['p90']:.0f}d",
                 f"{int(r['orders']):,}"]
                for _, r in agg.iterrows()
            ]
            styled_table(headers, rows, num_cols=[1, 2, 3, 4])
        else:
            st.caption("Not enough cycle data to render distribution.")

# === WAREHOUSE THROUGHPUT (inline section, not expander) ===
st.markdown('<div class="section-gap"></div>', unsafe_allow_html=True)
section_divider("Warehouse Throughput Over Time", eyebrow="STAGE 4 · CAPACITY")

with st.container(border=True):
    section_card_header("Monthly Delivered Value by Warehouse", "Stacked view of warehouse contribution")
    if "Warehouse" in dr_f.columns and "DEL_MONTH" in dr_f.columns:
        wm = dr_f.groupby(["DEL_MONTH", "Warehouse"])["Delivered Amount"].sum().reset_index()
        wm["Warehouse"] = wm["Warehouse"].map(lambda w: WAREHOUSE_LABELS.get(w, w))
        wm["Month"] = wm["DEL_MONTH"].dt.strftime("%b %y")
        fig = stacked_bar(wm, "Month", "Delivered Amount", "Warehouse", height=320,
                          y_title="Delivered (PHP)", x_title="Month")
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

# === TOP CUSTOMERS + DOW ===
st.markdown('<div class="section-gap"></div>', unsafe_allow_html=True)
section_divider("Who & When", eyebrow="STAGE 5 · OPERATIONAL PATTERNS")
col1, col2 = st.columns(2)

with col1:
    with st.container(border=True):
        section_card_header("Top Customers by Delivery", "Highest delivery volume")
        if "Customer" in dr_f.columns:
            top_c = dr_f.groupby("Customer")["Delivered Amount"].sum().nlargest(10).sort_values(ascending=True).reset_index()
            fig = horizontal_bar(top_c, "Delivered Amount", "Customer",
                                 x_title="Delivered (PHP)")
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

with col2:
    with st.container(border=True):
        section_card_header("Deliveries by Day of Week", "Operational scheduling patterns", tooltip=TT["delivery_by_dow"])
        if "DEL_DOW" in dr_f.columns:
            dow_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
            dd = dr_f.groupby("DEL_DOW")["Delivered Amount"].count().reset_index()
            dd.columns = ["Day", "Count"]
            dd["Day"] = pd.Categorical(dd["Day"], categories=dow_order, ordered=True)
            dd = dd.sort_values("Day").dropna(subset=["Day"])
            fig = bar_chart(dd, "Day", "Count", height=300,
                            x_title="Day of Week", y_title="Deliveries", y_currency=False)
            fig.update_traces(hovertemplate="<b>%{x}</b><br>%{y:,} deliveries<extra></extra>")
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

# === CHANNEL & BACKLOG (inline section) ===
st.markdown('<div class="section-gap"></div>', unsafe_allow_html=True)
section_divider("Channel Mix & Forward Backlog", eyebrow="STAGE 6 · PIPELINE")
col1, col2 = st.columns(2)
with col1:
    with st.container(border=True):
        section_card_header("Booking by Channel", "Where orders come from")
        if "Group Name" in so_f.columns:
            ch = so_f.groupby("Group Name")["Booking Amount"].sum().sort_values(ascending=True).reset_index()
            fig = horizontal_bar(ch, "Booking Amount", "Group Name",
                                 x_title="Booking (PHP)", height=280, dynamic_height=False)
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

with col2:
    with st.container(border=True):
        section_card_header("Forward Backlog", "Future-dated deliveries by horizon")
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
                    fig = bar_chart(bl, "Horizon", "Value", height=280,
                                    x_title="Time Horizon", y_title="Booking (PHP)")
                    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
                else:
                    st.caption("No future delivery backlog.")

scroll_to_top_button()
