import streamlit as st
from components.drawers import kpi_card


def render_kpi_row(kpis, columns=None):
    """Render a row of KPI cards.

    kpis: list of dicts with keys:
        label, value, delta (opt), delta_label (opt),
        value_class (opt), sub_text (opt)
    """
    n = columns or len(kpis)
    cols = st.columns(n)
    for i, kpi in enumerate(kpis):
        with cols[i % n]:
            kpi_card(
                label=kpi["label"],
                value=kpi["value"],
                delta=kpi.get("delta"),
                delta_label=kpi.get("delta_label"),
                value_class=kpi.get("value_class", ""),
                sub_text=kpi.get("sub_text"),
                icon=kpi.get("icon"),
                icon_class=kpi.get("icon_class", ""),
            )
