import streamlit as st
st.set_page_config(page_title="Customer Reconnection — Texicon", layout="wide",
                   initial_sidebar_state="collapsed")

try:
    from components.theme import inject_css, current_theme
    from components.drawers import render_top_bar
except ModuleNotFoundError:
    from dashboard.components.theme import inject_css, current_theme
    from dashboard.components.drawers import render_top_bar

st.markdown(inject_css(current_theme()), unsafe_allow_html=True)
render_top_bar(active_page="Reconnect")

import pandas as pd
import os

from components.auth import require_role, current_role

require_role(allowed=["owner", "sales"])

from data.loader import load_sales_report, load_sales_order, load_delivery_report, get_data_freshness
from data.transformer import transform_sales_report, transform_sales_order, transform_delivery_report
from data.tooltips import RECONNECT as TT
from data.risk_engine import compute_global_risks
from data.reconnection import build_reconnection_data, get_customer_transactions, get_segment_summary
from components.filters import render_top_filters, apply_filters_sr
from components.drawers import (
    kpi_card, section_header, insight_card, styled_table,
    badge, mini_card, top_bar, section_card_header, render_nav,
    empty_state, scroll_to_top_button, global_alert_strip, render_breadcrumb,
    hero_kpi)
from components.charts import donut_chart, bar_chart, horizontal_bar, stacked_bar
from components.formatting import format_php, format_number
from components.kpi_cards import render_kpi_row, kpi_spec_count
from data.constants import RECON_COLORS, RECON_SEGMENT_ORDER
from datetime import datetime

# -- Load & Transform --
sr_raw = load_sales_report()
so_raw = load_sales_order()
dr_raw = load_delivery_report()
sr = transform_sales_report(sr_raw)
so = transform_sales_order(so_raw)
dr = transform_delivery_report(dr_raw)

_role = current_role()
if _role == "owner":
    _risks = compute_global_risks(sr, so, dr)
else:
    _risks = []

if _role == "sales":
    render_breadcrumb([("Sales Home", "0_Sales_Home"), ("Customer Reconnection", None)])
else:
    render_breadcrumb([("Executive", "app"), ("Customer Reconnection", None)])

if _risks and _role == "owner":
    global_alert_strip(_risks)
filters = render_top_filters(sr, page_key="recon", expand_filters=False)
sr_f = apply_filters_sr(sr, filters)

if sr_f.empty:
    empty_state()
    st.stop()

cust_df = build_reconnection_data(sr_f)

if cust_df.empty:
    empty_state("No customer data available.", "Try adjusting your date range or filter criteria.")
    st.stop()

data_end = sr_f["DATE"].max().strftime("%B %d, %Y") if pd.notna(sr_f["DATE"].max()) else "N/A"

st.markdown('<div class="page-title">Customer Reconnection</div>', unsafe_allow_html=True)
st.markdown('<div class="page-subtitle">Identify inactive customers and prioritize re-engagement actions</div>', unsafe_allow_html=True)

# -- Hero: Falling Out (the metric that drives the page) --
summary = get_segment_summary(cust_df)
fo_count_hero = summary["Falling Out"]["count"]
fo_rev_hero = summary["Falling Out"]["revenue"]
total_hero = summary["total_customers"]
fo_share_hero = (fo_count_hero / total_hero * 100) if total_hero > 0 else 0

hero_kpi(
    label="FALLING OUT CUSTOMERS",
    value=format_number(fo_count_hero),
    sub_value=f"{fo_share_hero:.1f}% of {total_hero:,} customers \u00b7 {format_php(fo_rev_hero)} revenue at risk (>90d inactive)",
    tooltip=TT["falling_out"],
    value_class="danger",
    spark_color="#F26D6D",
)

# -- Supporting KPI Cards --
render_kpi_row([
    kpi_spec_count("FALLING OUT", summary["Falling Out"]["count"], value_class="danger",
                   sub_text=f"{format_php(summary['Falling Out']['revenue'])} at risk",
                   tooltip=TT["falling_out"],
                   card_class="segment-falling-out"),
    kpi_spec_count("AT RISK", summary["At Risk"]["count"], value_class="warning",
                   sub_text=f"{format_php(summary['At Risk']['revenue'])} at risk",
                   tooltip=TT["at_risk"],
                   card_class="segment-at-risk"),
    kpi_spec_count("HIGH POTENTIAL", summary["High Potential"]["count"],
                   sub_text=f"{format_php(summary['High Potential']['revenue'])} revenue",
                   tooltip=TT["high_potential"],
                   card_class="segment-high-potential"),
    kpi_spec_count("TOTAL CUSTOMERS", summary["total_customers"],
                   sub_text=f"{format_php(summary['total_revenue'])} total revenue",
                   tooltip=TT["total_customers"]),
])

# -- Insight Banner --
fo_count = summary["Falling Out"]["count"]
fo_rev = summary["Falling Out"]["revenue"]
total = summary["total_customers"]
fo_pct = (fo_count / total * 100) if total > 0 else 0

if fo_pct > 40:
    insight_card(
        f"<strong>{fo_pct:.0f}%</strong> of customers ({fo_count}) are Falling Out with "
        f"<strong>{format_php(fo_rev)}</strong> revenue at risk. Prioritize re-engagement.",
        "warning")
else:
    insight_card(
        f"Customer health is stable. <strong>{summary['High Potential']['count']}</strong> "
        f"active customers generating <strong>{format_php(summary['High Potential']['revenue'])}</strong>.",
        "info")

# -- Charts Row --
st.markdown('<div class="section-gap"></div>', unsafe_allow_html=True)

chart_col1, chart_col2 = st.columns(2)

with chart_col1:
    with st.container(border=True):
        section_card_header("Segment Distribution", "Customer count by segment", tooltip=TT["segment_distribution"])
        seg_labels = []
        seg_values = []
        seg_colors = []
        for seg in RECON_SEGMENT_ORDER:
            seg_labels.append(seg)
            seg_values.append(summary[seg]["count"])
            seg_colors.append(RECON_COLORS[seg])
        fig = donut_chart(
            seg_labels, seg_values, colors=seg_colors,
            center_text=str(total))
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

with chart_col2:
    with st.container(border=True):
        section_card_header("Segment Revenue", "Revenue at risk by segment", tooltip=TT["segment_revenue"])
        rev_data = pd.DataFrame([
            {"Segment": seg, "Revenue": summary[seg]["revenue"]}
            for seg in RECON_SEGMENT_ORDER
        ])
        fig = bar_chart(
            rev_data, x="Segment", y="Revenue",
            color="Segment", color_map=RECON_COLORS, height=300,
            y_title="Revenue (PHP)", x_title="Segment")
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

# -- Filters + Search --
st.markdown('<div class="section-gap"></div>', unsafe_allow_html=True)
section_header("Customer List")

fc1, fc2, fc3, fc4 = st.columns([3, 1.5, 1.5, 1.5])
with fc1:
    search = st.text_input("Search Customer", placeholder="Type customer name...", key="recon_search", label_visibility="collapsed")
with fc2:
    seg_filter = st.selectbox("Segment", ["All"] + RECON_SEGMENT_ORDER, key="recon_segment")
with fc3:
    sort_options = {"Priority Score": "priority_score", "Revenue": "total_revenue",
                    "Days Inactive": "days_inactive", "Customer Name": "CLIENT"}
    sort_label = st.selectbox("Sort By", list(sort_options.keys()), key="recon_sort")
with fc4:
    sort_dir = st.selectbox("Order", ["Desc", "Asc"], key="recon_dir")

# Apply table filters
display_df = cust_df.copy()
if search:
    display_df = display_df[display_df["CLIENT"].str.contains(search, case=False, na=False)]
if seg_filter != "All":
    display_df = display_df[display_df["segment"] == seg_filter]

sort_col = sort_options[sort_label]
display_df = display_df.sort_values(sort_col, ascending=(sort_dir == "Asc")).reset_index(drop=True)

# -- CSV Export --
csv_data = display_df[["CLIENT", "segment", "priority_score", "total_revenue", "days_inactive",
                        "tx_count", "total_qty", "top_products", "area_group", "sales_rep"]].copy()
csv_data.columns = ["Customer", "Segment", "Priority", "Revenue", "Days Inactive",
                     "Orders", "Qty (L/KG)", "Top Products", "Area", "Sales Rep"]
st.download_button(
    "Download CSV",
    csv_data.to_csv(index=False),
    file_name="texicon_reconnection_customers.csv",
    mime="text/csv")

# -- Customer Table --
BADGE_MAP = {"Falling Out": "red", "At Risk": "amber", "High Potential": "green"}

page_size = 50
shown = display_df.head(page_size)

if shown.empty:
    st.info("No customers match the current filters.")
else:
    rows = []
    row_classes = []
    for i, (_, r) in enumerate(shown.iterrows()):
        seg_badge = badge(r["segment"], BADGE_MAP.get(r["segment"], "green"))
        tp = str(r.get("top_products", "") or "")
        tp_display = (tp[:40] + "...") if len(tp) > 40 else tp
        rows.append([
            str(i + 1),
            f'{r["priority_score"]:.0f}',
            seg_badge,
            str(r["CLIENT"])[:30],
            format_php(r["total_revenue"]),
            f'{int(r["days_inactive"])}d',
            str(int(r["tx_count"])),
            tp_display,
            str(r.get("area_group", "")),
            str(r.get("sales_rep", ""))[:20],
        ])
        if r["segment"] == "Falling Out":
            row_classes.append("row-danger")
        elif r["segment"] == "At Risk":
            row_classes.append("row-warning")
        else:
            row_classes.append("")

    styled_table(
        ["#", "Priority", "Segment", "Customer", "Revenue", "Days Inactive",
         "Orders", "Top Products", "Area", "Sales Rep"],
        rows,
        green_cols=[4],
        row_classes=row_classes,
        num_cols=[0, 1, 4, 5, 6])

    if len(display_df) > page_size:
        st.caption(f"Showing top {page_size} of {len(display_df)} customers.")

# -- Customer Detail Expanders --
st.markdown('<div class="section-gap"></div>', unsafe_allow_html=True)
section_header("Customer Details")
st.caption("Expand a customer to view transaction history and top products.")

detail_df = shown.head(20)
for _, row in detail_df.iterrows():
    client = row["CLIENT"]
    seg_label = row["segment"]
    with st.expander(f"{client}  |  {seg_label}  |  {format_php(row['total_revenue'])}"):
        mc1, mc2, mc3, mc4 = st.columns(4)
        with mc1:
            mini_card("Total Revenue", format_php(row["total_revenue"]))
        with mc2:
            mini_card("Quantity (L/KG)", f'{row["total_qty"]:,.0f}')
        with mc3:
            mini_card("Orders", str(int(row["tx_count"])))
        with mc4:
            mini_card("Days Inactive", f'{int(row["days_inactive"])}')

        tx = get_customer_transactions(sr_f, client)
        if tx.empty:
            st.caption("No transactions found.")
        else:
            tx_rows = []
            for _, t in tx.head(20).iterrows():
                tx_rows.append([
                    t["DATE"].strftime("%b %d, %Y") if pd.notna(t.get("DATE")) else "",
                    str(t.get("INV NO.", "")),
                    str(t.get("ITEM", ""))[:30],
                    str(t.get("PRODUCT CATEGORY", "")),
                    f'{t.get("QTY IN L/KG", 0):,.1f}',
                    format_php(t.get("NET SALES", 0)),
                    str(t.get("TERMS", "")),
                ])
            styled_table(
                ["Date", "Invoice", "Item", "Category", "Qty (L/KG)", "Net Sales", "Terms"],
                tx_rows,
                green_cols=[5],
                num_cols=[4, 5])
            if len(tx) > 20:
                st.caption(f"Showing 20 of {len(tx)} transactions.")

# -- Additional Analysis --
st.markdown('<div class="section-gap"></div>', unsafe_allow_html=True)

col_a1, col_a2 = st.columns(2)

with col_a1:
    with st.container(border=True):
        section_card_header("Segments by Area", "Geographic distribution of customer health", tooltip=TT["segments_by_area"])
        if "area_group" in cust_df.columns:
            area_seg = cust_df.groupby(["area_group", "segment"]).size().reset_index(name="count")
            if not area_seg.empty:
                fig = stacked_bar(
                    area_seg, x="area_group", y="count", color="segment",
                    color_map=RECON_COLORS, height=300,
                    x_title="Area", y_title="Customers", y_currency=False)
                fig.update_traces(hovertemplate="<b>%{x}</b><br>%{fullData.name}: %{y} customers<extra></extra>")
                st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

with col_a2:
    with st.container(border=True):
        section_card_header("Falling Out by Sales Rep", "Top 10 reps with inactive customers", tooltip=TT["falling_out_by_rep"])
        if "sales_rep" in cust_df.columns:
            fo_by_rep = (
                cust_df[cust_df["segment"] == "Falling Out"]
                .groupby("sales_rep")
                .agg(count=("CLIENT", "size"), revenue=("total_revenue", "sum"))
                .nlargest(10, "count")
                .sort_values("count", ascending=True)
                .reset_index()
            )
            if not fo_by_rep.empty:
                fig = horizontal_bar(fo_by_rep, x="count", y="sales_rep",
                                     x_title="Falling-Out Customers", x_currency=False)
                fig.update_traces(hovertemplate="<b>%{y}</b><br>%{x} customers<extra></extra>")
                st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

scroll_to_top_button()
