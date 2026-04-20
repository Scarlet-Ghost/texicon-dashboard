import streamlit as st
st.set_page_config(page_title="Data Explorer — Texicon", layout="wide",
                   initial_sidebar_state="collapsed")

try:
    from components.theme import inject_css, current_theme
    from components.drawers import render_top_bar
except ModuleNotFoundError:
    from dashboard.components.theme import inject_css, current_theme
    from dashboard.components.drawers import render_top_bar

st.markdown(inject_css(current_theme()), unsafe_allow_html=True)
render_top_bar(active_page="Data")

import pandas as pd
import os
from datetime import datetime
from io import BytesIO

from components.auth import require_role, user_chip, current_role

require_role(allowed=["owner"])

from data.loader import load_sales_report, load_sales_order, load_delivery_report, load_collection_report, get_data_freshness
from data.transformer import (
    transform_sales_report, transform_sales_order,
    transform_delivery_report, transform_collection_report)
from components.drawers import (render_nav, top_bar, section_card_header,
                                scroll_to_top_button, global_alert_strip,
                                render_breadcrumb, hero_kpi)
from components.kpi_cards import (render_kpi_row, kpi_spec_money, kpi_spec_pct,
                                  kpi_spec_count)
from components.formatting import format_php, format_pct, format_number
from data.constants import PHP_SYMBOL
from data.tooltips import DATA_EXPLORER as TT
from data.risk_engine import compute_global_risks

# ============================================
# HELPERS
# ============================================

def _pagination_info(page, page_size, total):
    """Render pagination info text."""
    start = (page - 1) * page_size + 1
    end = min(page * page_size, total)
    total_pages = max(1, (total + page_size - 1) // page_size)
    st.markdown(
        f'<div class="data-pagination-info">Showing <strong>{start:,}–{end:,}</strong> '
        f'of <strong>{total:,}</strong> records  ·  Page <strong>{page}</strong> of <strong>{total_pages}</strong></div>',
        unsafe_allow_html=True)
    return total_pages

def _export_csv(df, filename):
    """Render a CSV download button for the filtered data."""
    csv_buf = BytesIO()
    csv_buf.write(b'\xef\xbb\xbf')  # UTF-8 BOM for Excel
    df.to_csv(csv_buf, index=False)
    csv_buf.seek(0)
    st.download_button(
        f"Export {len(df):,} rows as CSV",
        data=csv_buf,
        file_name=f"{filename}_{datetime.now().strftime('%Y%m%d')}.csv",
        mime="text/csv",
        use_container_width=False)

def _state_key(tab, key):
    return f"de_{tab}_{key}"

def _get_page(tab):
    return st.session_state.get(_state_key(tab, "page"), 1)

def _set_page(tab, val):
    st.session_state[_state_key(tab, "page")] = val

def _render_pagination(tab, total, page_size):
    """Render prev/next pagination controls. Returns nothing."""
    page = _get_page(tab)
    total_pages = max(1, (total + page_size - 1) // page_size)
    if page > total_pages:
        page = 1
        _set_page(tab, 1)

    _pagination_info(page, page_size, total)

    p1, p2, p_mid, p3, p4 = st.columns([0.8, 0.8, 1.4, 0.8, 0.8])
    with p1:
        if st.button("First", key=f"first_{tab}", disabled=(page <= 1), use_container_width=True):
            _set_page(tab, 1)
            st.rerun()
    with p2:
        if st.button("Prev", key=f"prev_{tab}", disabled=(page <= 1), use_container_width=True):
            _set_page(tab, page - 1)
            st.rerun()
    with p_mid:
        new_page = st.number_input("Go to page", min_value=1, max_value=total_pages,
                                    value=page, step=1, key=f"page_input_{tab}",
                                    label_visibility="collapsed")
        if new_page != page:
            _set_page(tab, new_page)
            st.rerun()
    with p3:
        if st.button("Next", key=f"next_{tab}", disabled=(page >= total_pages), use_container_width=True):
            _set_page(tab, page + 1)
            st.rerun()
    with p4:
        if st.button("Last", key=f"last_{tab}", disabled=(page >= total_pages), use_container_width=True):
            _set_page(tab, total_pages)
            st.rerun()

def _apply_search(df, search_term, cols):
    """Filter rows where any of the specified cols contain the search term."""
    if not search_term:
        return df
    term = search_term.strip().lower()
    mask = pd.Series(False, index=df.index)
    for c in cols:
        if c in df.columns:
            mask |= df[c].astype(str).str.lower().str.contains(term, na=False)
    return df[mask]

def _page_size_selector(tab):
    """Render page size selector. Returns chosen page size."""
    opts = [25, 50, 100, 250]
    key = _state_key(tab, "ps")
    idx = st.selectbox("Rows per page", opts, index=0, key=key)
    return idx

# ============================================
# LOAD & TRANSFORM DATA
# ============================================

sr_raw = load_sales_report()
sr = transform_sales_report(sr_raw)

so_raw = load_sales_order()
so = transform_sales_order(so_raw)

dr_raw = load_delivery_report()
dr = transform_delivery_report(dr_raw)

cr_raw = load_collection_report()
cr = transform_collection_report(cr_raw)

# ============================================
# PAGE LAYOUT
# ============================================

_risks = compute_global_risks(sr, so, dr)
render_breadcrumb([("Executive", "app"), ("Data Explorer", None)])
if _risks:
    global_alert_strip(_risks)

data_end = sr["DATE"].max().strftime("%B %d, %Y") if ("DATE" in sr.columns and not sr.empty and pd.notna(sr["DATE"].max())) else "N/A"
user_chip()

st.markdown('<div class="page-title">Data Explorer</div>', unsafe_allow_html=True)
st.markdown('<div class="page-subtitle">Browse, Filter & Export Raw Data</div>', unsafe_allow_html=True)

# ============================================
# TABS
# ============================================

tab_sr, tab_so, tab_dr, tab_cr = st.tabs([
    f"Sales Report  ({len(sr):,})",
    f"Sales Orders  ({len(so):,})",
    f"Delivery Report  ({len(dr):,})",
    f"Collections  ({len(cr):,})",
])

# ==================================================
# TAB 1: SALES REPORT
# ==================================================
with tab_sr:
    SR_DISPLAY_COLS = [
        "DATE", "CLIENT", "ITEM", "PRODUCT CATEGORY", "QTY IN L/KG",
        "NET SALES", "GROSS SALES", "AREA GROUP", "TERMS", "INV NO.",
        "DISCOUNT_PCT",
    ]
    sr_cols = [c for c in SR_DISPLAY_COLS if c in sr.columns]

    # --- Filters ---
    with st.container(border=True):
        section_card_header("Filters", "Search and filter the sales report data")
        fc1, fc2 = st.columns([3, 1])
        with fc1:
            sr_search = st.text_input(
                "Search by Client or Item",
                key="sr_search",
                placeholder="Type to search client or item name...")
        with fc2:
            sr_ps = _page_size_selector("sr")

        ff1, ff2, ff3, ff4 = st.columns(4)
        with ff1:
            if "PRODUCT CATEGORY" in sr.columns:
                cat_opts = ["All"] + sorted(sr["PRODUCT CATEGORY"].dropna().unique().tolist())
                sr_cat = st.selectbox("Product Category", cat_opts, key="sr_cat")
            else:
                sr_cat = "All"
        with ff2:
            if "AREA GROUP" in sr.columns:
                area_opts = ["All"] + sorted(sr["AREA GROUP"].dropna().unique().tolist())
                sr_area = st.selectbox("Area Group", area_opts, key="sr_area")
            else:
                sr_area = "All"
        with ff3:
            if "TERMS" in sr.columns:
                terms_opts = ["All"] + sorted(sr["TERMS"].dropna().unique().tolist())
                sr_terms = st.selectbox("Payment Terms", terms_opts, key="sr_terms")
            else:
                sr_terms = "All"
        with ff4:
            if "DATE" in sr.columns:
                min_d = sr["DATE"].min()
                max_d = sr["DATE"].max()
                if pd.notna(min_d) and pd.notna(max_d):
                    sr_date = st.date_input(
                        "Date Range",
                        value=(min_d.date(), max_d.date()),
                        min_value=min_d.date(),
                        max_value=max_d.date(),
                        key="sr_date_range")
                else:
                    sr_date = None
            else:
                sr_date = None

    # --- Apply Filters ---
    sr_f = sr.copy()
    sr_f = _apply_search(sr_f, sr_search, ["CLIENT", "ITEM"])
    if sr_cat != "All" and "PRODUCT CATEGORY" in sr_f.columns:
        sr_f = sr_f[sr_f["PRODUCT CATEGORY"] == sr_cat]
    if sr_area != "All" and "AREA GROUP" in sr_f.columns:
        sr_f = sr_f[sr_f["AREA GROUP"] == sr_area]
    if sr_terms != "All" and "TERMS" in sr_f.columns:
        sr_f = sr_f[sr_f["TERMS"] == sr_terms]
    if sr_date and isinstance(sr_date, tuple) and len(sr_date) == 2 and "DATE" in sr_f.columns:
        sr_f = sr_f[(sr_f["DATE"] >= pd.Timestamp(sr_date[0])) & (sr_f["DATE"] <= pd.Timestamp(sr_date[1]))]

    # Reset page when filters change
    active_filters = sum([
        sr_search != "",
        sr_cat != "All",
        sr_area != "All",
        sr_terms != "All",
    ])

    # --- Metrics ---
    net_rev = sr_f["NET SALES"].sum() if "NET SALES" in sr_f.columns else 0
    gross_rev = sr_f["GROSS SALES"].sum() if "GROSS SALES" in sr_f.columns else 0
    total_qty = sr_f["QTY IN L/KG"].sum() if "QTY IN L/KG" in sr_f.columns else 0
    avg_disc = sr_f["DISCOUNT_PCT"].mean() if "DISCOUNT_PCT" in sr_f.columns and not sr_f.empty else 0
    active_clients = sr_f["CLIENT"].nunique() if "CLIENT" in sr_f.columns else 0

    hero_kpi(
        label="SALES RECORDS",
        value=format_number(len(sr_f)),
        sub_value=f"filtered from {len(sr):,}" if len(sr_f) != len(sr) else f"{len(sr):,} rows",
        tooltip=TT["sr_total_records"],
    )
    render_kpi_row([
        kpi_spec_money("NET REVENUE", net_rev, tooltip=TT["sr_net_revenue"]),
        kpi_spec_money("GROSS REVENUE", gross_rev, tooltip=TT["sr_gross_revenue"]),
        kpi_spec_count("TOTAL QTY (L/KG)", total_qty, tooltip=TT["sr_total_qty"]),
        kpi_spec_pct("AVG DISCOUNT", avg_disc, thresholds=(8, 15), tooltip=TT["sr_avg_discount"]),
        kpi_spec_count("ACTIVE CLIENTS", active_clients, tooltip=TT["sr_active_clients"]),
    ])

    # --- Table ---
    if sr_f.empty:
        st.info("No records match the current filters.")
    else:
        # Prepare display dataframe
        sr_display = sr_f[sr_cols].copy()
        if "DATE" in sr_display.columns:
            sr_display["DATE"] = sr_display["DATE"].dt.strftime("%Y-%m-%d")
        if "DISCOUNT_PCT" in sr_display.columns:
            sr_display = sr_display.rename(columns={"DISCOUNT_PCT": "DISCOUNT %"})

        # Paginate
        page = _get_page("sr")
        total = len(sr_display)
        total_pages = max(1, (total + sr_ps - 1) // sr_ps)
        if page > total_pages:
            page = 1
            _set_page("sr", 1)
        start_idx = (page - 1) * sr_ps
        end_idx = start_idx + sr_ps
        sr_page = sr_display.iloc[start_idx:end_idx]

        col_config = {}
        for c in sr_page.columns:
            if c in ("NET SALES", "GROSS SALES"):
                col_config[c] = st.column_config.NumberColumn(c, format=f"{PHP_SYMBOL}%,.2f")
            elif c == "QTY IN L/KG":
                col_config[c] = st.column_config.NumberColumn(c, format="%,.2f")
            elif c == "DISCOUNT %":
                col_config[c] = st.column_config.NumberColumn(c, format="%.1f%%")

        st.dataframe(
            sr_page.reset_index(drop=True),
            use_container_width=True,
            hide_index=True,
            height=min(36 * sr_ps + 38, 950),
            column_config=col_config)

        # Pagination + Export
        ex1, ex2 = st.columns([3, 1])
        with ex1:
            _render_pagination("sr", total, sr_ps)
        with ex2:
            _export_csv(sr_f[sr_cols], "texicon_sales_report")

# ==================================================
# TAB 2: SALES ORDERS
# ==================================================
with tab_so:
    SO_DISPLAY_COLS = [
        "SO Date", "Delivery Date", "Customer Name", "Warehouse",
        "Group Name", "Ordered Qty", "Unit Price", "Booking Amount",
        "Payment Terms", "CYCLE_DAYS",
    ]
    so_cols = [c for c in SO_DISPLAY_COLS if c in so.columns]

    with st.container(border=True):
        section_card_header("Filters", "Search and filter sales order data")
        fc1, fc2 = st.columns([3, 1])
        with fc1:
            so_search = st.text_input(
                "Search by Customer",
                key="so_search",
                placeholder="Type to search customer name...")
        with fc2:
            so_ps = _page_size_selector("so")

        ff1, ff2, ff3 = st.columns(3)
        with ff1:
            if "Warehouse" in so.columns:
                wh_opts = ["All"] + sorted(so["Warehouse"].dropna().unique().tolist())
                so_wh = st.selectbox("Warehouse", wh_opts, key="so_wh")
            else:
                so_wh = "All"
        with ff2:
            if "Payment Terms" in so.columns:
                pt_opts = ["All"] + sorted(so["Payment Terms"].dropna().unique().tolist())
                so_pt = st.selectbox("Payment Terms", pt_opts, key="so_pt")
            else:
                so_pt = "All"
        with ff3:
            if "SO Date" in so.columns:
                min_d = so["SO Date"].min()
                max_d = so["SO Date"].max()
                if pd.notna(min_d) and pd.notna(max_d):
                    so_date = st.date_input(
                        "SO Date Range",
                        value=(min_d.date(), max_d.date()),
                        min_value=min_d.date(),
                        max_value=max_d.date(),
                        key="so_date_range")
                else:
                    so_date = None
            else:
                so_date = None

    # --- Apply Filters ---
    so_f = so.copy()
    so_f = _apply_search(so_f, so_search, ["Customer Name"])
    if so_wh != "All" and "Warehouse" in so_f.columns:
        so_f = so_f[so_f["Warehouse"] == so_wh]
    if so_pt != "All" and "Payment Terms" in so_f.columns:
        so_f = so_f[so_f["Payment Terms"] == so_pt]
    if so_date and isinstance(so_date, tuple) and len(so_date) == 2 and "SO Date" in so_f.columns:
        so_f = so_f[(so_f["SO Date"] >= pd.Timestamp(so_date[0])) & (so_f["SO Date"] <= pd.Timestamp(so_date[1]))]

    # --- Metrics ---
    total_booking = so_f["Booking Amount"].sum() if "Booking Amount" in so_f.columns else 0
    avg_unit = so_f["Unit Price"].mean() if "Unit Price" in so_f.columns and not so_f.empty else 0
    total_qty_so = so_f["Ordered Qty"].sum() if "Ordered Qty" in so_f.columns else 0
    avg_cycle = so_f["CYCLE_DAYS"].mean() if "CYCLE_DAYS" in so_f.columns and not so_f.empty else 0
    unique_cust = so_f["Customer Name"].nunique() if "Customer Name" in so_f.columns else 0

    hero_kpi(
        label="SALES ORDERS",
        value=format_number(len(so_f)),
        sub_value=f"filtered from {len(so):,}" if len(so_f) != len(so) else f"{len(so):,} rows",
        tooltip=TT["so_total_orders"],
    )
    render_kpi_row([
        kpi_spec_money("TOTAL BOOKING", total_booking, tooltip=TT["so_total_booking"]),
        kpi_spec_count("TOTAL QTY ORDERED", total_qty_so, tooltip=TT["so_total_qty"]),
        kpi_spec_money("AVG UNIT PRICE", avg_unit, tooltip=TT["so_avg_unit_price"]),
        {"label": "AVG CYCLE DAYS", "value": f"{avg_cycle:.1f} days",
         "value_class": "warning" if avg_cycle > 7 else "neutral",
         "tooltip": TT["so_avg_cycle"]},
        kpi_spec_count("UNIQUE CUSTOMERS", unique_cust, tooltip=TT["so_unique_customers"]),
    ])

    if so_f.empty:
        st.info("No records match the current filters.")
    else:
        so_display = so_f[so_cols].copy()
        if "SO Date" in so_display.columns:
            so_display["SO Date"] = so_display["SO Date"].dt.strftime("%Y-%m-%d")
        if "Delivery Date" in so_display.columns:
            so_display["Delivery Date"] = so_display["Delivery Date"].dt.strftime("%Y-%m-%d")

        page = _get_page("so")
        total = len(so_display)
        total_pages = max(1, (total + so_ps - 1) // so_ps)
        if page > total_pages:
            page = 1
            _set_page("so", 1)
        start_idx = (page - 1) * so_ps
        end_idx = start_idx + so_ps
        so_page = so_display.iloc[start_idx:end_idx]

        col_config = {}
        for c in so_page.columns:
            if c in ("Booking Amount", "Unit Price"):
                col_config[c] = st.column_config.NumberColumn(c, format=f"{PHP_SYMBOL}%,.2f")
            elif c == "Ordered Qty":
                col_config[c] = st.column_config.NumberColumn(c, format="%,.2f")
            elif c == "CYCLE_DAYS":
                col_config[c] = st.column_config.NumberColumn("Cycle Days", format="%d")

        st.dataframe(
            so_page.reset_index(drop=True),
            use_container_width=True,
            hide_index=True,
            height=min(36 * so_ps + 38, 950),
            column_config=col_config)

        ex1, ex2 = st.columns([3, 1])
        with ex1:
            _render_pagination("so", total, so_ps)
        with ex2:
            _export_csv(so_f[so_cols], "texicon_sales_orders")

# ==================================================
# TAB 3: DELIVERY REPORT
# ==================================================
with tab_dr:
    DR_DISPLAY_COLS = [
        "Delivery Date", "Customer", "Warehouse",
        "Delivered Qty", "Unit Price (VAT Incl)", "Delivered Amount", "DEL_DOW",
    ]
    dr_cols = [c for c in DR_DISPLAY_COLS if c in dr.columns]

    with st.container(border=True):
        section_card_header("Filters", "Search and filter delivery data")
        fc1, fc2 = st.columns([3, 1])
        with fc1:
            dr_search = st.text_input(
                "Search by Customer",
                key="dr_search",
                placeholder="Type to search customer name...")
        with fc2:
            dr_ps = _page_size_selector("dr")

        ff1, ff2 = st.columns(2)
        with ff1:
            if "Warehouse" in dr.columns:
                wh_opts = ["All"] + sorted(dr["Warehouse"].dropna().unique().tolist())
                dr_wh = st.selectbox("Warehouse", wh_opts, key="dr_wh")
            else:
                dr_wh = "All"
        with ff2:
            if "Delivery Date" in dr.columns:
                min_d = dr["Delivery Date"].min()
                max_d = dr["Delivery Date"].max()
                if pd.notna(min_d) and pd.notna(max_d):
                    dr_date = st.date_input(
                        "Delivery Date Range",
                        value=(min_d.date(), max_d.date()),
                        min_value=min_d.date(),
                        max_value=max_d.date(),
                        key="dr_date_range")
                else:
                    dr_date = None
            else:
                dr_date = None

    # --- Apply Filters ---
    dr_f = dr.copy()
    dr_f = _apply_search(dr_f, dr_search, ["Customer"])
    if dr_wh != "All" and "Warehouse" in dr_f.columns:
        dr_f = dr_f[dr_f["Warehouse"] == dr_wh]
    if dr_date and isinstance(dr_date, tuple) and len(dr_date) == 2 and "Delivery Date" in dr_f.columns:
        dr_f = dr_f[(dr_f["Delivery Date"] >= pd.Timestamp(dr_date[0])) & (dr_f["Delivery Date"] <= pd.Timestamp(dr_date[1]))]

    # --- Metrics ---
    total_del_qty = dr_f["Delivered Qty"].sum() if "Delivered Qty" in dr_f.columns else 0
    total_del_amt = dr_f["Delivered Amount"].sum() if "Delivered Amount" in dr_f.columns else 0
    avg_del_price = dr_f["Unit Price (VAT Incl)"].mean() if "Unit Price (VAT Incl)" in dr_f.columns and not dr_f.empty else 0
    unique_wh = dr_f["Warehouse"].nunique() if "Warehouse" in dr_f.columns else 0

    hero_kpi(
        label="DELIVERIES",
        value=format_number(len(dr_f)),
        sub_value=f"filtered from {len(dr):,}" if len(dr_f) != len(dr) else f"{len(dr):,} rows",
        tooltip=TT["dr_total_deliveries"],
    )
    render_kpi_row([
        kpi_spec_count("TOTAL QTY DELIVERED", total_del_qty, tooltip=TT["dr_total_qty"]),
        kpi_spec_money("DELIVERED AMOUNT", total_del_amt, tooltip=TT["dr_total_amount"]),
        kpi_spec_money("AVG UNIT PRICE (VAT)", avg_del_price, tooltip=TT["dr_avg_price"]),
        kpi_spec_count("ACTIVE WAREHOUSES", unique_wh, tooltip=TT["dr_active_warehouses"]),
    ])

    if dr_f.empty:
        st.info("No records match the current filters.")
    else:
        dr_display = dr_f[dr_cols].copy()
        if "Delivery Date" in dr_display.columns:
            dr_display["Delivery Date"] = dr_display["Delivery Date"].dt.strftime("%Y-%m-%d")

        page = _get_page("dr")
        total = len(dr_display)
        total_pages = max(1, (total + dr_ps - 1) // dr_ps)
        if page > total_pages:
            page = 1
            _set_page("dr", 1)
        start_idx = (page - 1) * dr_ps
        end_idx = start_idx + dr_ps
        dr_page = dr_display.iloc[start_idx:end_idx]

        col_config = {}
        for c in dr_page.columns:
            if c in ("Unit Price (VAT Incl)", "Delivered Amount"):
                col_config[c] = st.column_config.NumberColumn(c, format=f"{PHP_SYMBOL}%,.2f")
            elif c == "Delivered Qty":
                col_config[c] = st.column_config.NumberColumn(c, format="%,.2f")

        st.dataframe(
            dr_page.reset_index(drop=True),
            use_container_width=True,
            hide_index=True,
            height=min(36 * dr_ps + 38, 950),
            column_config=col_config)

        ex1, ex2 = st.columns([3, 1])
        with ex1:
            _render_pagination("dr", total, dr_ps)
        with ex2:
            _export_csv(dr_f[dr_cols], "texicon_delivery_report")

# ==================================================
# TAB 4: COLLECTION REPORT
# ==================================================
with tab_cr:
    cr_cols = [c for c in cr.columns if not c.startswith("Unnamed")]

    with st.container(border=True):
        section_card_header("Filters", "Search and filter collection data")
        fc1, fc2 = st.columns([3, 1])
        with fc1:
            cust_cols = [c for c in cr.columns if "CUSTOMER" in c.upper()]
            cr_search = st.text_input(
                "Search by Customer",
                key="cr_search",
                placeholder="Type to search customer name...")
        with fc2:
            cr_ps = _page_size_selector("cr")

        if "COLLECTION_DATE" in cr.columns:
            min_d = cr["COLLECTION_DATE"].min()
            max_d = cr["COLLECTION_DATE"].max()
            if pd.notna(min_d) and pd.notna(max_d):
                cr_date = st.date_input(
                    "Collection Date Range",
                    value=(min_d.date(), max_d.date()),
                    min_value=min_d.date(),
                    max_value=max_d.date(),
                    key="cr_date_range")
            else:
                cr_date = None
        else:
            cr_date = None

    # --- Apply Filters ---
    cr_f = cr.copy()
    if cr_search and cust_cols:
        cr_f = _apply_search(cr_f, cr_search, cust_cols)
    if cr_date and isinstance(cr_date, tuple) and len(cr_date) == 2 and "COLLECTION_DATE" in cr_f.columns:
        cr_f = cr_f[(cr_f["COLLECTION_DATE"] >= pd.Timestamp(cr_date[0])) & (cr_f["COLLECTION_DATE"] <= pd.Timestamp(cr_date[1]))]

    # --- Metrics ---
    amount_cols = [c for c in cr_f.columns if any(kw in c.upper() for kw in ["AMOUNT", "TOTAL"]) and "EWT" not in c.upper()]
    total_collected = cr_f[amount_cols[0]].sum() if amount_cols else 0
    unique_cust_cr = cr_f[cust_cols[0]].nunique() if cust_cols else 0

    hero_kpi(
        label="COLLECTIONS",
        value=format_number(len(cr_f)),
        sub_value=f"filtered from {len(cr):,}" if len(cr_f) != len(cr) else f"{len(cr):,} rows",
        tooltip=TT["cr_total_records"],
    )
    render_kpi_row([
        kpi_spec_money("TOTAL COLLECTED", total_collected, tooltip=TT["cr_total_collected"]),
        kpi_spec_count("UNIQUE CUSTOMERS", unique_cust_cr, tooltip=TT["cr_unique_customers"]),
    ])

    if cr_f.empty:
        st.info("No records match the current filters.")
    else:
        cr_display = cr_f[cr_cols].copy()

        # Format date columns
        for c in cr_display.columns:
            if pd.api.types.is_datetime64_any_dtype(cr_display[c]):
                cr_display[c] = cr_display[c].dt.strftime("%Y-%m-%d")

        page = _get_page("cr")
        total = len(cr_display)
        total_pages = max(1, (total + cr_ps - 1) // cr_ps)
        if page > total_pages:
            page = 1
            _set_page("cr", 1)
        start_idx = (page - 1) * cr_ps
        end_idx = start_idx + cr_ps
        cr_page = cr_display.iloc[start_idx:end_idx]

        col_config = {}
        for c in cr_page.columns:
            if any(kw in c.upper() for kw in ["AMOUNT", "TOTAL", "EWT", "DEPOSIT"]):
                try:
                    cr_page[c] = pd.to_numeric(cr_page[c], errors="coerce")
                    col_config[c] = st.column_config.NumberColumn(c, format=f"{PHP_SYMBOL}%,.2f")
                except Exception:
                    pass

        st.dataframe(
            cr_page.reset_index(drop=True),
            use_container_width=True,
            hide_index=True,
            height=min(36 * cr_ps + 38, 950),
            column_config=col_config)

        ex1, ex2 = st.columns([3, 1])
        with ex1:
            _render_pagination("cr", total, cr_ps)
        with ex2:
            _export_csv(cr_f[cr_cols], "texicon_collections")

scroll_to_top_button()
