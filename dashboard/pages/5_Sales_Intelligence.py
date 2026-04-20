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

require_role(allowed=["owner", "sales"])

from data.loader import load_sales_report, load_sales_order, load_delivery_report, get_data_freshness
from data.transformer import transform_sales_report, transform_sales_order, transform_delivery_report
from data.tooltips import INTEL as TT
from data.risk_engine import compute_global_risks
from components.filters import render_top_filters, apply_filters_sr
from components.drawers import (
    kpi_card, mini_card, compare_card, section_header, insight_card,
    styled_table, top_bar, section_card_header, render_nav, badge,
    empty_state, scroll_to_top_button, global_alert_strip, render_breadcrumb,
    hero_kpi, section_divider)
from components.charts import add_target_line
from data.constants import KPI_TARGETS
from components.charts import (
    bar_chart, horizontal_bar, donut_chart, line_bar_combo, area_chart)
from components.formatting import format_php, format_pct, format_number
from data.constants import CHART_COLORS
from data.analytics import (
    compute_q1_comparison, compute_item_pairings,
    compute_customer_habits, compute_margin_analysis,
    compute_daily_breakdown, build_kpi_trends)
from components.kpi_cards import (
    render_kpi_row, kpi_spec_money, kpi_spec_pct, kpi_spec_count)

# --- Load & Transform ---
sr_raw = load_sales_report()
sr = transform_sales_report(sr_raw)
so = transform_sales_order(load_sales_order())
dr = transform_delivery_report(load_delivery_report())

_role = current_role()
if _role == "owner":
    _risks = compute_global_risks(sr, so, dr)
else:
    _risks = []

render_nav(
    active_page="5_Sales_Intelligence",
    risk_count=len(_risks),
    role=_role,
)

if _role == "sales":
    render_breadcrumb([("Sales Home", "0_Sales_Home"), ("Sales Intelligence", None)])
else:
    render_breadcrumb([("Executive", "app"), ("Sales Intelligence", None)])

if _risks and _role == "owner":
    global_alert_strip(_risks)

filters = render_top_filters(sr, page_key="sales_intel", expand_filters=False)
sr_f = apply_filters_sr(sr, filters)

data_end = sr_f["DATE"].max().strftime("%B %d, %Y") if ("DATE" in sr_f.columns and not sr_f.empty and pd.notna(sr_f["DATE"].max())) else "N/A"
top_bar(data_end, datetime.now().strftime("%a, %b %d, %Y  %I:%M:%S %p"), freshness_hours=get_data_freshness())
user_chip()

st.markdown('<div class="page-title">Sales Intelligence</div>', unsafe_allow_html=True)
st.markdown('<div class="page-subtitle">Deep Analytics, Patterns & Comparisons</div>', unsafe_allow_html=True)

if sr_f.empty:
    empty_state()
    st.stop()

# ============================================
# HERO: Q1 REVENUE GROWTH
# ============================================
yoy = compute_q1_comparison(sr_f)
if yoy is not None:
    _g = yoy["growth"]["net_sales"]
    _trend_series = build_kpi_trends(sr_f).get("net_sales")
    hero_kpi(
        label="Q1 REVENUE GROWTH",
        value=f"{_g:+.1f}%",
        sub_value=f"{format_php(yoy['summary_2026']['net_sales'])} Q1 '26 vs {format_php(yoy['summary_2025']['net_sales'])} Q1 '25",
        trend=_trend_series,
        delta=_g,
        delta_label=f"{format_php(yoy['summary_2026']['net_sales'] - yoy['summary_2025']['net_sales'])} absolute change",
        tooltip=TT["revenue_growth"],
        value_class="" if _g >= 0 else "danger",
    )

# ============================================
# SECTION 1: Q1 YEAR-OVER-YEAR COMPARISON
# ============================================
section_divider("Year-over-Year Comparison", eyebrow="SECTION 1 · Q1 COMPARISON")

if yoy is None:
    st.info("Not enough Q1 data for comparison. Need both Q1 2025 and Q1 2026.")
else:
    s25 = yoy["summary_2025"]
    s26 = yoy["summary_2026"]
    gr = yoy["growth"]

    # KPI Row
    g = gr["net_sales"]; cg = gr["client_count"]; vg = gr["volume"]
    render_kpi_row([
        kpi_spec_money("Q1 '25 REVENUE", s25["net_sales"], value_class="neutral",
                       tooltip=TT["q1_revenue_25"]),
        kpi_spec_money("Q1 '26 REVENUE", s26["net_sales"], tooltip=TT["q1_revenue_26"]),
        kpi_spec_pct("REV GROWTH", g, value_class="" if g > 0 else "danger",
                     sub_text=f"{format_php(s26['net_sales'] - s25['net_sales'])} change",
                     tooltip=TT["revenue_growth"]),
        kpi_spec_pct("CLIENT GROWTH", cg, value_class="" if cg >= 0 else "danger",
                     sub_text=f"{s25['client_count']} \u2192 {s26['client_count']}",
                     tooltip=TT["client_growth"]),
        kpi_spec_pct("VOLUME GROWTH", vg, value_class="" if vg >= 0 else "danger",
                     sub_text=f"{s25['volume']:,.0f} \u2192 {s26['volume']:,.0f} L/KG",
                     tooltip=TT["volume_growth"]),
    ])

    # Monthly side-by-side chart
    st.markdown('<div class="section-gap"></div>', unsafe_allow_html=True)
    m_col1, m_col2 = st.columns([2, 1])

    with m_col1:
        with st.container(border=True):
            section_card_header("Monthly Revenue Comparison", "Q1 2025 vs Q1 2026 by month", tooltip=TT["monthly_comparison"])
            mdf = yoy["monthly"]
            if not mdf.empty:
                mdf = mdf.sort_values(["Year", "Month_Num"]).reset_index(drop=True)
                mdf["Year"] = mdf["Year"].astype(str)
                fig = bar_chart(mdf, x="Month_Label", y="Net Sales", color="Year",
                                barmode="group", height=300,
                                x_title="Month", y_title="Revenue (PHP)",
                                category_orders={"Month_Label": ["Jan", "Feb", "Mar"]})
                st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    with m_col2:
        # New / Lost clients
        with st.container(border=True):
            section_card_header("Client Migration", "New vs lost customers in Q1 2026")
            mc1, mc2, mc3 = st.columns(3)
            with mc1:
                mini_card("New", str(yoy["new_client_count"]))
            with mc2:
                mini_card("Lost", str(yoy["lost_client_count"]))
            with mc3:
                net_change = yoy["new_client_count"] - yoy["lost_client_count"]
                mini_card("Net", f"{'+' if net_change > 0 else ''}{net_change}")

            # Compare cards
            st.markdown("")
            compare_card("Avg Transaction", format_php(s26["avg_transaction"]),
                         format_php(s25["avg_transaction"]),
                         format_pct(gr["avg_transaction"]),
                         gr["avg_transaction"] >= 0)
            st.markdown("")
            compare_card("Items Sold", str(s26["item_count"]),
                         str(s25["item_count"]),
                         f"{s26['item_count'] - s25['item_count']:+d}",
                         s26["item_count"] >= s25["item_count"])

    # Top Gainers & Decliners
    st.markdown('<div class="section-gap"></div>', unsafe_allow_html=True)
    g_col1, g_col2 = st.columns(2)

    item_changes = yoy["item_changes"]
    if not item_changes.empty:
        with g_col1:
            with st.container(border=True):
                section_card_header("Top 10 Revenue Gainers", "Items with highest Q1 revenue growth", tooltip=TT["top_gainers"])
                gainers = item_changes.head(10)
                rows = []
                for _, r in gainers.iterrows():
                    rows.append([
                        str(r["ITEM"])[:30],
                        format_php(r.get("Q1_2025", 0)),
                        format_php(r.get("Q1_2026", 0)),
                        format_php(r["Change"]),
                        f"{r['Change_Pct']:+.1f}%",
                    ])
                styled_table(["Item", "Q1 '25", "Q1 '26", "Change", "%"], rows,
                             green_cols=[3], num_cols=[1, 2, 3, 4])

        with g_col2:
            with st.container(border=True):
                section_card_header("Top 10 Revenue Decliners", "Items with highest Q1 revenue decline", tooltip=TT["top_decliners"])
                losers = item_changes.tail(10).iloc[::-1]
                rows = []
                for _, r in losers.iterrows():
                    rows.append([
                        str(r["ITEM"])[:30],
                        format_php(r.get("Q1_2025", 0)),
                        format_php(r.get("Q1_2026", 0)),
                        format_php(r["Change"]),
                        f"{r['Change_Pct']:+.1f}%",
                    ])
                styled_table(["Item", "Q1 '25", "Q1 '26", "Change", "%"], rows,
                             red_cols=[3, 4], num_cols=[1, 2, 3, 4])

# ============================================
# SECTION 2: PRODUCT BUNDLES & PAIRINGS
# ============================================
section_divider("Product Bundles & Pairings", eyebrow="SECTION 2 · CROSS-SELL")

pairings = compute_item_pairings(sr_f)

if pairings is None:
    st.info("Not enough multi-item invoice data for pairing analysis.")
else:
    stats = pairings["stats"]
    insight_card(
        f"<strong>{stats['multi_item_pct']:.1f}%</strong> of invoices contain multiple products "
        f"({stats['multi_item_invoices']:,} of {stats['total_invoices']:,}). "
        f"Found <strong>{stats['unique_pairs']}</strong> unique item pairings.",
        "info")

    p_col1, p_col2 = st.columns([1.5, 1])

    with p_col1:
        with st.container(border=True):
            section_card_header("Top 15 Co-Purchased Pairs", "Items frequently bought together")
            pdf = pairings["pairings"].head(15)
            rows = []
            for _, r in pdf.iterrows():
                rows.append([
                    str(r["item_a"])[:22],
                    str(r["item_b"])[:22],
                    str(int(r["count"])),
                    f"{r['support_pct']:.1f}%",
                    f"{r['confidence_a_to_b']:.0f}%",
                    format_php(r["combined_revenue"]),
                ])
            styled_table(["Item A", "Item B", "Count", "Support", "Conf A\u2192B", "Revenue"],
                         rows, green_cols=[5], num_cols=[2, 3, 4, 5])

    with p_col2:
        with st.container(border=True):
            section_card_header("Top Pairs by Frequency", "Most common product combinations")
            top10 = pairings["pairings"].head(10).copy()
            top10["Pair"] = top10["item_a"].str[:15] + " + " + top10["item_b"].str[:15]
            top10 = top10.sort_values("count", ascending=True)
            fig = horizontal_bar(top10, x="count", y="Pair",
                                 x_title="Co-Purchases", x_currency=False)
            fig.update_traces(hovertemplate="<b>%{y}</b><br>%{x} co-purchases<extra></extra>")
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    # Bundle suggestions
    bundles = pairings["bundle_suggestions"]
    if not bundles.empty:
        st.markdown('<div class="section-gap"></div>', unsafe_allow_html=True)
        with st.container(border=True):
            section_card_header("Bundle Revenue Opportunities", "Top pairings by combined revenue potential")
            rows = []
            for i, (_, r) in enumerate(bundles.iterrows()):
                rows.append([
                    str(i + 1),
                    str(r["item_a"])[:25],
                    str(r["item_b"])[:25],
                    str(int(r["count"])),
                    format_php(r["combined_revenue"]),
                    f"{r['support_pct']:.1f}%",
                ])
            styled_table(["#", "Product A", "Product B", "Co-Purchases", "Combined Revenue", "Support"],
                         rows, green_cols=[4], num_cols=[0, 3, 4, 5])

# ============================================
# SECTION 3: CUSTOMER BEHAVIOR PATTERNS
# ============================================
section_divider("Customer Behavior Patterns", eyebrow="SECTION 3 · HABITS")

habits = compute_customer_habits(sr_f)

if habits is None:
    st.info("Not enough data for customer behavior analysis.")
else:
    bs = habits["basket_stats"]
    lifecycle = habits["lifecycle"]
    avg_ov = lifecycle["avg_order_value"].mean() if "avg_order_value" in lifecycle.columns else 0
    avg_freq = lifecycle["order_count"].mean() if "order_count" in lifecycle.columns else 0

    kpi_cols = st.columns(4)
    with kpi_cols[0]:
        kpi_card("AVG BASKET SIZE", f"{bs['mean']} items",
                 sub_text=f"Median: {bs['median']} items",
                 tooltip=TT["basket_size"])
    with kpi_cols[1]:
        kpi_card("AVG PURCHASE FREQ", f"{avg_freq:.1f} orders",
                 sub_text="Per customer in period",
                 tooltip=TT["purchase_freq"])
    with kpi_cols[2]:
        kpi_card("AVG ORDER VALUE", format_php(avg_ov),
                 sub_text="Net revenue per invoice",
                 tooltip=TT["avg_order_value"])
    with kpi_cols[3]:
        kpi_card("SINGLE-ITEM INVOICES", format_pct(bs["single_item_pct"]),
                 value_class="warning" if bs["single_item_pct"] > 50 else "",
                 sub_text="Cross-sell opportunity",
                 tooltip=TT["single_item_pct"])

    # Segment donut + frequency distribution
    st.markdown('<div class="section-gap"></div>', unsafe_allow_html=True)
    h_col1, h_col2 = st.columns(2)

    with h_col1:
        with st.container(border=True):
            section_card_header("Customer Segments", "Behavioral segmentation by value & frequency", tooltip=TT["customer_segments"])
            seg = habits["segment_summary"]
            if not seg.empty:
                seg_colors = {
                    "Power Buyer": "#00D68F",
                    "Bulk Buyer":  "#E2B04A",
                    "Regular":     "#6BA8FF",
                    "Light Buyer": "#5A6069",
                }
                colors = [seg_colors.get(s, "#5A6069") for s in seg["segment"]]
                fig = donut_chart(
                    seg["segment"].tolist(), seg["count"].tolist(),
                    colors=colors,
                    center_text=f"{seg['count'].sum()}\ncustomers")
                st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

                # Segment detail
                rows = []
                for _, r in seg.iterrows():
                    rows.append([
                        badge(r["segment"], "green" if r["segment"] == "Power Buyer" else "amber" if r["segment"] == "Bulk Buyer" else "red" if r["segment"] == "Light Buyer" else "green"),
                        str(int(r["count"])),
                        format_php(r["revenue"]),
                        format_php(r["avg_revenue"]),
                    ])
                styled_table(["Segment", "Customers", "Revenue", "Avg Revenue"], rows,
                             green_cols=[2], num_cols=[1, 2, 3])

    with h_col2:
        with st.container(border=True):
            section_card_header("Purchase Frequency Distribution", "How often customers buy", tooltip=TT["freq_distribution"])
            freq_df = habits["frequency_dist"]
            if not freq_df.empty:
                fig = bar_chart(freq_df, x="Frequency", y="Customers", height=280,
                                x_title="Orders per Customer", y_title="Customers", y_currency=False)
                fig.update_traces(hovertemplate="<b>%{x}</b><br>%{y} customers<extra></extra>")
                st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    # Day-of-week + basket size
    st.markdown('<div class="section-gap"></div>', unsafe_allow_html=True)
    h_col3, h_col4 = st.columns(2)

    with h_col3:
        with st.container(border=True):
            section_card_header("Purchase Day Patterns", "Revenue by day of week", tooltip=TT["dow_patterns"])
            dow = habits["timing_dow"]
            if not dow.empty:
                fig = bar_chart(dow, x="Day", y="Revenue", height=280,
                                x_title="Day of Week", y_title="Revenue (PHP)")
                st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    with h_col4:
        with st.container(border=True):
            section_card_header("Basket Size Distribution", "Items per invoice")
            basket_df = habits["basket_dist"]
            if not basket_df.empty:
                fig = bar_chart(basket_df, x="Basket Size", y="Invoices", height=280,
                                x_title="Basket Size", y_title="Invoices", y_currency=False)
                fig.update_traces(hovertemplate="<b>%{x}</b><br>%{y} invoices<extra></extra>")
                st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    # Top Power Buyers
    st.markdown('<div class="section-gap"></div>', unsafe_allow_html=True)
    power = habits["segments"]
    power_buyers = power[power["segment"] == "Power Buyer"].head(20)
    if not power_buyers.empty:
        with st.container(border=True):
            section_card_header("Top Power Buyers", "High-frequency, high-value customers", tooltip=TT["power_buyers"])
            rows = []
            for i, (_, r) in enumerate(power_buyers.iterrows()):
                rows.append([
                    str(i + 1),
                    str(r["CLIENT"])[:25],
                    str(int(r.get("order_count", 0))),
                    str(int(r.get("unique_items", 0))) if "unique_items" in r else "-",
                    format_php(r["total_revenue"]),
                    format_php(r["avg_order_value"]),
                    f'{int(r.get("span_days", 0))}d',
                ])
            styled_table(["#", "Customer", "Orders", "Products", "Revenue", "Avg Order", "Span"],
                         rows, green_cols=[4], num_cols=[0, 2, 3, 4, 5, 6])

if _role == "owner":
    # ============================================
    # SECTION 4: MARGIN & PRICING ANALYSIS
    # ============================================
    section_divider("Margin & Pricing Analysis (GP Proxy)", eyebrow="SECTION 4 · MARGIN")

    margins = compute_margin_analysis(sr_f)

    if margins is None:
        st.info("Not enough data for margin analysis.")
    else:
        kpi_cols = st.columns(3)
        with kpi_cols[0]:
            kpi_card("AVG DISCOUNT RATE", format_pct(margins["overall_discount"]),
                     value_class="warning" if margins["overall_discount"] > 8 else "",
                     sub_text="Across all transactions",
                     tooltip=TT["avg_discount"])
        with kpi_cols[1]:
            kpi_card("AVG UNIT NET PRICE", f"\u20B1{margins['overall_unit_price']:,.0f}/L",
                     value_class="neutral",
                     sub_text="Net revenue per L/KG",
                     tooltip=TT["avg_unit_price"])
        with kpi_cols[2]:
            risk_count = len(margins["margin_risk"]) if not margins["margin_risk"].empty else 0
            kpi_card("MARGIN RISK ITEMS", str(risk_count),
                     value_class="danger" if risk_count > 3 else "warning" if risk_count > 0 else "",
                     sub_text="Price declining or discount rising",
                     tooltip=TT["margin_risk_items"],
                     card_class="danger-glow" if risk_count > 3 else "")

        # Discount by category + top discounted clients
        st.markdown('<div class="section-gap"></div>', unsafe_allow_html=True)
        m_col1, m_col2 = st.columns(2)

        with m_col1:
            with st.container(border=True):
                section_card_header("Discount Rate by Category", "Average discount percentage", tooltip=TT["discount_by_category"])
                cat_df = margins["by_category"]
                if not cat_df.empty:
                    cat_sorted = cat_df.sort_values("avg_discount", ascending=True)
                    fig = horizontal_bar(cat_sorted, x="avg_discount", y="PRODUCT CATEGORY",
                                         x_title="Avg Discount (%)", x_currency=False)
                    fig.update_xaxes(ticksuffix="%")
                    fig.add_vline(x=KPI_TARGETS["discount_rate_max"]["value"], line_dash="dash",
                                  line_color=KPI_TARGETS["discount_rate_max"]["color"], line_width=1.5,
                                  opacity=0.7, annotation_text=KPI_TARGETS["discount_rate_max"]["label"],
                                  annotation_position="top right",
                                  annotation_font=dict(size=10, color=KPI_TARGETS["discount_rate_max"]["color"]))
                    fig.update_traces(hovertemplate="<b>%{y}</b><br>%{x:.1f}% avg discount<extra></extra>")
                    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

        with m_col2:
            with st.container(border=True):
                section_card_header("Top Discounted Clients", "Customers with highest avg discount", tooltip=TT["discount_by_client"])
                cli_df = margins["by_client"]
                if not cli_df.empty:
                    top_disc = cli_df.head(10).sort_values("avg_discount", ascending=True)
                    top_disc["CLIENT"] = top_disc["CLIENT"].str[:20]
                    fig = horizontal_bar(top_disc, x="avg_discount", y="CLIENT",
                                         color_seq=["#F26D6D"],
                                         x_title="Avg Discount (%)", x_currency=False)
                    fig.update_xaxes(ticksuffix="%")
                    fig.update_traces(hovertemplate="<b>%{y}</b><br>%{x:.1f}% avg discount<extra></extra>")
                    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

        # Price erosion table
        pe = margins["price_erosion"]
        if not pe.empty:
            st.markdown('<div class="section-gap"></div>', unsafe_allow_html=True)
            declining = pe[pe["price_change_pct"] < 0].head(15)
            if not declining.empty:
                with st.container(border=True):
                    section_card_header("Price Erosion Watch", "Items with declining unit net price Q1'25 \u2192 Q1'26", tooltip=TT["price_erosion"])
                    rows = []
                    for _, r in declining.iterrows():
                        rows.append([
                            str(r["ITEM"])[:30],
                            f"\u20B1{r['price_2025']:,.0f}",
                            f"\u20B1{r['price_2026']:,.0f}",
                            f"{r['price_change_pct']:+.1f}%",
                            format_php(r.get("revenue_2025", 0)),
                            format_php(r.get("revenue_2026", 0)),
                        ])
                    styled_table(["Item", "Price Q1'25", "Price Q1'26", "Change", "Rev Q1'25", "Rev Q1'26"],
                                 rows, red_cols=[3], num_cols=[1, 2, 3, 4, 5])

        # Margin risks
        mr = margins["margin_risk"]
        if not mr.empty:
            for _, r in mr.head(3).iterrows():
                insight_card(
                    f"<strong>{r['ITEM'][:30]}</strong>: unit price {r['price_change_pct']:+.1f}%, "
                    f"discount moved {r['discount_change']:+.1f}pp "
                    f"(Q1'25 \u20B1{r['price_2025']:,.0f}/L \u2192 Q1'26 \u20B1{r['price_2026']:,.0f}/L)",
                    "warning")

# ============================================
# SECTION 5: GRANULAR DATE BREAKDOWN
# ============================================
section_divider("Granular Date Breakdown", eyebrow="SECTION 5 · TIME PATTERNS")

daily_data = compute_daily_breakdown(sr_f)

if daily_data is None:
    st.info("No date data available for breakdown.")
else:
    peaks = daily_data["peaks"]

    # Peak mini-cards
    mc_cols = st.columns(4)
    with mc_cols[0]:
        mini_card("Best Day", f"{peaks['best_day']} \u2014 {format_php(peaks['best_day_rev'])}",
                  tooltip=TT["best_day"])
    with mc_cols[1]:
        mini_card("Worst Day", f"{peaks['worst_day']} \u2014 {format_php(peaks['worst_day_rev'])}",
                  tooltip=TT["worst_day"])
    with mc_cols[2]:
        mini_card("Avg Daily Rev", format_php(peaks["avg_daily_revenue"]),
                  tooltip=TT["avg_daily_rev"])
    with mc_cols[3]:
        mini_card("Active Days", str(peaks["total_active_days"]))

    # Daily revenue chart
    st.markdown('<div class="section-gap"></div>', unsafe_allow_html=True)
    with st.container(border=True):
        section_card_header("Daily Revenue", "Revenue per active sales day", tooltip=TT["daily_trend"])
        daily_df = daily_data["daily"]
        if not daily_df.empty and len(daily_df) > 1:
            import plotly.graph_objects as go
            from data.constants import PLOTLY_LAYOUT, TEXT_PRIMARY, TEXT_SECONDARY
            import copy

            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=daily_df["DATE"], y=daily_df["revenue"],
                mode="lines+markers",
                line=dict(color="#00D68F", width=2, shape="spline"),
                marker=dict(size=4, color="#00D68F"),
                hovertemplate="%{x|%b %d, %Y}<br>\u20B1%{y:,.0f}<extra></extra>",
                fill="tozeroy",
                fillcolor="rgba(0,214,143,0.08)"))
            layout = copy.deepcopy(PLOTLY_LAYOUT)
            layout.update(height=300)
            fig.update_layout(**layout)
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    # Day-of-week pattern + weekly bars
    st.markdown('<div class="section-gap"></div>', unsafe_allow_html=True)
    d_col1, d_col2 = st.columns(2)

    with d_col1:
        with st.container(border=True):
            section_card_header("Revenue by Day of Week", "Average daily revenue pattern", tooltip=TT["dow_patterns"])
            dow = daily_data["dow_pattern"]
            if not dow.empty:
                fig = bar_chart(dow, x="Day", y="Avg Revenue", height=280,
                                x_title="Day of Week", y_title="Avg Revenue (PHP)")
                st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    with d_col2:
        with st.container(border=True):
            section_card_header("Weekly Revenue Summary", "Aggregated by week", tooltip=TT["weekly_summary"])
            weekly = daily_data["weekly"]
            if not weekly.empty and len(weekly) > 1:
                fig = bar_chart(weekly, x="Week_Label", y="revenue", height=280,
                                x_title="Week", y_title="Revenue (PHP)")
                st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

scroll_to_top_button()
