import streamlit as st
import pandas as pd
import numpy as np
import os
from datetime import datetime

css_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "style.css")
with open(css_path) as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
st.markdown('<style>section[data-testid="stSidebar"]{display:none !important;}</style>', unsafe_allow_html=True)

from components.auth import require_role, user_chip, current_role

require_role(allowed=["owner"])

from data.loader import load_sales_report, load_collection_report, get_data_freshness, load_sales_order, load_delivery_report
from data.transformer import transform_sales_report, transform_collection_report, transform_sales_order, transform_delivery_report
from data.tooltips import CASH as TT
from data.risk_engine import compute_global_risks
from data.analytics import build_kpi_trends, try_compute_pdc_compliance
from components.filters import render_top_filters, apply_filters_sr
from components.drawers import (
    section_header, insight_card, kpi_card, alert_banner,
    risk_card, styled_table, top_bar, section_card_header, render_nav,
    empty_state, scroll_to_top_button, global_alert_strip, render_breadcrumb,
    hero_kpi, section_divider)
from components.kpi_cards import (
    render_kpi_row, kpi_spec_money, kpi_spec_pct, kpi_spec_days, kpi_spec_count)
from data.constants import KPI_TARGETS, PAYMENT_TERM_COLORS
from components.charts import (
    bar_chart, horizontal_bar, donut_chart, stacked_bar, gauge_chart,
    add_target_line, color_by_aging_bucket)
from components.formatting import format_php, format_pct, format_number


# Per-page KPI caveat registry — caller never has to remember to add sub_text.
# `{label_key: sub_text_template}`. Templates can be plain strings or callables
# of (locals,) returning a string.
KPI_REGISTRY = {
    "credit_ar":     lambda c: f"Estimated · n={c['credit_n']:,} invoices",
    "est_dso":       "Weighted by sales · est. from terms",
    "cr_exposure":   lambda c: f"{format_php(c['credit_sales'])} on credit",
    "collections":   "Sample · Apr 6-10, 2026",
    "mthly_credit":  lambda c: f"Avg over {c['months_in_data']} months",
}


def _caveat(key, ctx):
    v = KPI_REGISTRY.get(key)
    return v(ctx) if callable(v) else v


sr_raw = load_sales_report()
cr_raw = load_collection_report()
so_raw = load_sales_order()
dr_raw = load_delivery_report()
sr = transform_sales_report(sr_raw)
cr = transform_collection_report(cr_raw)
so = transform_sales_order(so_raw)
dr = transform_delivery_report(dr_raw)

_risks = compute_global_risks(sr, so, dr)
render_nav(active_page="2_Cash_Collections", risk_count=len(_risks), role=current_role())
render_breadcrumb([("Executive", "app"), ("Cash Flow & Collections", None)])
if _risks:
    global_alert_strip(_risks)
filters = render_top_filters(sr, page_key="cash", expand_filters=False)
sr_f = apply_filters_sr(sr, filters)

data_end = sr_f["DATE"].max().strftime("%B %d, %Y") if ("DATE" in sr_f.columns and not sr_f.empty and pd.notna(sr_f["DATE"].max())) else "N/A"
top_bar(data_end, datetime.now().strftime("%a, %b %d, %Y  %I:%M:%S %p"), freshness_hours=get_data_freshness())
user_chip()

st.markdown('<div class="page-title">Cash Flow & Collections</div>', unsafe_allow_html=True)
st.markdown('<div class="page-subtitle">Accounts Receivable, DSO Analysis & Payment Terms Compliance</div>', unsafe_allow_html=True)

alert_banner(
    "<strong>Limited Data:</strong> Collection data covers only "
    "<strong>April 6-10, 2026</strong>. AR estimates are derived from sales report "
    "payment terms, not actual receivables. Treat all figures as approximations.",
    "amber")

if sr_f.empty:
    empty_state()
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

# Caveat context (shared with KPI_REGISTRY)
_ctx = {
    "credit_n": int(credit_mask.sum()),
    "credit_sales": credit_sales,
    "months_in_data": months_in_data,
}

# Trends for sparklines
trends = build_kpi_trends(sr_f)

# --- HERO: CREDIT AR (danger) ---
hero_kpi(
    label="CREDIT AR EXPOSURE",
    value=format_php(credit_sales),
    sub_value=f"{credit_pct:.1f}% of {format_php(total_net)} revenue · n={_ctx['credit_n']:,} invoices",
    trend=trends.get("net_revenue"),
    tooltip=TT["credit_sales_ar"],
    value_class="danger",
    spark_color="#F26D6D",
)

# --- SUPPORTING KPI ROW (4 cards) ---
render_kpi_row([
    kpi_spec_days("EST. DSO", dso, thresholds=(30, 60),
                  tooltip=TT["est_dso"], sub_text=_caveat("est_dso", _ctx),
                  trend_data=trends.get("dso_estimate"),
                  card_class="danger-glow" if dso > 60 else ""),
    kpi_spec_pct("CR EXPOSURE", credit_pct, thresholds=(50, 70),
                 lower_is_better=True,
                 tooltip=TT["credit_exposure"], sub_text=_caveat("cr_exposure", _ctx),
                 trend_data=trends.get("credit_pct")),
    kpi_spec_money("COLLECTIONS", total_collected,
                   tooltip=TT["collections_total"], sub_text=_caveat("collections", _ctx)),
    kpi_spec_money("MTHLY CREDIT", monthly_credit, lower_is_better=True,
                   tooltip=TT["monthly_credit"], sub_text=_caveat("mthly_credit", _ctx),
                   trend_data=trends.get("net_revenue")),
])

# === CREDIT vs CASH + AR AGING ===
st.markdown('<div class="section-gap"></div>', unsafe_allow_html=True)
col1, col2 = st.columns(2)

with col1:
    with st.container(border=True):
        section_card_header("Credit vs Cash Split", "Revenue by payment type", tooltip=TT["credit_cash_split"])
        fig = donut_chart(
            ["Cash (COD/CBD)", "Credit"],
            [cash_sales, credit_sales],
            colors=["#00D68F", "#F26D6D"],
            center_text=f"{credit_pct:.0f}%\ncredit")
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

# Aging bucket data — needed by both AR Aging chart and Top Credit Exposure coloring
aging_per_client = {}
sr_ar = pd.DataFrame()
if "DATE" in sr_f.columns and "TERMS" in sr_f.columns:
    sr_ar = sr_f[credit_mask].copy()
    if not sr_ar.empty:
        sr_ar["TERM_DAYS"] = sr_ar["TERMS"].map(term_days_map).fillna(60)
        ref_date = sr_ar["DATE"].max()
        sr_ar["DAYS_OUT"] = (ref_date - sr_ar["DATE"]).dt.days
        bins = [0, 30, 60, 90, 180, 9999]
        bucket_labels = ["0-30d", "31-60d", "61-90d", "91-180d", "180+d"]
        sr_ar["Bucket"] = pd.cut(sr_ar["DAYS_OUT"], bins=bins, labels=bucket_labels, right=True)
        # Dominant bucket per client (by NET SALES)
        if "CLIENT" in sr_ar.columns:
            cb = sr_ar.groupby(["CLIENT", "Bucket"], observed=True)["NET SALES"].sum().reset_index()
            cb_top = cb.sort_values("NET SALES", ascending=False).drop_duplicates("CLIENT")
            aging_per_client = dict(zip(cb_top["CLIENT"], cb_top["Bucket"].astype(str)))

with col2:
    with st.container(border=True):
        section_card_header("Estimated AR Aging", "Days outstanding distribution", tooltip=TT["ar_aging"])
        if not sr_ar.empty:
            aging = sr_ar.groupby("Bucket", observed=True)["NET SALES"].sum().reset_index()
            aging.columns = ["Bucket", "Amount"]
            fig = bar_chart(aging, "Bucket", "Amount", height=280,
                            x_title="Aging Bucket", y_title="Outstanding (PHP)")
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

# === CREDIT EXPOSURE ===
st.markdown('<div class="section-gap"></div>', unsafe_allow_html=True)

col1, col2 = st.columns(2)
with col1:
    with st.container(border=True):
        section_card_header("Top Credit Exposure", "Highest credit customers (color = aging bucket)", tooltip=TT["top_credit_exposure"])
        if "CLIENT" in sr_f.columns:
            top_cr = sr_f[credit_mask].groupby("CLIENT")["NET SALES"].sum().nlargest(10).sort_values(ascending=True).reset_index()
            if not top_cr.empty:
                # color each bar by that client's dominant aging bucket
                color_seq = color_by_aging_bucket(top_cr["CLIENT"].tolist(), aging_per_client)
                # Plotly express needs a per-row color column when sequence varies
                top_cr_colored = top_cr.copy()
                top_cr_colored["_aging"] = [aging_per_client.get(c, "0-30d") for c in top_cr_colored["CLIENT"]]
                fig = bar_chart(top_cr_colored, x="NET SALES", y="CLIENT", color="_aging",
                                color_map={
                                    "0-30d":   "#00D68F",
                                    "31-60d":  "#E2B04A",
                                    "61-90d":  "#D39B3C",
                                    "91-180d": "#F26D6D",
                                    "180+d":   "#9E3636",
                                },
                                orientation="h", height=380,
                                x_title="Credit Exposure (PHP)", y_title="")
                fig.update_yaxes(autorange="reversed")
                st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

with col2:
    with st.container(border=True):
        section_card_header("Payment Terms Over Time", "Cash → credit gradient", tooltip=TT["terms_over_time"])
        if "YEAR_MONTH" in sr_f.columns and "TERMS" in sr_f.columns:
            tm = sr_f.groupby(["YEAR_MONTH", "TERMS"])["NET SALES"].sum().reset_index()
            tm["Month"] = tm["YEAR_MONTH"].dt.strftime("%b %y")
            fig = stacked_bar(tm, "Month", "NET SALES", "TERMS", height=300,
                              color_map=PAYMENT_TERM_COLORS,
                              y_title="Revenue (PHP)", x_title="Month")
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

# === COMPLIANCE ===
st.markdown('<div class="section-gap"></div>', unsafe_allow_html=True)

_pdc = try_compute_pdc_compliance(sr_f, cr)
with st.container(border=True):
    section_card_header("Payment-Date Compliance (PDC)", "30-day and 60-day on-time rates", tooltip=TT["compliance_30d"])
    if _pdc:
        pcol1, pcol2, pcol3 = st.columns([1, 1, 1.2])
        with pcol1:
            st.markdown('<div style="font-size:var(--f-xs); color:var(--fg-2); text-transform:uppercase; letter-spacing:0.06em; font-weight:500; margin-bottom:var(--s-2);">30-DAY COMPLIANCE</div>', unsafe_allow_html=True)
            fig = gauge_chart(_pdc["30d_pct"], height=160, target=90)
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
        with pcol2:
            st.markdown('<div style="font-size:var(--f-xs); color:var(--fg-2); text-transform:uppercase; letter-spacing:0.06em; font-weight:500; margin-bottom:var(--s-2);">60-DAY COMPLIANCE</div>', unsafe_allow_html=True)
            fig = gauge_chart(_pdc["60d_pct"], height=160, target=90)
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
        with pcol3:
            insight_card(
                f"<strong>30-day:</strong> {_pdc['30d_paid']} of {_pdc['30d_n']} invoices paid on time. Target 90%.",
                "info" if _pdc["30d_pct"] >= 75 else "warning",
            )
            insight_card(
                f"<strong>60-day:</strong> {_pdc['60d_paid']} of {_pdc['60d_n']} invoices paid on time. Target 90%.",
                "info" if _pdc["60d_pct"] >= 75 else "danger" if _pdc["60d_pct"] < 50 else "warning",
            )
    else:
        alert_banner(
            "<strong>Metric disabled.</strong> PDC compliance requires matching invoices to "
            "actual collection dates. Current collection sample (Apr 6-10, 2026) does not "
            "yield enough joined records (need n &ge; 20 per bucket) to compute reliable 30-day "
            "and 60-day on-time rates. This panel will activate when full collection data is loaded.",
            "amber")

# === COLLECTION SAMPLE ===
st.markdown('<div class="section-gap"></div>', unsafe_allow_html=True)
with st.expander("Collection Activity (Sample Data)", expanded=True):
    cust_col = [c for c in cr.columns if "CUSTOMER" in c.upper()]
    date_col = [c for c in cr.columns if "DATE" in c.upper() and "DEPOSIT" not in c.upper()]

    col1, col2 = st.columns(2)
    with col1:
        if date_col and total_cols:
            cr_daily = cr.groupby(cr[date_col[0]].dt.date)[total_cols[0]].sum().reset_index()
            cr_daily.columns = ["Date", "Amount"]
            fig = bar_chart(cr_daily, "Date", "Amount", height=250,
                            x_title="Date", y_title="Collected (PHP)")
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    with col2:
        if cust_col and total_cols:
            cc = cr.groupby(cust_col[0])[total_cols[0]].sum().nlargest(10).sort_values(ascending=True).reset_index()
            cc.columns = ["Customer", "Amount"]
            fig = horizontal_bar(cc, "Amount", "Customer", height=250,
                                 x_title="Collected (PHP)")
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

# === DSO SCENARIOS ===
st.markdown('<div class="section-gap"></div>', unsafe_allow_html=True)
with st.container(border=True):
    section_card_header("DSO Improvement Scenarios", "Model impact of reducing days sales outstanding", tooltip=TT["dso_scenario"])

    _slider_max = max(int(dso) + 30, 60)
    _slider_default = max(30, int(dso) - 15)
    target = st.slider("Target DSO (days)", 30, _slider_max, _slider_default, 5)
    days_freed = max(dso - target, 0)
    cash_freed = credit_sales / 365 * days_freed

    # Merged summary panel (replaces the 3-card row)
    st.markdown(
        f'''<div class="hero-kpi" style="margin-top:var(--s-4); margin-bottom:0;">
            <div class="hero-kpi-label">CASH FREED AT TARGET DSO</div>
            <div class="hero-kpi-value accent">{format_php(cash_freed)}</div>
            <div class="hero-kpi-meta">
                <span class="hero-kpi-sub">Current: <strong style="color:var(--fg-0);">{dso:.0f}d</strong> → Target: <strong style="color:var(--fg-0);">{target:.0f}d</strong></span>
                <span class="hero-kpi-delta positive">{days_freed:.0f} days improved</span>
            </div>
        </div>''',
        unsafe_allow_html=True,
    )

scroll_to_top_button()
