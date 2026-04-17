import streamlit as st
from components.drawers import kpi_card, _tt
from components.formatting import format_php, format_pct, format_number


def render_kpi_row(kpis, columns=None):
    """Render a row of KPI cards from a list of spec dicts.

    Each spec supports:
        label, value, delta, delta_label, value_class, sub_text, icon,
        icon_class, tooltip, card_class, trend_data, computable, na_reason

    A spec with `computable=False` renders an na_card() in place of the value.
    """
    n = columns or len(kpis)
    cols = st.columns(n)
    for i, kpi in enumerate(kpis):
        with cols[i % n]:
            if kpi.get("computable") is False:
                na_card(
                    label=kpi["label"],
                    reason=kpi.get("na_reason", "Data unavailable"),
                    tooltip=kpi.get("tooltip"),
                )
            else:
                kpi_card(
                    label=kpi["label"],
                    value=kpi["value"],
                    delta=kpi.get("delta"),
                    delta_label=kpi.get("delta_label"),
                    value_class=kpi.get("value_class", ""),
                    sub_text=kpi.get("sub_text"),
                    icon=kpi.get("icon"),
                    icon_class=kpi.get("icon_class", ""),
                    tooltip=kpi.get("tooltip"),
                    card_class=kpi.get("card_class", ""),
                    trend_data=kpi.get("trend_data"),
                    lower_is_better=kpi.get("lower_is_better", False),
                )


def na_card(label, reason, tooltip=None):
    """Render a KPI card whose value cannot be computed honestly. Replaces any
    pattern of fabricating placeholder numbers."""
    html = (
        f'<div class="kpi-card kpi-card-na"{_tt(tooltip)}>'
        f'<div class="kpi-label">{label}</div>'
        f'<div class="kpi-value kpi-value--na">N/A</div>'
        f'<div class="kpi-delta muted">{reason}</div>'
        f'</div>'
    )
    st.markdown(html, unsafe_allow_html=True)


# --- Spec factories ----------------------------------------------------------
# Each factory returns a dict consumable by render_kpi_row(). Centralizes
# formatting + threshold-to-class so call sites stay declarative.

def _class_from_thresholds(value, thresholds, lower_is_better=False):
    """thresholds = (warn, danger). Returns 'warning' or 'danger' or ''."""
    if not thresholds:
        return ""
    warn, danger = thresholds
    if lower_is_better:
        if value <= danger: return "danger"
        if value <= warn:   return "warning"
        return ""
    if value >= danger: return "danger"
    if value >= warn:   return "warning"
    return ""


def kpi_spec_money(label, value_num, *, thresholds=None, lower_is_better=False,
                   sub_text=None, tooltip=None, trend_data=None, card_class="",
                   value_class=None):
    cls = value_class if value_class is not None else _class_from_thresholds(
        value_num, thresholds, lower_is_better)
    return {
        "label": label,
        "value": format_php(value_num),
        "value_class": cls,
        "sub_text": sub_text,
        "tooltip": tooltip,
        "trend_data": trend_data,
        "card_class": card_class,
        "lower_is_better": lower_is_better,
    }


def kpi_spec_pct(label, value_num, *, thresholds=None, lower_is_better=False,
                 sub_text=None, tooltip=None, trend_data=None, card_class="",
                 value_class=None):
    cls = value_class if value_class is not None else _class_from_thresholds(
        value_num, thresholds, lower_is_better)
    return {
        "label": label,
        "value": format_pct(value_num),
        "value_class": cls,
        "sub_text": sub_text,
        "tooltip": tooltip,
        "trend_data": trend_data,
        "card_class": card_class,
        "lower_is_better": lower_is_better,
    }


def kpi_spec_days(label, value_num, *, thresholds=None, sub_text=None, tooltip=None,
                  trend_data=None, card_class="", value_class=None,
                  lower_is_better=True):
    cls = value_class if value_class is not None else _class_from_thresholds(
        value_num or 0, thresholds)
    return {
        "label": label,
        "value": f"{value_num:.0f} days" if value_num is not None else "—",
        "value_class": cls,
        "sub_text": sub_text,
        "tooltip": tooltip,
        "trend_data": trend_data,
        "card_class": card_class,
        "lower_is_better": lower_is_better,
    }


def kpi_spec_count(label, value_num, *, sub_text=None, tooltip=None, trend_data=None,
                   value_class="neutral", card_class="", lower_is_better=False):
    return {
        "label": label,
        "value": format_number(value_num),
        "value_class": value_class,
        "sub_text": sub_text,
        "tooltip": tooltip,
        "trend_data": trend_data,
        "card_class": card_class,
        "lower_is_better": lower_is_better,
    }


def kpi_spec_na(label, na_reason, *, tooltip=None):
    return {
        "label": label,
        "value": None,
        "computable": False,
        "na_reason": na_reason,
        "tooltip": tooltip,
    }
