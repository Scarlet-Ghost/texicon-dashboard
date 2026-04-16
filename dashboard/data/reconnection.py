import pandas as pd
import numpy as np
from data.constants import (
    RECON_THRESHOLDS, RECON_URGENCY, RECON_EXCLUDE_CLIENTS,
)


def build_reconnection_data(sr_f, ref_date=None):
    """Aggregate sales report to customer level with segmentation and priority scoring."""
    if sr_f.empty or "CLIENT" not in sr_f.columns or "DATE" not in sr_f.columns:
        return pd.DataFrame()

    df = sr_f[~sr_f["CLIENT"].isin(RECON_EXCLUDE_CLIENTS)].copy()
    if df.empty:
        return pd.DataFrame()

    if ref_date is None:
        ref_date = df["DATE"].max()

    # --- Core aggregation ---
    qty_col = "QTY IN L/KG" if "QTY IN L/KG" in df.columns else None
    agg_dict = {
        "NET SALES": "sum",
        "DATE": ["max", "min"],
    }
    if "INV NO." in df.columns:
        agg_dict["INV NO."] = "nunique"
    if qty_col:
        agg_dict[qty_col] = "sum"

    cust = df.groupby("CLIENT").agg(agg_dict)
    cust.columns = ["_".join(c).strip("_") for c in cust.columns]
    cust = cust.rename(columns={
        "NET SALES_sum": "total_revenue",
        "DATE_max": "last_purchase",
        "DATE_min": "first_purchase",
    })
    if "INV NO._nunique" in cust.columns:
        cust = cust.rename(columns={"INV NO._nunique": "tx_count"})
    else:
        cust["tx_count"] = df.groupby("CLIENT").size()
    if qty_col:
        cust = cust.rename(columns={f"{qty_col}_sum": "total_qty"})
    else:
        cust["total_qty"] = 0

    cust = cust.reset_index()

    # --- Days inactive & segmentation ---
    cust["days_inactive"] = (ref_date - cust["last_purchase"]).dt.days
    hp = RECON_THRESHOLDS["high_potential"]
    ar = RECON_THRESHOLDS["at_risk"]
    cust["segment"] = np.where(
        cust["days_inactive"] <= hp, "High Potential",
        np.where(cust["days_inactive"] <= ar, "At Risk", "Falling Out"),
    )

    # --- Priority score ---
    max_rev = max(cust["total_revenue"].max(), 1)
    cust["urgency"] = cust["segment"].map(RECON_URGENCY)
    cust["priority_score"] = ((cust["total_revenue"] / max_rev * 100) * cust["urgency"]).round(1)

    # --- Enrichment: top products, category, area, sales rep ---
    top_products = (
        df.groupby(["CLIENT", "ITEM"])["NET SALES"]
        .sum()
        .reset_index()
        .sort_values(["CLIENT", "NET SALES"], ascending=[True, False])
        .groupby("CLIENT")
        .head(3)
        .groupby("CLIENT")["ITEM"]
        .apply(lambda x: ", ".join(s[:25] for s in x))
        .rename("top_products")
    )
    cust = cust.merge(top_products, on="CLIENT", how="left")

    if "PRODUCT CATEGORY" in df.columns:
        top_cat = df.groupby("CLIENT")["PRODUCT CATEGORY"].agg(
            lambda x: x.mode().iloc[0] if not x.mode().empty else ""
        ).rename("top_category")
        cust = cust.merge(top_cat, on="CLIENT", how="left")
    else:
        cust["top_category"] = ""

    if "AREA GROUP" in df.columns:
        area = df.groupby("CLIENT")["AREA GROUP"].agg(
            lambda x: x.mode().iloc[0] if not x.mode().empty else ""
        ).rename("area_group")
        cust = cust.merge(area, on="CLIENT", how="left")
    else:
        cust["area_group"] = ""

    if "SR" in df.columns:
        sr = df.groupby("CLIENT")["SR"].agg(
            lambda x: x.mode().iloc[0] if not x.mode().empty else ""
        ).rename("sales_rep")
        cust = cust.merge(sr, on="CLIENT", how="left")
    else:
        cust["sales_rep"] = ""

    # --- Derived ---
    cust["avg_order_value"] = np.where(cust["tx_count"] > 0, cust["total_revenue"] / cust["tx_count"], 0)
    cust = cust.sort_values("priority_score", ascending=False).reset_index(drop=True)

    return cust


def get_customer_transactions(sr_f, client_name):
    """Return transaction history for a single customer."""
    if sr_f.empty or "CLIENT" not in sr_f.columns:
        return pd.DataFrame()

    mask = sr_f["CLIENT"] == client_name
    cols = [c for c in ["DATE", "INV NO.", "ITEM", "PRODUCT CATEGORY", "QTY IN L/KG", "NET SALES", "TERMS"]
            if c in sr_f.columns]
    return sr_f.loc[mask, cols].sort_values("DATE", ascending=False).reset_index(drop=True)


def get_segment_summary(cust_df):
    """Return segment counts and revenue for KPI cards."""
    summary = {}
    if cust_df.empty:
        for seg in ["Falling Out", "At Risk", "High Potential"]:
            summary[seg] = {"count": 0, "revenue": 0}
        summary["total_customers"] = 0
        summary["total_revenue"] = 0
        return summary

    for seg in ["Falling Out", "At Risk", "High Potential"]:
        sub = cust_df[cust_df["segment"] == seg]
        summary[seg] = {"count": len(sub), "revenue": sub["total_revenue"].sum()}

    summary["total_customers"] = len(cust_df)
    summary["total_revenue"] = cust_df["total_revenue"].sum()
    return summary
