import streamlit as st
import pandas as pd


PERIOD_RANGES = {
    "Q1 2025": ("2025-01-01", "2025-03-31"),
    "Q1 2026": ("2026-01-01", "2026-03-31"),
    "Full Period": (None, None),
}


def _init_state():
    if "period" not in st.session_state:
        st.session_state.period = "Full Period"


def render_top_filters(sr_df, so_df=None, dr_df=None, page_key="main", expand_filters=False):
    """Render filters as a top bar with period buttons + dropdown filters.
    Returns a filter dict. Sidebar is NOT used.
    expand_filters: when True, "More Filters" expander opens by default."""
    _init_state()

    # --- Period Buttons Row ---
    pcols = st.columns([1, 1, 1, 1, 1, 0.7])
    for i, label in enumerate(["Q1 2025", "Q1 2026", "Full Period", "Custom"]):
        with pcols[i]:
            btn_type = "primary" if st.session_state.period == label else "secondary"
            if st.button(label, key=f"period_{label}_{page_key}", use_container_width=True, type=btn_type):
                st.session_state.period = label
                st.rerun()

    # Reset button
    with pcols[5]:
        if st.button("Reset", key=f"reset_{page_key}", use_container_width=True, type="secondary"):
            st.session_state.period = "Full Period"
            for k in list(st.session_state.keys()):
                if any(k.startswith(p) for p in [f"area_{page_key}", f"pcat_{page_key}",
                                                   f"terms_{page_key}", f"wh_{page_key}"]):
                    del st.session_state[k]
            st.rerun()

    filters = {}

    # --- Apply Period Date Range ---
    selected = st.session_state.period
    if selected in PERIOD_RANGES:
        start, end = PERIOD_RANGES[selected]
        if start and end:
            filters["date_start"] = pd.Timestamp(start)
            filters["date_end"] = pd.Timestamp(end)

    # --- Custom Date Picker (inline) ---
    if selected == "Custom" and "DATE" in sr_df.columns:
        min_d = sr_df["DATE"].min()
        max_d = sr_df["DATE"].max()
        if pd.notna(min_d) and pd.notna(max_d):
            dc1, dc2 = st.columns(2)
            with dc1:
                start_date = st.date_input("From", value=min_d.date(), min_value=min_d.date(),
                                           max_value=max_d.date(), key=f"cust_start_{page_key}")
                filters["date_start"] = pd.Timestamp(start_date)
            with dc2:
                end_date = st.date_input("To", value=max_d.date(), min_value=min_d.date(),
                                         max_value=max_d.date(), key=f"cust_end_{page_key}")
                filters["date_end"] = pd.Timestamp(end_date)

    # --- Dropdown Filters Row (inside expander) ---
    with st.expander("More Filters", expanded=expand_filters):
        f1, f2, f3, f4 = st.columns(4)

        with f1:
            if "AREA GROUP" in sr_df.columns:
                areas = sorted(sr_df["AREA GROUP"].dropna().unique().tolist())
                sel = st.multiselect("Area Group", areas, default=[], key=f"area_{page_key}",
                                     placeholder=f"All ({len(areas)})")
                filters["area_group"] = sel if sel else areas

        with f2:
            if "PRODUCT CATEGORY" in sr_df.columns:
                cats = sorted(sr_df["PRODUCT CATEGORY"].dropna().unique().tolist())
                sel = st.multiselect("Product Category", cats, default=[], key=f"pcat_{page_key}",
                                     placeholder=f"All ({len(cats)})")
                filters["product_category"] = sel if sel else cats

        with f3:
            if "TERMS" in sr_df.columns:
                terms = sorted(sr_df["TERMS"].dropna().unique().tolist())
                sel = st.multiselect("Payment Terms", terms, default=[], key=f"terms_{page_key}",
                                     placeholder=f"All ({len(terms)})")
                filters["terms"] = sel if sel else terms

        with f4:
            wh_vals = set()
            if so_df is not None and "Warehouse" in so_df.columns:
                wh_vals.update(so_df["Warehouse"].dropna().unique())
            if dr_df is not None and "Warehouse" in dr_df.columns:
                wh_vals.update(dr_df["Warehouse"].dropna().unique())
            if wh_vals:
                wh_list = sorted(wh_vals)
                sel = st.multiselect("Warehouse", wh_list, default=[], key=f"wh_{page_key}",
                                     placeholder=f"All ({len(wh_list)})")
                filters["warehouse"] = sel if sel else wh_list

    # --- Active Filter Chips ---
    _render_active_chips(filters, sr_df, so_df, dr_df, page_key)

    return filters


def _render_active_chips(filters, sr_df, so_df, dr_df, page_key):
    """Show active filter chips for non-default filters."""
    chips = []

    if st.session_state.period != "Full Period":
        chips.append(f"Period: {st.session_state.period}")

    if "area_group" in filters and "AREA GROUP" in sr_df.columns:
        all_areas = sorted(sr_df["AREA GROUP"].dropna().unique().tolist())
        if set(filters["area_group"]) != set(all_areas):
            chips.append(f"Areas: {len(filters['area_group'])}/{len(all_areas)}")

    if "product_category" in filters and "PRODUCT CATEGORY" in sr_df.columns:
        all_cats = sorted(sr_df["PRODUCT CATEGORY"].dropna().unique().tolist())
        if set(filters["product_category"]) != set(all_cats):
            chips.append(f"Categories: {len(filters['product_category'])}/{len(all_cats)}")

    if "terms" in filters and "TERMS" in sr_df.columns:
        all_terms = sorted(sr_df["TERMS"].dropna().unique().tolist())
        if set(filters["terms"]) != set(all_terms):
            chips.append(f"Terms: {len(filters['terms'])}/{len(all_terms)}")

    if "warehouse" in filters:
        wh_vals = set()
        if so_df is not None and "Warehouse" in so_df.columns:
            wh_vals.update(so_df["Warehouse"].dropna().unique())
        if dr_df is not None and "Warehouse" in dr_df.columns:
            wh_vals.update(dr_df["Warehouse"].dropna().unique())
        if wh_vals and set(filters["warehouse"]) != wh_vals:
            chips.append(f"Warehouses: {len(filters['warehouse'])}/{len(wh_vals)}")

    if chips:
        chip_html = "".join(f'<span class="filter-chip">{c}</span>' for c in chips)
        st.markdown(f'<div class="filter-chips-row">{chip_html}</div>', unsafe_allow_html=True)


def get_active_filter_count(filters, sr_df, so_df=None):
    """Return count of active (non-default) filters for nav badge."""
    count = 0
    if st.session_state.get("period", "Full Period") != "Full Period":
        count += 1
    if "area_group" in filters and "AREA GROUP" in sr_df.columns:
        all_areas = sorted(sr_df["AREA GROUP"].dropna().unique().tolist())
        if set(filters["area_group"]) != set(all_areas):
            count += 1
    if "product_category" in filters and "PRODUCT CATEGORY" in sr_df.columns:
        all_cats = sorted(sr_df["PRODUCT CATEGORY"].dropna().unique().tolist())
        if set(filters["product_category"]) != set(all_cats):
            count += 1
    if "terms" in filters and "TERMS" in sr_df.columns:
        all_terms = sorted(sr_df["TERMS"].dropna().unique().tolist())
        if set(filters["terms"]) != set(all_terms):
            count += 1
    return count


def apply_filters_sr(df, filters):
    mask = pd.Series(True, index=df.index)
    if "date_start" in filters and "DATE" in df.columns:
        mask &= df["DATE"] >= filters["date_start"]
    if "date_end" in filters and "DATE" in df.columns:
        mask &= df["DATE"] <= filters["date_end"]
    if "area_group" in filters and "AREA GROUP" in df.columns:
        mask &= df["AREA GROUP"].isin(filters["area_group"])
    if "product_category" in filters and "PRODUCT CATEGORY" in df.columns:
        mask &= df["PRODUCT CATEGORY"].isin(filters["product_category"])
    if "terms" in filters and "TERMS" in df.columns:
        mask &= df["TERMS"].isin(filters["terms"])
    return df[mask]


def apply_filters_so(df, filters):
    mask = pd.Series(True, index=df.index)
    if "date_start" in filters and "SO Date" in df.columns:
        mask &= df["SO Date"] >= filters["date_start"]
    if "date_end" in filters and "SO Date" in df.columns:
        mask &= df["SO Date"] <= filters["date_end"]
    if "warehouse" in filters and "Warehouse" in df.columns:
        mask &= df["Warehouse"].isin(filters["warehouse"])
    if "terms" in filters and "Payment Terms" in df.columns:
        mask &= df["Payment Terms"].isin(filters["terms"])
    return df[mask]


def apply_filters_dr(df, filters):
    mask = pd.Series(True, index=df.index)
    if "date_start" in filters and "Delivery Date" in df.columns:
        mask &= df["Delivery Date"] >= filters["date_start"]
    if "date_end" in filters and "Delivery Date" in df.columns:
        mask &= df["Delivery Date"] <= filters["date_end"]
    if "warehouse" in filters and "Warehouse" in df.columns:
        mask &= df["Warehouse"].isin(filters["warehouse"])
    return df[mask]
