import streamlit as st
import pandas as pd
import os

css_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "style.css")
with open(css_path) as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
st.markdown('<style>section[data-testid="stSidebar"]{display:none !important;}</style>', unsafe_allow_html=True)

from data.loader import load_sales_report
from data.transformer import transform_sales_report
from data.reconnection import build_reconnection_data, get_customer_transactions, get_segment_summary
from components.filters import render_top_filters, apply_filters_sr
from components.drawers import (
    kpi_card, section_header, insight_card, styled_table,
    badge, mini_card, top_bar, section_card_header,
)
from components.charts import donut_chart, bar_chart, horizontal_bar, stacked_bar
from components.formatting import format_php, format_number
from data.constants import RECON_COLORS, RECON_SEGMENT_ORDER
from datetime import datetime

# -- Load & Transform --
sr_raw = load_sales_report()
sr = transform_sales_report(sr_raw)

filters = render_top_filters(sr, page_key="recon")
sr_f = apply_filters_sr(sr, filters)

if sr_f.empty:
    st.warning("No data matches the current filters.")
    st.stop()

cust_df = build_reconnection_data(sr_f)

if cust_df.empty:
    st.warning("No customer data available.")
    st.stop()

data_end = sr_f["DATE"].max().strftime("%B %d, %Y") if pd.notna(sr_f["DATE"].max()) else "N/A"
top_bar(data_end, datetime.now().strftime("%a, %b %d, %Y  %I:%M:%S %p"))

st.markdown('<div class="page-title">Customer Reconnection</div>', unsafe_allow_html=True)
st.markdown('<div class="page-subtitle">Identify inactive customers and prioritize re-engagement actions</div>', unsafe_allow_html=True)

# -- KPI Cards --
summary = get_segment_summary(cust_df)

kpi_cols = st.columns(4)
with kpi_cols[0]:
    kpi_card(
        "FALLING OUT",
        format_number(summary["Falling Out"]["count"]),
        value_class="danger",
        sub_text=f"{format_php(summary['Falling Out']['revenue'])} at risk",
        icon="\U0001F6A8", icon_class="danger",
    )
with kpi_cols[1]:
    kpi_card(
        "AT RISK",
        format_number(summary["At Risk"]["count"]),
        value_class="warning",
        sub_text=f"{format_php(summary['At Risk']['revenue'])} at risk",
        icon="\u26A0", icon_class="warning",
    )
with kpi_cols[2]:
    kpi_card(
        "HIGH POTENTIAL",
        format_number(summary["High Potential"]["count"]),
        sub_text=f"{format_php(summary['High Potential']['revenue'])} revenue",
        icon="\u2B50",
    )
with kpi_cols[3]:
    kpi_card(
        "TOTAL CUSTOMERS",
        format_number(summary["total_customers"]),
        sub_text=f"{format_php(summary['total_revenue'])} total revenue",
        icon="\U0001F465",
    )

# -- Insight Banner --
fo_count = summary["Falling Out"]["count"]
fo_rev = summary["Falling Out"]["revenue"]
total = summary["total_customers"]
fo_pct = (fo_count / total * 100) if total > 0 else 0

if fo_pct > 40:
    insight_card(
        f"<strong>{fo_pct:.0f}%</strong> of customers ({fo_count}) are Falling Out with "
        f"<strong>{format_php(fo_rev)}</strong> revenue at risk. Prioritize re-engagement.",
        "warning",
    )
else:
    insight_card(
        f"Customer health is stable. <strong>{summary['High Potential']['count']}</strong> "
        f"active customers generating <strong>{format_php(summary['High Potential']['revenue'])}</strong>.",
        "info",
    )

# -- Charts Row --
st.markdown('<div class="section-gap"></div>', unsafe_allow_html=True)

chart_col1, chart_col2 = st.columns(2)

with chart_col1:
    with st.container(border=True):
        section_card_header("Segment Distribution", "Customer count by segment")
        seg_labels = []
        seg_values = []
        seg_colors = []
        for seg in RECON_SEGMENT_ORDER:
            seg_labels.append(seg)
            seg_values.append(summary[seg]["count"])
            seg_colors.append(RECON_COLORS[seg])
        fig = donut_chart(
            seg_labels, seg_values, colors=seg_colors,
            center_text=str(total),
        )
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

with chart_col2:
    with st.container(border=True):
        section_card_header("Segment Revenue", "Revenue at risk by segment")
        rev_data = pd.DataFrame([
            {"Segment": seg, "Revenue": summary[seg]["revenue"]}
            for seg in RECON_SEGMENT_ORDER
        ])
        fig = bar_chart(
            rev_data, x="Segment", y="Revenue",
            color="Segment", color_map=RECON_COLORS, height=300,
        )
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
    mime="text/csv",
)

# -- Customer Table --
BADGE_MAP = {"Falling Out": "red", "At Risk": "amber", "High Potential": "green"}

page_size = 50
shown = display_df.head(page_size)

if shown.empty:
    st.info("No customers match the current filters.")
else:
    rows = []
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

    styled_table(
        ["#", "Priority", "Segment", "Customer", "Revenue", "Days Inactive",
         "Orders", "Top Products", "Area", "Sales Rep"],
        rows,
        green_cols=[4],
    )

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
            mini_card("Total Revenue", format_php(row["total_revenue"]), icon="\U0001F4B0")
        with mc2:
            mini_card("Quantity (L/KG)", f'{row["total_qty"]:,.0f}', icon="\U0001F4E6")
        with mc3:
            mini_card("Orders", str(int(row["tx_count"])), icon="\U0001F4CB")
        with mc4:
            mini_card("Days Inactive", f'{int(row["days_inactive"])}', icon="\u23F0")

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
            )
            if len(tx) > 20:
                st.caption(f"Showing 20 of {len(tx)} transactions.")

# -- Additional Analysis --
st.markdown('<div class="section-gap"></div>', unsafe_allow_html=True)

col_a1, col_a2 = st.columns(2)

with col_a1:
    with st.container(border=True):
        section_card_header("Segments by Area", "Geographic distribution of customer health")
        if "area_group" in cust_df.columns:
            area_seg = cust_df.groupby(["area_group", "segment"]).size().reset_index(name="count")
            if not area_seg.empty:
                fig = stacked_bar(
                    area_seg, x="area_group", y="count", color="segment",
                    color_map=RECON_COLORS, height=300,
                )
                st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

with col_a2:
    with st.container(border=True):
        section_card_header("Falling Out by Sales Rep", "Top 10 reps with inactive customers")
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
                fig = horizontal_bar(fo_by_rep, x="count", y="sales_rep", height=300)
                st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
