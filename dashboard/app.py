import streamlit as st
import pandas as pd
import numpy as np
import os
import time
from datetime import datetime

st.set_page_config(
    page_title="Texicon Executive Dashboard",
    layout="wide",
    initial_sidebar_state="collapsed")

# Load CSS + hide sidebar completely
css_path = os.path.join(os.path.dirname(__file__), "assets", "style.css")
with open(css_path) as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
st.markdown(
    '<style>section[data-testid="stSidebar"] { display: none !important; }</style>',
    unsafe_allow_html=True)

from components.auth import render_login, current_role, user_chip, require_role

# Login gate — must run before any data loads.
if current_role() is None:
    render_login()

# Sales users land on Sales Home, not the exec dashboard.
if current_role() == "sales":
    st.switch_page("pages/0_Sales_Home.py")

# Owner-only below this point.
require_role(allowed=["owner"])

from data.loader import load_sales_report, load_sales_order, load_delivery_report, load_collection_report, get_data_freshness
from data.transformer import (
    transform_sales_report, transform_sales_order,
    transform_delivery_report, transform_collection_report)
from components.filters import render_top_filters, apply_filters_sr, apply_filters_so, apply_filters_dr
from components.drawers import (
    top_bar, alert_banner, section_header, risk_card, insight_card,
    kpi_card, mini_card, compare_card, concentration_bar, styled_table, badge,
    risk_section_header, all_clear_box, section_card_header, render_nav,
    empty_state, scroll_to_top_button, executive_summary_panel,
    global_alert_strip, render_breadcrumb, glossary_panel, action_button_row,
    hero_kpi, section_divider)
from components.charts import (
    bar_chart, horizontal_bar, donut_chart, line_bar_combo,
    stacked_bar, area_chart, funnel_chart, treemap_chart, add_target_line)
from components.formatting import format_php, format_pct, format_number, format_days
from data.tooltips import EXEC as TT
from data.risk_engine import compute_global_risks
from components.insights import generate_executive_insights
from data.glossary import METRIC_DEFINITIONS
from data.analytics import compute_monthly_kpi_trends
from data.constants import KPI_TARGETS, WAREHOUSE_LABELS
from components.kpi_cards import (
    render_kpi_row, kpi_spec_money, kpi_spec_pct, kpi_spec_count)

t0 = time.time()

# --- Load & Transform ---
sr_raw = load_sales_report()
so_raw = load_sales_order()
dr_raw = load_delivery_report()
cr_raw = load_collection_report()

sr = transform_sales_report(sr_raw)
so = transform_sales_order(so_raw)
dr = transform_delivery_report(dr_raw)
cr = transform_collection_report(cr_raw)

# --- Navigation ---
# Compute risks early for nav badge
_pre_risks = compute_global_risks(sr, so, dr)
render_nav(active_page="app", risk_count=len(_pre_risks), role=current_role())

# --- Top Filters (collapsed by default on Executive overview) ---
filters = render_top_filters(sr, so, dr, page_key="main", expand_filters=False)
sr_f = apply_filters_sr(sr, filters)
so_f = apply_filters_so(so, filters)
dr_f = apply_filters_dr(dr, filters)

# --- Monthly KPI Trends (for sparklines) ---
kpi_trends = compute_monthly_kpi_trends(sr_f)

# --- Empty State ---
if sr_f.empty:
    data_end = "N/A"
    top_bar(data_end, datetime.now().strftime("%a, %b %d, %Y  %I:%M:%S %p"))
    user_chip()
    empty_state()
    st.stop()

# --- Top Bar with freshness ---
data_end = sr_f["DATE"].max().strftime("%B %d, %Y") if ("DATE" in sr_f.columns and pd.notna(sr_f["DATE"].max())) else "N/A"
freshness_hours = get_data_freshness()
top_bar(data_end, datetime.now().strftime("%a, %b %d, %Y  %I:%M:%S %p"),
        freshness_hours=freshness_hours)
user_chip()

# --- Page Title ---
st.markdown('<div class="page-title">Executive Dashboard</div>', unsafe_allow_html=True)
st.markdown('<div class="page-subtitle">Q1 2025-2026 Performance Overview</div>', unsafe_allow_html=True)

# ============================================
# COMPUTE ALL METRICS
# ============================================
total_net = sr_f["NET SALES"].sum()
total_gross = sr_f["GROSS SALES"].sum()
discount_amt = total_gross - total_net
discount_pct = (discount_amt / total_gross * 100) if total_gross > 0 else 0

total_bookings = so_f["Booking Amount"].sum()
total_delivered = dr_f["Delivered Amount"].sum()

active_clients = sr_f["CLIENT"].nunique() if "CLIENT" in sr_f.columns else 0
unique_invoices = sr_f["INV NO."].nunique() if "INV NO." in sr_f.columns else max(len(sr_f), 1)
total_transactions = len(sr_f)
avg_transaction = total_net / unique_invoices if unique_invoices > 0 else 0

# Volume
total_qty = sr_f["QTY IN L/KG"].sum() if "QTY IN L/KG" in sr_f.columns else 0

# Credit
credit_mask = sr_f["IS_CREDIT"] == True if "IS_CREDIT" in sr_f.columns else pd.Series(False, index=sr_f.index)
credit_sales = sr_f.loc[credit_mask, "NET SALES"].sum()
cash_sales = total_net - credit_sales
credit_pct = (credit_sales / total_net * 100) if total_net > 0 else 0

# DSO
term_days_map = {"COD": 0, "CBD": 0, "CASH": 0, "30PDC": 30, "30D": 30, "60PDC": 60, "60D": 60, "90D": 90, "120D": 120}
sr_credit = sr_f[credit_mask].copy()
if not sr_credit.empty and "TERMS" in sr_credit.columns:
    sr_credit["TERM_DAYS"] = sr_credit["TERMS"].map(term_days_map).fillna(60)
    _credit_net_sum = sr_credit["NET SALES"].sum()
    dso_estimate = (sr_credit["TERM_DAYS"] * sr_credit["NET SALES"]).sum() / _credit_net_sum if _credit_net_sum > 0 else 0
else:
    dso_estimate = 0

# Fulfillment
fulfillment_rate = (total_delivered / total_bookings * 100) if total_bookings > 0 else 0
booking_gap = total_bookings - total_net
booking_gap_pct = (booking_gap / total_bookings * 100) if total_bookings > 0 else 0

# On-time (within 7 days)
if "CYCLE_DAYS" in so_f.columns:
    valid_orders = so_f[so_f["CYCLE_DAYS"].notna()]
    on_time_pct = (len(valid_orders[valid_orders["CYCLE_DAYS"] <= 7]) / len(valid_orders) * 100) if len(valid_orders) > 0 else 0
else:
    on_time_pct = 0

# Top product
top_product = "N/A"
top_product_pct = 0
if "ITEM" in sr_f.columns:
    item_sales = sr_f.groupby("ITEM")["NET SALES"].sum()
    if not item_sales.empty:
        top_product = item_sales.idxmax()
        top_product_pct = (item_sales.max() / total_net * 100) if total_net > 0 else 0
        if len(top_product) > 20:
            top_product = top_product[:20] + "..."

# Top customer
top_customer = "N/A"
top_customer_val = 0
if "CLIENT" in sr_f.columns:
    client_sales = sr_f.groupby("CLIENT")["NET SALES"].sum()
    if not client_sales.empty:
        top_customer = client_sales.idxmax()
        top_customer_val = client_sales.max()
        if len(top_customer) > 20:
            top_customer = top_customer[:20] + "..."

# Top area
top_area = "N/A"
if "AREA GROUP" in sr_f.columns:
    area_sales = sr_f.groupby("AREA GROUP")["NET SALES"].sum()
    if not area_sales.empty:
        top_area = area_sales.idxmax()

# Collection
total_cols = [c for c in cr.columns if "TOTAL" in c.upper() and "DEPOSIT" not in c.upper()]
total_collected = cr[total_cols[0]].sum() if total_cols else 0

# Revenue per customer
rev_per_customer = total_net / active_clients if active_clients > 0 else 0

# GLYPHOTEX concentration
glyph_pct = 0
if "ITEM" in sr_f.columns and total_net > 0:
    glyphotex_mask = sr_f["ITEM"].str.contains("GLYPHOTEX", case=False, na=False)
    glyph_rev = sr_f.loc[glyphotex_mask, "NET SALES"].sum()
    glyph_pct = (glyph_rev / total_net * 100)

# ============================================
# HERO METRIC — Net Revenue (the headline)
# ============================================
months_in_data = sr_f["YEAR_MONTH"].nunique() if "YEAR_MONTH" in sr_f.columns else 0
hero_kpi(
    label="NET REVENUE",
    value=format_php(total_net),
    sub_value=f"{active_clients:,} active customers · {months_in_data} months",
    trend=kpi_trends.get("net_revenue"),
    tooltip=TT["net_revenue"],
)

# ============================================
# EXECUTIVE SUMMARY (auto-generated insights)
# ============================================
exec_insights = generate_executive_insights({
    "total_net": total_net, "total_gross": total_gross,
    "discount_pct": discount_pct, "active_clients": active_clients,
    "credit_pct": credit_pct, "fulfillment_pct": fulfillment_rate,
    "on_time_pct": on_time_pct, "glyph_pct": glyph_pct,
})
executive_summary_panel(exec_insights)

# ============================================
# COMPUTE RISK ALERTS (before rendering)
# ============================================
risks = []

if "ITEM" in sr_f.columns:
    if glyph_pct > 15:
        risks.append(("Product Concentration Risk",
                       f"GLYPHOTEX 480 SL accounts for {glyph_pct:.1f}% of total revenue ({format_php(glyph_rev)}). "
                       "Single-product dependency creates significant business risk.",
                       "warning"))

if credit_pct > 60:
    risks.append(("High Credit Exposure",
                   f"{credit_pct:.1f}% of sales ({format_php(credit_sales)}) are on credit terms. "
                   f"Estimated DSO: {dso_estimate:.0f} days. Monitor top credit accounts closely.",
                   "danger"))

if on_time_pct < 70:
    risks.append(("Delivery Performance Below Target",
                   f"Only {on_time_pct:.1f}% of orders delivered within 7 days. "
                   "Service level gaps may impact customer retention.",
                   "warning"))

if booking_gap_pct > 15:
    risks.append(("Fulfillment Gap",
                   f"Booking-to-invoice gap of {booking_gap_pct:.1f}% ({format_php(booking_gap)}). "
                   "Orders not converting to revenue \u2014 investigate supply constraints.",
                   "warning"))

# ============================================
# SUPPORTING KPI ROW (6 cards — net revenue lives in the hero above)
# ============================================
_gp_per_unit = total_net / total_qty if total_qty > 0 else 0
render_kpi_row([
    {"label": "TOTAL QTY SOLD", "value": f"{total_qty:,.0f} L/KG",
     "sub_text": f"{sr_f['QTY IN CTN'].sum():,.0f} cartons" if "QTY IN CTN" in sr_f.columns else "",
     "tooltip": TT["total_qty"], "trend_data": kpi_trends.get("qty")},
    kpi_spec_money("GROSS SALES", total_gross, tooltip=TT["gross_sales"],
                   trend_data=kpi_trends.get("net_revenue")),
    kpi_spec_pct("DISCOUNT RATE", discount_pct, thresholds=(10, 15),
                 lower_is_better=True,
                 tooltip=TT["discount_rate"], trend_data=kpi_trends.get("discount_pct")),
    {"label": "GP PER UNIT", "value": format_php(_gp_per_unit, 2) + "/L",
     "sub_text": "Net revenue / qty", "tooltip": TT["gp_per_unit"]},
    kpi_spec_count("ACTIVE CUSTOMERS", active_clients,
                   sub_text="Purchased this period", tooltip=TT["active_customers"],
                   trend_data=kpi_trends.get("active_customers")),
    kpi_spec_pct("CREDIT EXPOSURE", credit_pct, thresholds=(50, 70),
                 lower_is_better=True,
                 sub_text=f"{format_php(credit_sales)} on credit",
                 tooltip=TT["credit_exposure"],
                 card_class="danger-glow" if credit_pct > 70 else "warning-glow" if credit_pct > 60 else "",
                 trend_data=kpi_trends.get("credit_pct")),
])

# ============================================
# YOY COMPARISON ROW (5 compare cards)
# ============================================
st.markdown('<div class="section-gap"></div>', unsafe_allow_html=True)
comp_cols = st.columns(5)
with comp_cols[0]:
    compare_card("Net Revenue", format_php(total_net), f"{total_transactions:,} txns", f"{unique_invoices:,} invoices", True,
                 tooltip=TT["net_revenue"])
with comp_cols[1]:
    compare_card("Delivered Value", format_php(total_delivered), format_php(total_bookings) + " booked",
                 f"{fulfillment_rate:.1f}%", fulfillment_rate >= 85, tooltip=TT["fulfillment_rate"])
with comp_cols[2]:
    compare_card("Discount", format_php(discount_amt), format_pct(discount_pct), f"of gross sales", True,
                 tooltip=TT["discount_rate"])
with comp_cols[3]:
    compare_card("Est. DSO", f"{dso_estimate:.0f} days", f"{credit_pct:.0f}% on credit",
                 badge("Watch", "amber" if dso_estimate > 45 else "green"), dso_estimate <= 45,
                 tooltip=TT["dso"])
with comp_cols[4]:
    compare_card("On-Time Delivery", format_pct(on_time_pct), "within 7 days",
                 badge("At Risk", "red") if on_time_pct < 70 else badge("OK", "green"), on_time_pct >= 70,
                 tooltip=TT["avg_lead_time"])

# ============================================
# MONTHLY REVENUE + PRODUCT MIX (in section cards)
# ============================================
st.markdown('<div class="section-gap"></div>', unsafe_allow_html=True)
chart_col1, chart_col2 = st.columns([2, 1])

with chart_col1:
    with st.container(border=True):
        section_card_header("Monthly Revenue", "Revenue and volume trends over time",
                            tooltip=TT["monthly_revenue"])
        if "YEAR_MONTH" in sr_f.columns:
            monthly = sr_f.groupby("YEAR_MONTH").agg(
                Net=("NET SALES", "sum"), Gross=("GROSS SALES", "sum")).sort_index().reset_index()
            monthly["Month"] = monthly["YEAR_MONTH"].dt.strftime("%b %y")

            rev_tab1, rev_tab2 = st.tabs(["Revenue", "Volume"])
            with rev_tab1:
                fig = line_bar_combo(monthly, "Month", "Net", "Gross", "Net Sales", "Gross Sales",
                                     y_title="Revenue (PHP)")
                st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
            with rev_tab2:
                if "YEAR_MONTH" in sr_f.columns and "QTY IN L/KG" in sr_f.columns:
                    vol_monthly = sr_f.groupby("YEAR_MONTH")["QTY IN L/KG"].sum().sort_index().reset_index()
                    vol_monthly["Month"] = vol_monthly["YEAR_MONTH"].dt.strftime("%b %y")
                    fig = bar_chart(vol_monthly, "Month", "QTY IN L/KG", height=300,
                                    y_title="Volume (L/KG)", y_currency=False)
                    fig.update_traces(hovertemplate="<b>%{x}</b><br>%{y:,.0f} L/KG<extra></extra>")
                    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

with chart_col2:
    with st.container(border=True):
        section_card_header("Product Category Mix", "Revenue share by product type",
                            tooltip=TT["product_mix"])
        if "PRODUCT CATEGORY" in sr_f.columns:
            cat_data = sr_f.groupby("PRODUCT CATEGORY")["NET SALES"].sum().sort_values(ascending=False)
            fig = donut_chart(
                cat_data.index.tolist(), cat_data.values.tolist(),
                center_text=f"{len(cat_data)}\ncategories")
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

# ============================================
# REVENUE CONCENTRATION + CATEGORY MIX
# ============================================
st.markdown('<div class="section-gap"></div>', unsafe_allow_html=True)
conc_col1, conc_col2 = st.columns([1, 1])

with conc_col1:
    with st.container(border=True):
        section_card_header("Revenue Concentration", "Customer revenue distribution",
                            tooltip=TT["revenue_concentration"])
        if "CLIENT" in sr_f.columns:
            client_sorted = sr_f.groupby("CLIENT")["NET SALES"].sum().sort_values(ascending=False)
            n_clients = len(client_sorted)
            top5_val = client_sorted.head(5).sum()
            next5_val = client_sorted.iloc[5:10].sum() if n_clients > 5 else 0
            next10_val = client_sorted.iloc[10:20].sum() if n_clients > 10 else 0
            rest_val = client_sorted.iloc[20:].sum() if n_clients > 20 else 0

            top5_pct = (top5_val / total_net * 100) if total_net > 0 else 0
            next5_pct = (next5_val / total_net * 100) if total_net > 0 else 0
            next10_pct = (next10_val / total_net * 100) if total_net > 0 else 0
            rest_pct = 100 - top5_pct - next5_pct - next10_pct

            concentration_bar([
                (f"Top 5: {top5_pct:.1f}%", max(top5_pct, 5), "#F26D6D"),
                (f"Next 5: {next5_pct:.1f}%", max(next5_pct, 5), "#E2B04A"),
                (f"Next 10: {next10_pct:.1f}%", max(next10_pct, 5), "#6BA8FF"),
                (f"Rest: {rest_pct:.1f}%", max(rest_pct, 5), "#5A6069"),
            ])

            # Top 10 table
            top10 = sr_f.groupby("CLIENT").agg(
                Revenue=("NET SALES", "sum"),
                Qty=("QTY IN L/KG", "sum") if "QTY IN L/KG" in sr_f.columns else ("NET SALES", "count"),
                Orders=("INV NO.", "nunique") if "INV NO." in sr_f.columns else ("NET SALES", "count")).nlargest(10, "Revenue").reset_index()
            top10["Share"] = (top10["Revenue"] / total_net * 100) if total_net > 0 else 0

            rows = []
            for i, r in top10.iterrows():
                rows.append([
                    f"{len(rows)+1}",
                    r["CLIENT"][:28] + ("..." if len(r["CLIENT"]) > 28 else ""),
                    f"{r['Qty']:,.0f}",
                    f"\u20B1{r['Revenue']:,.0f}",
                    f"{r['Share']:.1f}%",
                ])
            styled_table(["#", "Customer", "Qty (L/KG)", "Revenue", "Share"], rows,
                         green_cols=[3], num_cols=[0, 2, 3, 4])

with conc_col2:
    with st.container(border=True):
        section_card_header("Revenue Mix by Category", "Monthly category share trends",
                            tooltip=TT["category_trend"])
        if "PRODUCT CATEGORY" in sr_f.columns and "YEAR_MONTH" in sr_f.columns:
            cat_monthly = sr_f.groupby(["YEAR_MONTH", "PRODUCT CATEGORY"])["NET SALES"].sum().reset_index()
            pivot = cat_monthly.pivot_table(index="YEAR_MONTH", columns="PRODUCT CATEGORY", values="NET SALES", fill_value=0).sort_index()
            _row_sums = pivot.sum(axis=1)
            pivot_pct = pivot.div(_row_sums.replace(0, np.nan), axis=0).fillna(0) * 100
            pivot_pct.index = pivot_pct.index.strftime("%b %y")

            fig = area_chart(pivot_pct.reset_index(), pivot_pct.index.name or "YEAR_MONTH",
                             pivot_pct.columns.tolist(), y_title="Share (%)")
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

# ============================================
# RISK ALERTS
# ============================================
st.markdown('<div class="section-gap"></div>', unsafe_allow_html=True)
risk_section_header("Risk Alerts", risks=risks)

if not risks:
    all_clear_box()
else:
    risk_cols = st.columns(2)
    for i, (title, desc, rtype) in enumerate(risks):
        with risk_cols[i % 2]:
            risk_card(title, desc, rtype, tooltip=TT.get(f"risk_{['product_conc','credit_exp','delivery','fulfillment'][min(i,3)]}", ""))

# ============================================
# QUICK ACTIONS (CEO buttons)
# ============================================
st.markdown('<div class="section-gap"></div>', unsafe_allow_html=True)
section_header("Quick Actions")
action_button_row()

# ============================================
# OPERATIONS & DELIVERY OVERVIEW (inline section)
# ============================================
section_divider("Operations & Delivery Overview", eyebrow="SECTION · OPERATIONS")

op_cols = st.columns(3)
with op_cols[0]:
    kpi_card("FULFILLMENT RATE", format_pct(fulfillment_rate),
             value_class="" if fulfillment_rate >= 90 else "warning" if fulfillment_rate >= 80 else "danger",
             sub_text=f"{format_php(total_delivered)} of {format_php(total_bookings)}", tooltip=TT["fulfillment_rate"],
             card_class="danger-glow" if fulfillment_rate < 80 else "")
with op_cols[1]:
    _cycle_vals = so_f["CYCLE_DAYS"].dropna() if "CYCLE_DAYS" in so_f.columns else pd.Series(dtype=float)
    avg_cycle = _cycle_vals.mean() if not _cycle_vals.empty else 0
    median_cycle = _cycle_vals.median() if not _cycle_vals.empty else 0
    kpi_card("AVG LEAD TIME", f"{avg_cycle:.1f} days",
             sub_text=f"Median: {median_cycle:.0f} days",
             tooltip=TT["avg_lead_time"])
with op_cols[2]:
    total_deliveries = dr_f["Delivery No"].nunique() if "Delivery No" in dr_f.columns else len(dr_f)
    kpi_card("TOTAL DELIVERIES", format_number(total_deliveries), value_class="neutral",
             sub_text=f"{dr_f['Warehouse'].nunique() if 'Warehouse' in dr_f.columns else 0} warehouses")

st.markdown('<div class="section-gap-sm"></div>', unsafe_allow_html=True)
wh_col1, wh_col2 = st.columns([1, 2])
with wh_col1:
    if "Warehouse" in dr_f.columns:
        with st.container(border=True):
            section_card_header("Warehouse Split", "Delivered value by warehouse")
            wh_data = dr_f.groupby("Warehouse")["Delivered Amount"].sum().sort_values(ascending=False)
            wh_labels = [WAREHOUSE_LABELS.get(k, k) for k in wh_data.index]
            fig = donut_chart(wh_labels, wh_data.values.tolist(), height=260,
                              center_text=f"{len(wh_data)}\nwarehouses")
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
with wh_col2:
    if "DEL_MONTH" in dr_f.columns:
        with st.container(border=True):
            section_card_header("Monthly Deliveries", "Delivered value and count by month")
            del_monthly = dr_f.groupby("DEL_MONTH").agg(
                Count=("Delivered Amount", "count"),
                Value=("Delivered Amount", "sum")).sort_index().reset_index()
            del_monthly["Month"] = del_monthly["DEL_MONTH"].dt.strftime("%b %y")
            fig = line_bar_combo(del_monthly, "Month", "Value", "Count",
                                 "Delivered Value", "Deliveries", height=260,
                                 y_title="Delivered Value (PHP)",
                                 line_on_secondary=True, line_currency=False,
                                 line_y_title="Deliveries (count)")
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

# ============================================
# CUSTOMER ECONOMICS (inline section)
# ============================================
section_divider("Customer Economics", eyebrow="SECTION · CUSTOMERS")

ce_cols = st.columns(3)
if "CLIENT" in sr_f.columns:
    client_freq = sr_f.groupby("CLIENT").size()
    repeat = (client_freq >= 6).sum()
    occasional = ((client_freq >= 2) & (client_freq < 6)).sum()
    onetime = (client_freq == 1).sum()
    repeat_rev = sr_f[sr_f["CLIENT"].isin(client_freq[client_freq >= 6].index)]["NET SALES"].sum()
    repeat_pct = (repeat_rev / total_net * 100) if total_net > 0 else 0
else:
    repeat, occasional, onetime, repeat_pct = 0, 0, 0, 0

with ce_cols[0]:
    kpi_card("LOYAL CUSTOMERS", format_number(repeat),
             sub_text=f"{repeat_pct:.0f}% of revenue \u2022 6+ orders")
with ce_cols[1]:
    kpi_card("OCCASIONAL", format_number(occasional), value_class="warning",
             sub_text="2-5 orders in period")
with ce_cols[2]:
    kpi_card("ONE-TIME", format_number(onetime), value_class="neutral",
             sub_text="Single purchase only")

if "AREA GROUP" in sr_f.columns:
    st.markdown('<div class="section-gap-sm"></div>', unsafe_allow_html=True)
    geo_cols = st.columns(3)
    area_data = sr_f.groupby("AREA GROUP").agg(
        Revenue=("NET SALES", "sum"),
        Clients=("CLIENT", "nunique"),
        Transactions=("NET SALES", "count")).sort_values("Revenue", ascending=False)

    for i, (area, row) in enumerate(area_data.iterrows()):
        with geo_cols[i % 3]:
            pct = (row["Revenue"] / total_net * 100) if total_net > 0 else 0
            compare_card(area, format_php(row["Revenue"]),
                         f"{row['Clients']:,.0f} clients", f"{pct:.1f}%", True,
                         tooltip=TT["area_performance"])

# ============================================
# WORKING CAPITAL & CASH FLOW (inline section)
# ============================================
section_divider("Working Capital & Cash Flow", eyebrow="SECTION · CASH FLOW")

wc_cols = st.columns(3)
with wc_cols[0]:
    kpi_card("CREDIT SALES", format_php(credit_sales),
             value_class="danger" if credit_pct > 70 else "",
             sub_text=f"{credit_pct:.1f}% of total revenue",
             tooltip=TT["credit_exposure"])
with wc_cols[1]:
    kpi_card("EST. DSO", f"{dso_estimate:.0f} days",
             value_class="danger" if dso_estimate > 60 else "warning",
             sub_text="Weighted by sales amount",
             tooltip=TT["dso"])
with wc_cols[2]:
    kpi_card("COLLECTIONS (SAMPLE)", format_php(total_collected), value_class="neutral",
             sub_text="Apr 6-10, 2026 only")

st.markdown('<div class="section-gap-sm"></div>', unsafe_allow_html=True)
wc2_cols = st.columns(3)
with wc2_cols[0]:
    kpi_card("TRANSACTION VOLUME", format_number(total_transactions), value_class="neutral",
             sub_text="line items in period")
with wc2_cols[1]:
    kpi_card("AVG REVENUE / TX", format_php(avg_transaction), value_class="neutral",
             sub_text="per invoice")
with wc2_cols[2]:
    kpi_card("REVENUE / CUSTOMER", format_php(rev_per_customer), value_class="neutral",
             sub_text=f"across {active_clients} customers",
             tooltip=TT["rev_per_customer"])

# ============================================
# SCROLL TO TOP + COMPUTE TIME
# ============================================
# Re-render top_bar with compute time now that everything is rendered
_compute_ms = int((time.time() - t0) * 1000)
st.markdown(f'<div style="text-align:right; font-size:var(--f-xs); color:var(--fg-3); margin-top:var(--s-4);">Rendered in {_compute_ms}ms</div>', unsafe_allow_html=True)
scroll_to_top_button()
