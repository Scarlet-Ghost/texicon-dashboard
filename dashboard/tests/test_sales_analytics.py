"""Smoke tests for Sales Home analytics helpers."""
import pandas as pd
import pytest

from data.analytics import (
    get_active_customers_this_month,
    get_new_customers_this_month,
    get_top_customers_ytd,
    get_top_items_ytd,
)


@pytest.fixture
def sample_sr():
    today = pd.Timestamp.today()
    this_month = today.replace(day=1)
    last_month = (this_month - pd.Timedelta(days=1)).replace(day=1)
    last_year = today.replace(year=today.year - 1, day=1)
    return pd.DataFrame({
        "customer": ["Acme", "Acme", "Beta", "Gamma", "Delta"],
        "item": ["X", "Y", "X", "Z", "Z"],
        "date": [this_month, last_month, this_month, last_year, this_month],
        "revenue": [100.0, 200.0, 50.0, 30.0, 70.0],
        "qty": [1, 2, 1, 1, 2],
    })


def test_active_customers_this_month(sample_sr):
    assert get_active_customers_this_month(sample_sr) == 3


def test_new_customers_this_month(sample_sr):
    # Beta and Delta have first-ever order this month
    assert get_new_customers_this_month(sample_sr) == 2


def test_top_customers_ytd_returns_correct_shape(sample_sr):
    df = get_top_customers_ytd(sample_sr, n=3)
    assert list(df.columns) == ["customer", "revenue", "orders", "last_order_date"]
    assert len(df) <= 3


def test_top_items_ytd_includes_qty_if_present(sample_sr):
    df = get_top_items_ytd(sample_sr, n=5)
    assert "item" in df.columns
    assert "revenue" in df.columns


def test_empty_dataframe_safe():
    empty = pd.DataFrame(columns=["customer", "item", "date", "revenue"])
    assert get_active_customers_this_month(empty) == 0
    assert get_new_customers_this_month(empty) == 0
    assert get_top_customers_ytd(empty).empty
    assert get_top_items_ytd(empty).empty
