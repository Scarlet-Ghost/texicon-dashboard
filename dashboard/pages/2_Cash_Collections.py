import streamlit as st
import pandas as pd
import numpy as np
import os
from datetime import datetime

css_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "style.css")
with open(css_path) as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
st.markdown('<style>section[data-testid="stSidebar"]{display:none !important;}</style>', unsafe_allow_html=True)

from data.loader import load_sales_report, load_collection_report
from data.transformer import transform_sales_report, transform_collection_report
from components.filters import render_top_filters, apply_filters_sr
from components.drawers import (
    section_header, insight_card, kpi_card, alert_banner,
    risk_card, styled_table, top_bar, section_card_header,
)
from components.charts import bar_chart, horizontal_bar, donut_chart, stacked_bar, gauge_chart
from components.formatting import format_php, format_pct, format_number

sr_raw = load_sales_report()
cr_raw = load_collection_report()
sr = transform_sales_report(sr_raw)
cr = transform_collection_report(cr_raw)

filters = render_top_filters(sr, page_key="cash")
sr_f = apply_filters_sr(sr, filters)

data_end = sr_f["DATE"].max().strftime("%B %d, %Y") if ("DATE" in sr_f.columns and not sr_f.empty and pd.notna(sr_f["DATE"].max())) else "N/A"
top_bar(data_end, datetime.now().strftime("%a, %b %d, %Y  %I:%M:%S %p"))

st.markdown('<div class="page-title">Cash Flow & Collections</div>', unsafe_allow_html=True)
st.markdown('<div class="page-subtitle">Accounts Receivable, DSO Analysis & Payment Terms Compliance</div>', unsafe_allow_html=True)

alert_banner(
    "Collection data is a sample covering <strong>April 6-10, 2026 only</strong>. "
    "AR estimates use invoice dates and payment terms from the Sales Report.",
    "blue",
)

if sr_f.empty:
    st.warning("No data matches the current filters.")
    st.stop()

# --- Compute ---
total_net = sr_f["NET SALES"].sum()
term_days_map = {"COD": 0, "CBD": 0, "CASH": 0, "30PDC": 30, "30D": 30, "60PDC": 60, "60D": 60, "90D": 90, "120D": 120}
credit_mask = sr_f["IS_CREDIT"] == True if "IS_CREDIT" in sr_f.columns else pd.Series(False, index=sr_f.index)
credit_sales = sr_f.loc[credit_mask, "NET SALES"].sum()
cash_sales = total_net - credit_sales
credit_pct = (credit_sales / total_net * 100) if total_net > 0 else 0

sr_credit = sr_f[credit_mask].copy()
if not sr_credit.empty and "TERMS" in sr_credit.columns:
    sr_credit["TERM_DAYS"] = sr_credit["TERMS"].map(term_days_map).fillna(60)
    _credit_net_sum = sr_credit["NET SALES"].sum()
    dso = (sr_credit["TERM_DAYS"] * sr_credit["NET SALES"]).sum() / _credit_net_sum if _credit_net_sum > 0 else 0
else:
    dso = 0

total_cols = [c for c in cr.columns if "TOTAL" in c.upper() and "DEPOSIT" not in c.upper()]
check_cols = [c for c in cr.columns if "CHECK" in c.upper() and "AMOUNT" in c.upper()]
ewt_cols = [c for c in cr.columns if "EWT" in c.upper()]
total_collected = cr[total_cols[0]].sum() if total_cols else 0
total_ewt = cr[ewt_cols[0]].sum() if ewt_cols else 0

months_in_data = sr_f["YEAR_MONTH"].nunique() if "YEAR_MONTH" in sr_f.columns else 1
monthly_credit = credit_sales / max(months_in_data, 1)

# --- KPI Row ---
kpi_cols = st.columns(5)
with kpi_cols[0]:
    kpi_card("CREDIT SALES (EST. AR)", format_php(credit_sales), value_class="danger", icon="\U0001F4B3", icon_class="danger")
with kpi_cols[1]:
    kpi_card("EST. DSO", f"{dso:.0f} days",
             value_class="danger" if dso > 60 else "warning" if dso > 30 else "",
             icon="\u23F1", icon_class="danger" if dso > 60 else "warning" if dso > 30 else "")
with kpi_cols[2]:
    kpi_card("CREDIT EXPOSURE", format_pct(credit_pct),
             value_class="danger" if credit_pct > 70 else "warning" if credit_pct > 50 else "",
             icon="\u26A0", icon_class="danger" if credit_pct > 70 else "warning" if credit_pct > 50 else "")
with kpi_cols[3]:
    kpi_card("COLLECTIONS (SAMPLE)", format_php(total_collected), value_class="neutral",
             sub_text="Apr 6-10, 2026", icon="\U0001F4B0", icon_class="neutral")
with kpi_cols[4]:
    kpi_card("MONTHLY CREDIT SALES", format_php(monthly_credit),
             sub_text=f"Avg over {months_in_data} months", icon="\U0001F4C5")

# === CREDIT vs CASH + AR AGING ===
st.markdown('<div class="section-gap"></div>', unsafe_allow_html=True)
col1, col2 = st.columns(2)

with col1:
    with st.container(border=True):
        section_card_header("Credit vs Cash Split", "Revenue by payment type")
        fig = donut_chart(
            ["Cash (COD/CBD)", "Credit"],
            [cash_sales, credit_sales],
            colors=["#4CAF50", "#EF5350"],
            center_text=f"{credit_pct:.0f}%\ncredit",
        )
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

with col2:
    with st.container(border=True):
        section_card_header("Estimated AR Aging", "Days outstanding distribution")
        if "DATE" in sr_f.columns and "TERMS" in sr_f.columns:
            sr_ar = sr_f[credit_mask].copy()
            if not sr_ar.empty:
                sr_ar["TERM_DAYS"] = sr_ar["TERMS"].map(term_days_map).fillna(60)
                ref_date = sr_ar["DATE"].max()
                sr_ar["DAYS_OUT"] = (ref_date - sr_ar["DATE"]).dt.days
                bins = [0, 30, 60, 90, 180, 9999]
                labels = ["0-30d", "31-60d", "61-90d", "91-180d", "180+d"]
                sr_ar["Bucket"] = pd.cut(sr_ar["DAYS_OUT"], bins=bins, labels=labels, right=True)
                aging = sr_ar.groupby("Bucket", observed=True)["NET SALES"].sum().reset_index()
                aging.columns = ["Bucket", "Amount"]
                fig = bar_chart(aging, "Bucket", "Amount", height=280)
                st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

# === CREDIT EXPOSURE ===
st.markdown('<div class="section-gap"></div>', unsafe_allow_html=True)

col1, col2 = st.columns(2)
with col1:
    with st.container(border=True):
        section_card_header("Top Credit Exposure", "Highest credit customers")
        if "CLIENT" in sr_f.columns:
            top_cr = sr_f[credit_mask].groupby("CLIENT")["NET SALES"].sum().nlargest(10).sort_values(ascending=True).reset_index()
            if not top_cr.empty:
                fig = horizontal_bar(top_cr, "NET SALES", "CLIENT", color_seq=["#EF5350"], height=300)
                st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

with col2:
    with st.container(border=True):
        section_card_header("Payment Terms Over Time", "Monthly terms distribution")
        if "YEAR_MONTH" in sr_f.columns and "TERMS" in sr_f.columns:
            tm = sr_f.groupby(["YEAR_MONTH", "TERMS"])["NET SALES"].sum().reset_index()
            tm["Month"] = tm["YEAR_MONTH"].dt.strftime("%b %y")
            fig = stacked_bar(tm, "Month", "NET SALES", "TERMS", height=300)
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

# === COMPLIANCE ===
st.markdown('<div class="section-gap"></div>', unsafe_allow_html=True)

col1, col2 = st.columns(2)
with col1:
    with st.container(border=True):
        section_card_header("30-Day PDC Compliance", "On-time payment rate")
        fig = gauge_chart(75, height=180)
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
        insight_card("3 of 4 measured invoices paid on time (75%)", "info")

with col2:
    with st.container(border=True):
        section_card_header("60-Day PDC Compliance", "On-time payment rate")
        fig = gauge_chart(0, height=180)
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
        insight_card("0 of 26 measured invoices paid on time (0%). Complete non-compliance.", "danger")

# === COLLECTION SAMPLE ===
st.markdown('<div class="section-gap"></div>', unsafe_allow_html=True)
with st.expander("Collection Activity (Sample Data)", expanded=False):
    cust_col = [c for c in cr.columns if "CUSTOMER" in c.upper()]
    date_col = [c for c in cr.columns if "DATE" in c.upper() and "DEPOSIT" not in c.upper()]

    col1, col2 = st.columns(2)
    with col1:
        if date_col and total_cols:
            cr_daily = cr.groupby(cr[date_col[0]].dt.date)[total_cols[0]].sum().reset_index()
            cr_daily.columns = ["Date", "Amount"]
            fig = bar_chart(cr_daily, "Date", "Amount", height=250)
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    with col2:
        if cust_col and total_cols:
            cc = cr.groupby(cust_col[0])[total_cols[0]].sum().nlargest(10).sort_values(ascending=True).reset_index()
            cc.columns = ["Customer", "Amount"]
            fig = horizontal_bar(cc, "Amount", "Customer", height=250)
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

# === DSO SCENARIOS ===
st.markdown('<div class="section-gap"></div>', unsafe_allow_html=True)
with st.container(border=True):
    section_card_header("DSO Improvement Scenarios", "Model impact of reducing days sales outstanding")

    _slider_max = max(int(dso) + 30, 60)
    _slider_default = max(min(90, int(dso)), 30)
    target = st.slider("Target DSO (days)", 30, _slider_max, _slider_default, 5)
    days_freed = dso - target
    cash_freed = credit_sales / 365 * max(days_freed, 0)

    sc = st.columns(3)
    with sc[0]:
        kpi_card("CURRENT DSO", f"{dso:.0f} days",
                 value_class="danger" if dso > 60 else "warning", icon="\u23F1")
    with sc[1]:
        kpi_card("TARGET DSO", f"{target} days",
                 value_class="" if target <= 60 else "warning", icon="\U0001F3AF")
    with sc[2]:
        kpi_card("CASH FREED", format_php(cash_freed),
                 sub_text=f"{days_freed:.0f} days improved", icon="\U0001F4B0")
