import os
import pandas as pd
import streamlit as st
from data.constants import DATA_DIR, FILE_NAMES


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
