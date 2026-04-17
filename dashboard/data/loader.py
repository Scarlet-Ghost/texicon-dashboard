import os
import pandas as pd
import streamlit as st
from datetime import datetime
from data.constants import DATA_DIR, FILE_NAMES


def get_data_freshness():
    """Return hours since the most recently modified data file."""
    mtimes = []
    for key, fname in FILE_NAMES.items():
        path = os.path.join(DATA_DIR, fname)
        if os.path.exists(path):
            mtimes.append(os.path.getmtime(path))
    if not mtimes:
        return None
    latest = max(mtimes)
    hours = (datetime.now().timestamp() - latest) / 3600
    return hours


@st.cache_data(ttl=3600)
def load_sales_report():
    path = os.path.join(DATA_DIR, FILE_NAMES["sales_report"])
    df = pd.read_excel(path, engine="openpyxl")
    return df


@st.cache_data(ttl=3600)
def load_sales_order():
    path = os.path.join(DATA_DIR, FILE_NAMES["sales_order"])
    df = pd.read_excel(path, engine="openpyxl")
    return df


@st.cache_data(ttl=3600)
def load_delivery_report():
    path = os.path.join(DATA_DIR, FILE_NAMES["delivery_report"])
    df = pd.read_excel(path, engine="openpyxl")
    return df


@st.cache_data(ttl=3600)
def load_collection_report():
    path = os.path.join(DATA_DIR, FILE_NAMES["collection_report"])
    df = pd.read_excel(path, header=3, engine="openpyxl")
    # Drop phantom rows (all-NaN)
    df = df.dropna(how="all")
    # Keep only rows with a valid customer
    if "CUSTOMER" in df.columns:
        df = df[df["CUSTOMER"].notna()]
    return df
