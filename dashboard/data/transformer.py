import pandas as pd
import numpy as np
from data.constants import MONTH_ORDER, PRODUCT_CATEGORY_CLEANUP, CLUSTER_CLEANUP


def transform_sales_report(df):
    df = df.copy()
    # Strip whitespace from column names
    df.columns = df.columns.str.strip()

    # Coerce numeric columns
    for col in ["NET SALES", "GROSS SALES", "ORIGINAL PRICE", "QTY IN CTN", "QTY IN L/KG"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    # Normalize product category
    if "PRODUCT CATEGORY" in df.columns:
        df["PRODUCT CATEGORY"] = df["PRODUCT CATEGORY"].str.strip().str.upper()
        df["PRODUCT CATEGORY"] = df["PRODUCT CATEGORY"].replace(PRODUCT_CATEGORY_CLEANUP)

    # Normalize cluster names
    if "CLUSTER" in df.columns:
        df["CLUSTER"] = df["CLUSTER"].str.strip().str.upper()
        df["CLUSTER"] = df["CLUSTER"].replace(CLUSTER_CLEANUP)

    # Ensure date column
    if "SI. DATE" in df.columns:
        df["DATE"] = pd.to_datetime(df["SI. DATE"], errors="coerce")

    # Create MONTH_NUM for sorting
    if "MONTH" in df.columns:
        df["MONTH_CLEAN"] = df["MONTH"].str.strip().str.upper()
        df["MONTH_NUM"] = df["MONTH_CLEAN"].map(MONTH_ORDER)

    # Create sortable YEAR_MONTH
    if "YEAR" in df.columns and "MONTH_NUM" in df.columns:
        df["YEAR_MONTH"] = pd.to_datetime(
            df["YEAR"].astype(int).astype(str) + "-" + df["MONTH_NUM"].astype(int).astype(str) + "-01",
            errors="coerce",
        )

    # Compute discount amount
    df["DISCOUNT_AMOUNT"] = df["GROSS SALES"] - df["NET SALES"]
    df["DISCOUNT_PCT"] = np.where(
        df["GROSS SALES"] > 0,
        (df["DISCOUNT_AMOUNT"] / df["GROSS SALES"]) * 100,
        0,
    )

    # Normalize area group
    if "AREA GROUP" in df.columns:
        df["AREA GROUP"] = df["AREA GROUP"].str.strip().str.upper()

    # Normalize payment terms
    if "TERMS" in df.columns:
        df["TERMS"] = df["TERMS"].str.strip().str.upper()

    # Normalize client names
    if "CLIENT" in df.columns:
        df["CLIENT"] = df["CLIENT"].str.strip()

    # Sales category for credit vs cash
    if "SALES CATEGORY" in df.columns:
        df["SALES CATEGORY"] = df["SALES CATEGORY"].str.strip().str.upper()
    if "TERMS" in df.columns:
        df["IS_CREDIT"] = ~df["TERMS"].isin(["COD", "CBD", "CASH"])

    return df


def transform_sales_order(df):
    df = df.copy()
    df.columns = df.columns.str.strip()

    # Ensure dates
    for col in ["SO Date", "Delivery Date"]:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce")

    # Compute cycle days
    if "SO Date" in df.columns and "Delivery Date" in df.columns:
        df["CYCLE_DAYS"] = (df["Delivery Date"] - df["SO Date"]).dt.days
        df["CYCLE_DAYS"] = df["CYCLE_DAYS"].clip(lower=0)

    # Create month column
    if "SO Date" in df.columns:
        df["SO_MONTH"] = df["SO Date"].dt.to_period("M").dt.to_timestamp()

    # Coerce amounts
    if "Booking Amount" in df.columns:
        df["Booking Amount"] = pd.to_numeric(df["Booking Amount"], errors="coerce").fillna(0)
    if "Unit Price" in df.columns:
        df["Unit Price"] = pd.to_numeric(df["Unit Price"], errors="coerce").fillna(0)
    if "Ordered Qty" in df.columns:
        df["Ordered Qty"] = pd.to_numeric(df["Ordered Qty"], errors="coerce").fillna(0)

    # Normalize names
    if "Customer Name" in df.columns:
        df["Customer Name"] = df["Customer Name"].str.strip()
    if "Warehouse" in df.columns:
        df["Warehouse"] = df["Warehouse"].str.strip().str.upper()
    if "Payment Terms" in df.columns:
        df["Payment Terms"] = df["Payment Terms"].str.strip().str.upper()
    if "Group Name" in df.columns:
        df["Group Name"] = df["Group Name"].str.strip().str.upper()

    return df


def transform_delivery_report(df):
    df = df.copy()
    df.columns = df.columns.str.strip()

    # Ensure date
    if "Delivery Date" in df.columns:
        df["Delivery Date"] = pd.to_datetime(df["Delivery Date"], errors="coerce")

    # Create month column
    if "Delivery Date" in df.columns:
        df["DEL_MONTH"] = df["Delivery Date"].dt.to_period("M").dt.to_timestamp()

    # Coerce amounts
    for col in ["Delivered Qty", "Unit Price (VAT Incl)", "Delivered Amount"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    # Normalize
    if "Warehouse" in df.columns:
        df["Warehouse"] = df["Warehouse"].str.strip().str.upper()
    if "Customer" in df.columns:
        df["Customer"] = df["Customer"].str.strip()

    # Day of week
    if "Delivery Date" in df.columns:
        df["DEL_DOW"] = df["Delivery Date"].dt.day_name()

    return df


def transform_collection_report(df):
    df = df.copy()
    df.columns = df.columns.str.strip()

    # Coerce amounts
    for col in df.columns:
        if any(kw in col.upper() for kw in ["AMOUNT", "EWT", "TOTAL", "DEPOSIT"]):
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    # Find the date column
    date_cols = [c for c in df.columns if "DATE" in c.upper() and "DEPOSIT" not in c.upper()]
    if date_cols:
        df[date_cols[0]] = pd.to_datetime(df[date_cols[0]], errors="coerce")
        df["COLLECTION_DATE"] = df[date_cols[0]]

    # Find deposit date
    deposit_cols = [c for c in df.columns if "DEPOSIT" in c.upper() and "DATE" in c.upper()]
    if deposit_cols:
        df[deposit_cols[0]] = pd.to_datetime(df[deposit_cols[0]], errors="coerce")

    # Normalize customer
    cust_cols = [c for c in df.columns if "CUSTOMER" in c.upper()]
    if cust_cols:
        df[cust_cols[0]] = df[cust_cols[0]].astype(str).str.strip()

    return df


def build_customer_area_lookup(sr_df):
    """Build customer -> area group mapping from sales report."""
    if "CLIENT" in sr_df.columns and "AREA GROUP" in sr_df.columns:
        lookup = sr_df.groupby("CLIENT")["AREA GROUP"].agg(lambda x: x.mode().iloc[0] if not x.mode().empty else x.iloc[0])
        return lookup.to_dict()
    return {}
