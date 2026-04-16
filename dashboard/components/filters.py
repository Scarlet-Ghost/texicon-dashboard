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


def render_top_filters(sr_df, so_df=None, dr_df=None, page_key="main"):
    """Render filters as a top bar with period buttons + dropdown filters.
    Returns a filter dict. Sidebar is NOT used."""
    _init_state()

    # --- Period Buttons Row ---
    pcols = st.columns([1, 1, 1, 1, 4])
    for i, label in enumerate(["Q1 2025", "Q1 2026", "Full Period", "Custom"]):
        with pcols[i]:
            btn_type = "primary" if st.session_state.period == label else "secondary"
            if st.button(label, key=f"period_{label}_{page_key}", use_container_width=True, type=btn_type):
                st.session_state.period = label
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
            dc1, dc2, _ = st.columns([1, 1, 2])
            with dc1:
                start_date = st.date_input("From", value=min_d.date(), min_value=min_d.date(),
                                           max_value=max_d.date(), key=f"cust_start_{page_key}")
                filters["date_start"] = pd.Timestamp(start_date)
            with dc2:
                end_date = st.date_input("To", value=max_d.date(), min_value=min_d.date(),
                                         max_value=max_d.date(), key=f"cust_end_{page_key}")
                filters["date_end"] = pd.Timestamp(end_date)

    # --- Dropdown Filters Row (inside expander) ---
    with st.expander("More Filters", expanded=False):
        f1, f2, f3, f4 = st.columns(4)

        with f1:
            if "AREA GROUP" in sr_df.columns:
                areas = sorted(sr_df["AREA GROUP"].dropna().unique().tolist())
                sel = st.multiselect("Area Group", areas, default=areas, key=f"area_{page_key}")
                filters["area_group"] = sel

        with f2:
            if "PRODUCT CATEGORY" in sr_df.columns:
                cats = sorted(sr_df["PRODUCT CATEGORY"].dropna().unique().tolist())
                sel = st.multiselect("Product Category", cats, default=cats, key=f"pcat_{page_key}")
                filters["product_category"] = sel

        with f3:
            if "TERMS" in sr_df.columns:
                terms = sorted(sr_df["TERMS"].dropna().unique().tolist())
                sel = st.multiselect("Payment Terms", terms, default=terms, key=f"terms_{page_key}")
                filters["terms"] = sel

        with f4:
            wh_vals = set()
            if so_df is not None and "Warehouse" in so_df.columns:
                wh_vals.update(so_df["Warehouse"].dropna().unique())
            if dr_df is not None and "Warehouse" in dr_df.columns:
                wh_vals.update(dr_df["Warehouse"].dropna().unique())
            if wh_vals:
                wh_list = sorted(wh_vals)
                sel = st.multiselect("Warehouse", wh_list, default=wh_list, key=f"wh_{page_key}")
                filters["warehouse"] = sel

    return filters


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
