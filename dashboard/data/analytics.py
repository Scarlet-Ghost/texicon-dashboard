"""
Texicon Sales Intelligence Analytics Module
Pure data functions — no Streamlit imports.
"""
import pandas as pd
import numpy as np
from itertools import combinations


# ---------------------------------------------------------------------------
# 0. Monthly KPI Trends (for KPI card sparklines)
# ---------------------------------------------------------------------------

def compute_monthly_kpi_trends(sr_df):
    """Return dict of monthly series for KPI sparklines. Missing columns return [].
    Each series is a list of floats ordered by month."""
    if sr_df.empty or "YEAR_MONTH" not in sr_df.columns:
        return {}

    gb = sr_df.groupby("YEAR_MONTH")
    trends = {}
    trends["net_revenue"] = gb["NET SALES"].sum().sort_index().tolist()
    trends["net_sales"] = trends["net_revenue"]
    if "GROSS SALES" in sr_df.columns:
        trends["gross_sales"] = gb["GROSS SALES"].sum().sort_index().tolist()

    gross = gb["GROSS SALES"].sum().sort_index() if "GROSS SALES" in sr_df.columns else None
    net = gb["NET SALES"].sum().sort_index()
    if gross is not None:
        disc_pct = ((gross - net) / gross.replace(0, np.nan) * 100).fillna(0).tolist()
        trends["discount_pct"] = disc_pct

    if "CLIENT" in sr_df.columns:
        trends["active_customers"] = gb["CLIENT"].nunique().sort_index().tolist()
        trends["active_clients"] = trends["active_customers"]
    if "QTY IN L/KG" in sr_df.columns:
        trends["qty"] = gb["QTY IN L/KG"].sum().sort_index().tolist()
    if "INV NO." in sr_df.columns:
        invoices_mo = gb["INV NO."].nunique().sort_index()
        net_mo = gb["NET SALES"].sum().sort_index()
        avg_tx = (net_mo / invoices_mo.replace(0, np.nan)).fillna(0).tolist()
        trends["avg_transaction"] = avg_tx
    if "IS_CREDIT" in sr_df.columns:
        credit_mo = sr_df.groupby(["YEAR_MONTH", "IS_CREDIT"])["NET SALES"].sum().unstack(fill_value=0)
        if True in credit_mo.columns:
            total_mo = credit_mo.sum(axis=1).replace(0, np.nan)
            trends["credit_pct"] = (credit_mo[True] / total_mo * 100).fillna(0).sort_index().tolist()

    # Estimated DSO trend, weighted by credit sales per month
    if "IS_CREDIT" in sr_df.columns and "TERMS" in sr_df.columns:
        term_days_map = {"COD": 0, "CBD": 0, "CASH": 0, "30PDC": 30, "30D": 30,
                         "60PDC": 60, "60D": 60, "90D": 90, "120D": 120}
        cr = sr_df[sr_df["IS_CREDIT"] == True].copy()
        if not cr.empty:
            cr["TERM_DAYS"] = cr["TERMS"].map(term_days_map).fillna(60)
            dso_mo = cr.groupby("YEAR_MONTH").apply(
                lambda d: (d["TERM_DAYS"] * d["NET SALES"]).sum() / max(d["NET SALES"].sum(), 1)
            ).sort_index().tolist()
            trends["dso_estimate"] = dso_mo

    return trends


def build_kpi_trends(sr_f, so_f=None, dr_f=None):
    """Single entry point for all per-page KPI sparkline data. Returns the union
    of monthly trends derivable from each frame. Pages call this once and key
    into the result by metric name (e.g. trends.get('net_sales'))."""
    trends = compute_monthly_kpi_trends(sr_f) if sr_f is not None else {}

    # Bookings + fulfillment from sales orders
    if so_f is not None and not so_f.empty and "SO Date" in so_f.columns:
        so = so_f.copy()
        so["SO_MONTH"] = so["SO Date"].dt.to_period("M").dt.to_timestamp()
        if "Booking Amount" in so.columns:
            trends["bookings"] = so.groupby("SO_MONTH")["Booking Amount"].sum().sort_index().tolist()
        if "CYCLE_DAYS" in so.columns:
            cd = so.dropna(subset=["CYCLE_DAYS"])
            if not cd.empty:
                trends["on_time_pct"] = cd.groupby("SO_MONTH").apply(
                    lambda d: (d["CYCLE_DAYS"].le(7).sum() / max(len(d), 1)) * 100
                ).sort_index().tolist()
                trends["avg_lead_time"] = cd.groupby("SO_MONTH")["CYCLE_DAYS"].mean().sort_index().tolist()

    # Delivery counts and value from delivery report
    if dr_f is not None and not dr_f.empty and "Delivery Date" in dr_f.columns:
        dr = dr_f.copy()
        dr["DEL_MONTH"] = dr["Delivery Date"].dt.to_period("M").dt.to_timestamp()
        if "Delivered Amount" in dr.columns:
            trends["delivered_value"] = dr.groupby("DEL_MONTH")["Delivered Amount"].sum().sort_index().tolist()
            trends["total_deliveries"] = dr.groupby("DEL_MONTH").size().sort_index().tolist()

    # Fulfillment rate per month if both bookings and delivered exist
    if "bookings" in trends and "delivered_value" in trends:
        n = min(len(trends["bookings"]), len(trends["delivered_value"]))
        if n > 0:
            trends["fulfillment_rate"] = [
                (trends["delivered_value"][i] / trends["bookings"][i] * 100) if trends["bookings"][i] > 0 else 0
                for i in range(n)
            ]

    return trends


# ---------------------------------------------------------------------------
# 0b. PDC Compliance — honest computation or None
# ---------------------------------------------------------------------------

def try_compute_pdc_compliance(sr_f, cr_f, min_n=20):
    """Compute 30-day and 60-day Payment-Date Compliance from sales report
    (invoice dates + payment terms) and collection report (deposit dates).

    Returns None when either bucket has fewer than `min_n` invoices in the
    overlapping period — the metric is unreliable below that threshold and we
    refuse to fabricate one. Returns a dict otherwise:

        {"30d_pct": float, "30d_n": int, "30d_paid": int,
         "60d_pct": float, "60d_n": int, "60d_paid": int,
         "sample_window": "YYYY-MM-DD .. YYYY-MM-DD"}
    """
    if sr_f is None or cr_f is None or sr_f.empty or cr_f.empty:
        return None
    if "INV NO." not in sr_f.columns or "TERMS" not in sr_f.columns or "DATE" not in sr_f.columns:
        return None

    inv_col = next((c for c in cr_f.columns if c.upper() in ("INV NO.", "INVOICE NO", "INV NO", "INVOICE")), None)
    deposit_col = next((c for c in cr_f.columns if "DEPOSIT" in c.upper() and "DATE" in c.upper()), None)
    if not inv_col or not deposit_col:
        return None

    cr = cr_f[[inv_col, deposit_col]].dropna()
    cr.columns = ["INV NO.", "DEPOSIT_DATE"]
    sr = sr_f[["INV NO.", "DATE", "TERMS"]].dropna(subset=["INV NO.", "DATE", "TERMS"])

    merged = sr.merge(cr, on="INV NO.", how="inner")
    if merged.empty:
        return None

    merged["TERMS_UP"] = merged["TERMS"].astype(str).str.upper()
    days_late = (merged["DEPOSIT_DATE"] - merged["DATE"]).dt.days

    out = {}
    for bucket_name, term_filter, expected_days in (
        ("30d", merged["TERMS_UP"].isin(["30D", "30PDC"]), 30),
        ("60d", merged["TERMS_UP"].isin(["60D", "60PDC"]), 60),
    ):
        sub = merged[term_filter]
        n = len(sub)
        if n < min_n:
            return None
        on_time = (days_late[sub.index] <= expected_days).sum()
        out[f"{bucket_name}_n"] = int(n)
        out[f"{bucket_name}_paid"] = int(on_time)
        out[f"{bucket_name}_pct"] = float(on_time) / n * 100

    if "DEPOSIT_DATE" in merged.columns and not merged["DEPOSIT_DATE"].dropna().empty:
        out["sample_window"] = (
            merged["DEPOSIT_DATE"].min().strftime("%Y-%m-%d") + " .. " +
            merged["DEPOSIT_DATE"].max().strftime("%Y-%m-%d")
        )
    return out


# ---------------------------------------------------------------------------
# 1. Q1 Year-over-Year Comparison
# ---------------------------------------------------------------------------

def _q1_metrics(df):
    """Compute summary metrics for a Q1 slice."""
    return {
        "net_sales": df["NET SALES"].sum(),
        "gross_sales": df["GROSS SALES"].sum(),
        "volume": df["QTY IN L/KG"].sum() if "QTY IN L/KG" in df.columns else 0,
        "client_count": df["CLIENT"].nunique() if "CLIENT" in df.columns else 0,
        "item_count": df["ITEM"].nunique() if "ITEM" in df.columns else 0,
        "invoice_count": df["INV NO."].nunique() if "INV NO." in df.columns else 0,
        "avg_transaction": (
            df["NET SALES"].sum() / max(df["INV NO."].nunique(), 1)
            if "INV NO." in df.columns else 0
        ),
        "avg_discount_pct": df["DISCOUNT_PCT"].mean() if "DISCOUNT_PCT" in df.columns else 0,
    }


def _safe_growth(new, old):
    return ((new - old) / old * 100) if old > 0 else (100.0 if new > 0 else 0.0)


def compute_q1_comparison(sr_df):
    """Compare Q1 2025 vs Q1 2026 across all key dimensions."""
    if sr_df.empty or "YEAR" not in sr_df.columns:
        return None

    q1_months = ["JANUARY", "FEBRUARY", "MARCH"]
    mc = "MONTH_CLEAN" if "MONTH_CLEAN" in sr_df.columns else "MONTH"
    sr_q = sr_df[sr_df[mc].isin(q1_months)].copy()
    sr_q["YEAR"] = sr_q["YEAR"].astype(int)

    q1_25 = sr_q[sr_q["YEAR"] == 2025]
    q1_26 = sr_q[sr_q["YEAR"] == 2026]

    if q1_25.empty and q1_26.empty:
        return None

    s25 = _q1_metrics(q1_25)
    s26 = _q1_metrics(q1_26)

    growth = {k: _safe_growth(s26[k], s25[k]) for k in s25}

    # --- Monthly breakdown for side-by-side chart ---
    month_order = {"JANUARY": 1, "FEBRUARY": 2, "MARCH": 3}
    monthly = []
    for year, sub in [(2025, q1_25), (2026, q1_26)]:
        if sub.empty:
            continue
        m = sub.groupby(mc)["NET SALES"].sum().reset_index()
        m.columns = ["Month", "Net Sales"]
        m["Month_Num"] = m["Month"].map(month_order)
        m["Year"] = year
        m["Month_Label"] = m["Month"].str[:3].str.title()
        monthly.append(m)
    monthly_df = pd.concat(monthly, ignore_index=True) if monthly else pd.DataFrame()

    # --- Item changes ---
    item_25 = q1_25.groupby("ITEM")["NET SALES"].sum().rename("Q1_2025") if not q1_25.empty else pd.Series(dtype=float, name="Q1_2025")
    item_26 = q1_26.groupby("ITEM")["NET SALES"].sum().rename("Q1_2026") if not q1_26.empty else pd.Series(dtype=float, name="Q1_2026")
    item_cmp = pd.concat([item_25, item_26], axis=1).fillna(0)
    item_cmp["Change"] = item_cmp["Q1_2026"] - item_cmp["Q1_2025"]
    item_cmp["Change_Pct"] = np.where(
        item_cmp["Q1_2025"] > 0,
        item_cmp["Change"] / item_cmp["Q1_2025"] * 100,
        np.where(item_cmp["Q1_2026"] > 0, 100, 0),
    )
    item_cmp = item_cmp.reset_index().rename(columns={"index": "ITEM"}) if "ITEM" not in item_cmp.columns else item_cmp.reset_index()

    # --- Client changes ---
    cli_25 = q1_25.groupby("CLIENT")["NET SALES"].sum().rename("Q1_2025") if not q1_25.empty else pd.Series(dtype=float, name="Q1_2025")
    cli_26 = q1_26.groupby("CLIENT")["NET SALES"].sum().rename("Q1_2026") if not q1_26.empty else pd.Series(dtype=float, name="Q1_2026")
    cli_cmp = pd.concat([cli_25, cli_26], axis=1).fillna(0)
    cli_cmp["Change"] = cli_cmp["Q1_2026"] - cli_cmp["Q1_2025"]
    cli_cmp["Change_Pct"] = np.where(
        cli_cmp["Q1_2025"] > 0,
        cli_cmp["Change"] / cli_cmp["Q1_2025"] * 100,
        np.where(cli_cmp["Q1_2026"] > 0, 100, 0),
    )
    cli_cmp = cli_cmp.reset_index()

    # New / Lost clients
    clients_25 = set(q1_25["CLIENT"].unique()) if not q1_25.empty else set()
    clients_26 = set(q1_26["CLIENT"].unique()) if not q1_26.empty else set()
    new_clients = sorted(clients_26 - clients_25)
    lost_clients = sorted(clients_25 - clients_26)

    new_cli_df = cli_cmp[cli_cmp["CLIENT"].isin(new_clients)].sort_values("Q1_2026", ascending=False) if new_clients else pd.DataFrame()
    lost_cli_df = cli_cmp[cli_cmp["CLIENT"].isin(lost_clients)].sort_values("Q1_2025", ascending=False) if lost_clients else pd.DataFrame()

    return {
        "summary_2025": s25,
        "summary_2026": s26,
        "growth": growth,
        "monthly": monthly_df,
        "item_changes": item_cmp.sort_values("Change", ascending=False),
        "client_changes": cli_cmp.sort_values("Change", ascending=False),
        "new_clients": new_cli_df,
        "lost_clients": lost_cli_df,
        "new_client_count": len(new_clients),
        "lost_client_count": len(lost_clients),
    }


# ---------------------------------------------------------------------------
# 2. Item Pairing / Bundle Analysis
# ---------------------------------------------------------------------------

def compute_item_pairings(sr_df, min_support=5):
    """Find frequently co-purchased items on the same invoice."""
    if sr_df.empty or "INV NO." not in sr_df.columns or "ITEM" not in sr_df.columns:
        return None

    inv_items = sr_df.groupby("INV NO.")["ITEM"].apply(lambda x: sorted(set(x)))
    total_invoices = len(inv_items)
    multi = inv_items[inv_items.apply(len) > 1]

    if multi.empty:
        return None

    # Count individual item frequencies
    item_freq = sr_df.groupby("ITEM")["INV NO."].nunique()

    # Count co-occurrences
    from collections import Counter
    pair_counts = Counter()
    for items in multi:
        for pair in combinations(items, 2):
            pair_counts[pair] += 1

    # Build DataFrame
    rows = []
    for (a, b), count in pair_counts.items():
        if count < min_support:
            continue
        freq_a = item_freq.get(a, 1)
        freq_b = item_freq.get(b, 1)
        support_pct = count / total_invoices * 100

        # Revenue where both items appear on same invoice
        invs_with_pair = sr_df[sr_df["INV NO."].isin(
            multi[multi.apply(lambda x: a in x and b in x)].index
        )]
        combined_rev = invs_with_pair[invs_with_pair["ITEM"].isin([a, b])]["NET SALES"].sum()

        rows.append({
            "item_a": a,
            "item_b": b,
            "count": count,
            "support_pct": round(support_pct, 2),
            "confidence_a_to_b": round(count / freq_a * 100, 1),
            "confidence_b_to_a": round(count / freq_b * 100, 1),
            "combined_revenue": combined_rev,
        })

    if not rows:
        return None

    pairings = pd.DataFrame(rows).sort_values("count", ascending=False).reset_index(drop=True)
    bundles = pairings.nlargest(10, "combined_revenue").reset_index(drop=True)

    return {
        "pairings": pairings,
        "bundle_suggestions": bundles,
        "stats": {
            "total_invoices": total_invoices,
            "multi_item_invoices": len(multi),
            "multi_item_pct": round(len(multi) / total_invoices * 100, 1),
            "unique_pairs": len(pairings),
        },
    }


# ---------------------------------------------------------------------------
# 3. Customer Behavior Patterns
# ---------------------------------------------------------------------------

def compute_customer_habits(sr_df):
    """Analyze purchasing patterns and segment customers by behavior."""
    if sr_df.empty or "CLIENT" not in sr_df.columns:
        return None

    # --- Frequency distribution ---
    cust_orders = sr_df.groupby("CLIENT")["INV NO."].nunique() if "INV NO." in sr_df.columns else sr_df.groupby("CLIENT").size()
    bins = [0, 1, 3, 6, 12, 9999]
    labels = ["1x", "2-3x", "4-6x", "7-12x", "13+"]
    freq_dist = pd.cut(cust_orders, bins=bins, labels=labels, right=True).value_counts().reindex(labels).fillna(0)
    freq_df = freq_dist.reset_index()
    freq_df.columns = ["Frequency", "Customers"]

    # --- Basket size (items per invoice) ---
    if "INV NO." in sr_df.columns and "ITEM" in sr_df.columns:
        basket = sr_df.groupby("INV NO.")["ITEM"].nunique()
        basket_stats = {
            "mean": round(basket.mean(), 1),
            "median": int(basket.median()),
            "max": int(basket.max()),
            "single_item_pct": round((basket == 1).sum() / len(basket) * 100, 1),
        }
        basket_bins = [0, 1, 2, 3, 5, 99]
        basket_labels = ["1 item", "2 items", "3 items", "4-5 items", "6+"]
        basket_dist = pd.cut(basket, bins=basket_bins, labels=basket_labels, right=True).value_counts().reindex(basket_labels).fillna(0)
        basket_df = basket_dist.reset_index()
        basket_df.columns = ["Basket Size", "Invoices"]
    else:
        basket_stats = {"mean": 0, "median": 0, "max": 0, "single_item_pct": 0}
        basket_df = pd.DataFrame()

    # --- Purchase timing ---
    dow_df = pd.DataFrame()
    dom_df = pd.DataFrame()
    if "DATE" in sr_df.columns:
        valid_dates = sr_df[sr_df["DATE"].notna()]
        if not valid_dates.empty:
            dow_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
            dow = valid_dates.groupby(valid_dates["DATE"].dt.day_name()).agg(
                Transactions=("NET SALES", "count"),
                Revenue=("NET SALES", "sum"),
            )
            dow = dow.reindex(dow_order).fillna(0).reset_index()
            dow.columns = ["Day", "Transactions", "Revenue"]
            dow_df = dow

            dom = valid_dates.groupby(valid_dates["DATE"].dt.day).agg(
                Transactions=("NET SALES", "count"),
                Revenue=("NET SALES", "sum"),
            ).reset_index()
            dom.columns = ["Day of Month", "Transactions", "Revenue"]
            dom_df = dom

    # --- Customer lifecycle ---
    agg_dict = {"NET SALES": "sum"}
    if "DATE" in sr_df.columns:
        agg_dict["DATE"] = ["min", "max"]
    if "INV NO." in sr_df.columns:
        agg_dict["INV NO."] = "nunique"
    if "ITEM" in sr_df.columns:
        agg_dict["ITEM"] = "nunique"
    if "QTY IN L/KG" in sr_df.columns:
        agg_dict["QTY IN L/KG"] = "sum"

    lifecycle = sr_df.groupby("CLIENT").agg(agg_dict)
    lifecycle.columns = ["_".join(c).strip("_") for c in lifecycle.columns]

    rename_map = {"NET SALES_sum": "total_revenue"}
    if "DATE_min" in lifecycle.columns:
        rename_map["DATE_min"] = "first_purchase"
    if "DATE_max" in lifecycle.columns:
        rename_map["DATE_max"] = "last_purchase"
    if "INV NO._nunique" in lifecycle.columns:
        rename_map["INV NO._nunique"] = "order_count"
    if "ITEM_nunique" in lifecycle.columns:
        rename_map["ITEM_nunique"] = "unique_items"
    if "QTY IN L/KG_sum" in lifecycle.columns:
        rename_map["QTY IN L/KG_sum"] = "total_qty"

    lifecycle = lifecycle.rename(columns=rename_map).reset_index()

    if "first_purchase" in lifecycle.columns and "last_purchase" in lifecycle.columns:
        lifecycle["span_days"] = (lifecycle["last_purchase"] - lifecycle["first_purchase"]).dt.days
    else:
        lifecycle["span_days"] = 0

    if "order_count" in lifecycle.columns:
        lifecycle["avg_order_value"] = np.where(
            lifecycle["order_count"] > 0,
            lifecycle["total_revenue"] / lifecycle["order_count"],
            0,
        )
    else:
        lifecycle["order_count"] = sr_df.groupby("CLIENT").size().values
        lifecycle["avg_order_value"] = np.where(
            lifecycle["order_count"] > 0,
            lifecycle["total_revenue"] / lifecycle["order_count"],
            0,
        )

    # --- Behavioral segmentation ---
    freq_col = "order_count"
    val_col = "total_revenue"

    if freq_col in lifecycle.columns and val_col in lifecycle.columns:
        freq_med = lifecycle[freq_col].median()
        val_q75 = lifecycle[val_col].quantile(0.75)
        val_q25 = lifecycle[val_col].quantile(0.25)

        conditions = [
            (lifecycle[freq_col] >= freq_med) & (lifecycle[val_col] >= val_q75),
            (lifecycle[freq_col] < freq_med) & (lifecycle[val_col] >= val_q75),
            (lifecycle[val_col] < val_q25),
        ]
        choices = ["Power Buyer", "Bulk Buyer", "Light Buyer"]
        lifecycle["segment"] = np.select(conditions, choices, default="Regular")
    else:
        lifecycle["segment"] = "Regular"

    seg_summary = lifecycle.groupby("segment").agg(
        count=("CLIENT", "size"),
        revenue=(val_col, "sum"),
        avg_revenue=(val_col, "mean"),
    ).reset_index()

    return {
        "frequency_dist": freq_df,
        "basket_stats": basket_stats,
        "basket_dist": basket_df,
        "timing_dow": dow_df,
        "timing_dom": dom_df,
        "lifecycle": lifecycle.sort_values("total_revenue", ascending=False),
        "segments": lifecycle,
        "segment_summary": seg_summary,
    }


# ---------------------------------------------------------------------------
# 4. Margin / GP Proxy Analysis
# ---------------------------------------------------------------------------

def compute_margin_analysis(sr_df):
    """Analyze discount rates and unit pricing as GP proxy."""
    if sr_df.empty:
        return None

    df = sr_df.copy()
    if "QTY IN L/KG" in df.columns:
        df["unit_net_price"] = np.where(
            df["QTY IN L/KG"] > 0, df["NET SALES"] / df["QTY IN L/KG"], 0
        )
    else:
        df["unit_net_price"] = 0

    if "DISCOUNT_PCT" not in df.columns:
        df["DISCOUNT_PCT"] = np.where(
            df["GROSS SALES"] > 0,
            (df["GROSS SALES"] - df["NET SALES"]) / df["GROSS SALES"] * 100,
            0,
        )

    # --- By product ---
    by_product = pd.DataFrame()
    if "ITEM" in df.columns:
        by_product = df.groupby("ITEM").agg(
            avg_discount=("DISCOUNT_PCT", "mean"),
            avg_unit_price=("unit_net_price", "mean"),
            net_sales=("NET SALES", "sum"),
            volume=("QTY IN L/KG", "sum") if "QTY IN L/KG" in df.columns else ("NET SALES", "count"),
        ).round(2).sort_values("net_sales", ascending=False).reset_index()

    # --- By client ---
    by_client = pd.DataFrame()
    if "CLIENT" in df.columns:
        by_client = df.groupby("CLIENT").agg(
            avg_discount=("DISCOUNT_PCT", "mean"),
            net_sales=("NET SALES", "sum"),
            transactions=("NET SALES", "count"),
        ).round(2).sort_values("avg_discount", ascending=False).reset_index()

    # --- By area ---
    by_area = pd.DataFrame()
    if "AREA GROUP" in df.columns:
        by_area = df.groupby("AREA GROUP").agg(
            avg_discount=("DISCOUNT_PCT", "mean"),
            net_sales=("NET SALES", "sum"),
            avg_unit_price=("unit_net_price", "mean"),
        ).round(2).sort_values("net_sales", ascending=False).reset_index()

    # --- By product category ---
    by_category = pd.DataFrame()
    if "PRODUCT CATEGORY" in df.columns:
        by_category = df.groupby("PRODUCT CATEGORY").agg(
            avg_discount=("DISCOUNT_PCT", "mean"),
            net_sales=("NET SALES", "sum"),
            avg_unit_price=("unit_net_price", "mean"),
        ).round(2).sort_values("net_sales", ascending=False).reset_index()

    # --- By month ---
    by_month = pd.DataFrame()
    if "YEAR_MONTH" in df.columns:
        by_month = df.groupby("YEAR_MONTH").agg(
            avg_discount=("DISCOUNT_PCT", "mean"),
            avg_unit_price=("unit_net_price", "mean"),
            net_sales=("NET SALES", "sum"),
        ).round(2).sort_index().reset_index()
        by_month["Month"] = by_month["YEAR_MONTH"].dt.strftime("%b %y")

    # --- Price erosion: Q1 2025 vs Q1 2026 ---
    price_erosion = pd.DataFrame()
    margin_risk = pd.DataFrame()
    q1_months = ["JANUARY", "FEBRUARY", "MARCH"]
    mc = "MONTH_CLEAN" if "MONTH_CLEAN" in df.columns else "MONTH"
    if mc in df.columns and "YEAR" in df.columns and "ITEM" in df.columns:
        q1 = df[df[mc].isin(q1_months)].copy()
        q1["YEAR"] = q1["YEAR"].astype(int)
        q25 = q1[q1["YEAR"] == 2025]
        q26 = q1[q1["YEAR"] == 2026]

        if not q25.empty and not q26.empty:
            p25 = q25.groupby("ITEM").agg(
                price_2025=("unit_net_price", "mean"),
                discount_2025=("DISCOUNT_PCT", "mean"),
                revenue_2025=("NET SALES", "sum"),
            )
            p26 = q26.groupby("ITEM").agg(
                price_2026=("unit_net_price", "mean"),
                discount_2026=("DISCOUNT_PCT", "mean"),
                revenue_2026=("NET SALES", "sum"),
            )
            pe = pd.concat([p25, p26], axis=1).dropna(subset=["price_2025", "price_2026"])
            pe["price_change"] = pe["price_2026"] - pe["price_2025"]
            pe["price_change_pct"] = np.where(
                pe["price_2025"] > 0, pe["price_change"] / pe["price_2025"] * 100, 0
            )
            pe["discount_change"] = pe["discount_2026"] - pe["discount_2025"]
            price_erosion = pe.round(2).sort_values("price_change_pct").reset_index()

            # Margin risk: discount increased AND price decreased
            margin_risk = pe[
                (pe["discount_change"] > 0.5) | (pe["price_change_pct"] < -5)
            ].round(2).sort_values("price_change_pct").reset_index()

    # Summary stats
    overall_discount = df["DISCOUNT_PCT"].mean() if not df.empty else 0
    overall_unit_price = df.loc[df["unit_net_price"] > 0, "unit_net_price"].mean() if not df.empty else 0

    return {
        "by_product": by_product,
        "by_client": by_client,
        "by_area": by_area,
        "by_category": by_category,
        "by_month": by_month,
        "price_erosion": price_erosion,
        "margin_risk": margin_risk,
        "overall_discount": round(overall_discount, 2),
        "overall_unit_price": round(overall_unit_price, 2),
    }


# ---------------------------------------------------------------------------
# 5. Granular Date Breakdown
# ---------------------------------------------------------------------------

def compute_daily_breakdown(sr_df):
    """Daily, weekly, and pattern-level date breakdowns."""
    if sr_df.empty or "DATE" not in sr_df.columns:
        return None

    df = sr_df[sr_df["DATE"].notna()].copy()
    if df.empty:
        return None

    # --- Daily ---
    daily = df.groupby("DATE").agg(
        revenue=("NET SALES", "sum"),
        volume=("QTY IN L/KG", "sum") if "QTY IN L/KG" in df.columns else ("NET SALES", "count"),
        transactions=("NET SALES", "count"),
        invoices=("INV NO.", "nunique") if "INV NO." in df.columns else ("NET SALES", "count"),
    ).sort_index().reset_index()
    daily["day_name"] = daily["DATE"].dt.day_name()
    daily["Date_Label"] = daily["DATE"].dt.strftime("%b %d")

    # --- Weekly ---
    df_daily = df.set_index("DATE").resample("W-MON")
    weekly = df_daily.agg(
        revenue=("NET SALES", "sum"),
        transactions=("NET SALES", "count"),
    ).reset_index()
    weekly["Week_Label"] = weekly["DATE"].dt.strftime("W%U %b %d")
    if len(weekly) > 1:
        weekly["wow_change"] = weekly["revenue"].pct_change() * 100
    else:
        weekly["wow_change"] = 0

    # --- Peaks ---
    best_day = daily.loc[daily["revenue"].idxmax()] if not daily.empty else None
    worst_day = daily.loc[daily["revenue"].idxmin()] if not daily.empty else None
    avg_daily_rev = daily["revenue"].mean() if not daily.empty else 0

    peaks = {
        "best_day": best_day["DATE"].strftime("%b %d, %Y") if best_day is not None else "N/A",
        "best_day_rev": best_day["revenue"] if best_day is not None else 0,
        "worst_day": worst_day["DATE"].strftime("%b %d, %Y") if worst_day is not None else "N/A",
        "worst_day_rev": worst_day["revenue"] if worst_day is not None else 0,
        "avg_daily_revenue": avg_daily_rev,
        "total_active_days": len(daily),
    }

    # --- Day of week pattern ---
    dow_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    dow = daily.groupby("day_name").agg(
        avg_revenue=("revenue", "mean"),
        total_revenue=("revenue", "sum"),
        count=("revenue", "count"),
    )
    dow = dow.reindex(dow_order).fillna(0).reset_index()
    dow.columns = ["Day", "Avg Revenue", "Total Revenue", "Active Days"]

    return {
        "daily": daily,
        "weekly": weekly,
        "peaks": peaks,
        "dow_pattern": dow,
    }


# ---- Sales Home helpers ----
# Exposed for pages/0_Sales_Home.py. All helpers accept the transformed
# sales-report dataframe (`sr`) and return pure-python / pandas results.
# No cost/margin columns referenced.


def _resolve_columns(sr):
    """Return (customer_col, item_col, date_col, revenue_col) by best-match.

    Falls back to the first column whose lowercase name contains the keyword.
    Raises KeyError if no plausible column is found.
    """
    def pick(keywords):
        for col in sr.columns:
            lc = col.lower()
            if any(k in lc for k in keywords):
                return col
        raise KeyError(f"No column matching {keywords} in {list(sr.columns)}")

    customer_col = pick(["client", "customer"])
    # Prefer the bare "ITEM" column over "ITEM CODE" by checking exact match first
    item_col = next(
        (col for col in sr.columns if col.upper() == "ITEM"),
        None,
    ) or pick(["item", "product", "sku"])
    # Prefer the parsed "DATE" column over raw "SI. DATE"
    date_col = next(
        (col for col in sr.columns if col.upper() == "DATE"),
        None,
    ) or pick(["date", "txn_date", "transaction"])
    revenue_col = pick(["net sales", "revenue", "total", "amount"])
    return customer_col, item_col, date_col, revenue_col


def get_active_customers_this_month(sr, today=None):
    """Distinct customer count with at least one transaction in the current month."""
    if sr is None or len(sr) == 0:
        return 0
    today = today or pd.Timestamp.today()
    customer_col, _, date_col, _ = _resolve_columns(sr)
    mask = (
        (sr[date_col].dt.year == today.year)
        & (sr[date_col].dt.month == today.month)
    )
    return int(sr.loc[mask, customer_col].nunique())


def get_new_customers_this_month(sr, today=None):
    """Customers whose first-ever order falls in the current month."""
    if sr is None or len(sr) == 0:
        return 0
    today = today or pd.Timestamp.today()
    customer_col, _, date_col, _ = _resolve_columns(sr)
    first_order = sr.groupby(customer_col)[date_col].min()
    mask = (first_order.dt.year == today.year) & (first_order.dt.month == today.month)
    return int(mask.sum())


def get_top_customers_ytd(sr, n=10, today=None):
    """Top N customers by YTD revenue. Returns DataFrame with columns:
    customer, revenue, orders, last_order_date.
    """
    if sr is None or len(sr) == 0:
        return pd.DataFrame(columns=["customer", "revenue", "orders", "last_order_date"])
    today = today or pd.Timestamp.today()
    customer_col, _, date_col, revenue_col = _resolve_columns(sr)
    ytd = sr[sr[date_col].dt.year == today.year]
    if ytd.empty:
        return pd.DataFrame(columns=["customer", "revenue", "orders", "last_order_date"])
    agg = ytd.groupby(customer_col).agg(
        revenue=(revenue_col, "sum"),
        orders=(date_col, "count"),
        last_order_date=(date_col, "max"),
    ).reset_index().rename(columns={customer_col: "customer"})
    return agg.sort_values("revenue", ascending=False).head(n).reset_index(drop=True)


def get_top_items_ytd(sr, n=10, today=None):
    """Top N items by YTD revenue. Returns DataFrame with columns:
    item, revenue, qty (if a qty column exists, else omitted).
    """
    if sr is None or len(sr) == 0:
        return pd.DataFrame(columns=["item", "revenue"])
    today = today or pd.Timestamp.today()
    _, item_col, date_col, revenue_col = _resolve_columns(sr)
    ytd = sr[sr[date_col].dt.year == today.year]
    if ytd.empty:
        return pd.DataFrame(columns=["item", "revenue"])

    qty_col = None
    for col in sr.columns:
        lc = col.lower()
        if "qty" in lc or "quantity" in lc or lc == "units":
            qty_col = col
            break

    if qty_col is not None:
        agg = ytd.groupby(item_col).agg(
            revenue=(revenue_col, "sum"),
            qty=(qty_col, "sum"),
        ).reset_index().rename(columns={item_col: "item"})
    else:
        agg = ytd.groupby(item_col).agg(
            revenue=(revenue_col, "sum"),
        ).reset_index().rename(columns={item_col: "item"})
    return agg.sort_values("revenue", ascending=False).head(n).reset_index(drop=True)
