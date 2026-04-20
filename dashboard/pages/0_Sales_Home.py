"""Sales Home — landing page for the sales role.

Shows active customers, new customers, at-risk / falling-out counts,
top 10 customers YTD, top 10 items YTD. No cost / margin / AR / ops data.
"""
import streamlit as st
import pandas as pd
import os
from datetime import datetime

st.set_page_config(
    page_title="Texicon — Sales Home",
    layout="wide",
    initial_sidebar_state="collapsed",
)

css_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "style.css")
with open(css_path) as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
st.markdown(
    '<style>section[data-testid="stSidebar"]{display:none !important;}</style>',
    unsafe_allow_html=True,
)

from components.auth import require_role, user_chip, current_role

require_role(allowed=["sales"])

from data.loader import load_sales_report, get_data_freshness
from data.transformer import transform_sales_report
from data.reconnection import build_reconnection_data
from data.analytics import (
    get_active_customers_this_month,
    get_new_customers_this_month,
    get_top_customers_ytd,
    get_top_items_ytd,
)
from components.drawers import (
    top_bar, render_nav, render_breadcrumb,
    section_header, hero_kpi, styled_table, empty_state,
)
from components.kpi_cards import render_kpi_row, kpi_spec_count
from components.formatting import format_php, format_number

# --- Load & Transform ---
sr_raw = load_sales_report()
sr = transform_sales_report(sr_raw)
freshness_hours = get_data_freshness()

now = datetime.now()
top_bar(
    data_date=now.strftime("%b %d, %Y"),
    current_time=now.strftime("%I:%M %p"),
    freshness_hours=freshness_hours,
)
user_chip()

render_nav(active_page="0_Sales_Home", risk_count=0, role=current_role())
render_breadcrumb([("Sales Home", None)])

# --- Hero KPI: active customers this month ---
active = get_active_customers_this_month(sr)
hero_kpi(
    label="Active Customers This Month",
    value=format_number(active),
    sub_value="unique customers with at least one order",
)

# --- Mini-KPI row: new / at-risk / falling-out ---
new_count = get_new_customers_this_month(sr)
recon = build_reconnection_data(sr)
at_risk = int((recon["segment"] == "At Risk").sum()) if not recon.empty else 0
falling = int((recon["segment"] == "Falling Out").sum()) if not recon.empty else 0

render_kpi_row([
    kpi_spec_count("New this month", new_count),
    kpi_spec_count("At Risk", at_risk),
    kpi_spec_count("Falling Out", falling),
])

# --- Top 10 customers YTD ---
section_header("Top 10 Customers — Year to Date")
top_cust = get_top_customers_ytd(sr, n=10)
if top_cust.empty:
    empty_state("No customer revenue yet this year.")
else:
    display = top_cust.copy()
    display["revenue"] = display["revenue"].apply(format_php)
    display["last_order_date"] = pd.to_datetime(display["last_order_date"]).dt.strftime("%b %d, %Y")
    display.columns = ["Customer", "Revenue", "Orders", "Last Order"]
    styled_table(display)

# --- Top 10 items YTD ---
section_header("Top 10 Items — Year to Date")
top_items = get_top_items_ytd(sr, n=10)
if top_items.empty:
    empty_state("No item revenue yet this year.")
else:
    display = top_items.copy()
    display["revenue"] = display["revenue"].apply(format_php)
    if "qty" in display.columns:
        display["qty"] = display["qty"].apply(format_number)
        display.columns = ["Item", "Revenue", "Qty"]
    else:
        display.columns = ["Item", "Revenue"]
    styled_table(display)
