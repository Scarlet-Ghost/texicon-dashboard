import streamlit as st
try:
    from components.formatting import format_php, format_pct, format_number
except ModuleNotFoundError:
    from dashboard.components.formatting import format_php, format_pct, format_number


def render_kpi_row(specs, columns=None):
    """Render a row of KPI cards from a list of spec dicts.

    Each spec supports:
        label, value, delta, delta_dir, numeric_target, prefix, suffix, variant
        (new redesign keys)

    Legacy keys (value_class, sub_text, tooltip, card_class, trend_data,
    computable, na_reason, lower_is_better) are tolerated and ignored — they
    were consumed by the old kpi_card() helper which is no longer called here.

    A spec with `computable=False` renders an na_card() in place of the KPI.
    """
    import streamlit as st
    from dashboard.components.drawers import kpi_card_html, kpi_row_html
    from dashboard.components.motion import count_up_runtime_script

    def _to_kwargs(spec):
        """Map spec keys to kpi_card_html kwargs.

        Legacy spec helpers (kpi_spec_money, kpi_spec_pct, kpi_spec_count) emit:
          label, value, value_class, sub_text, tooltip, trend_data, card_class,
          lower_is_better
        None of these collide with the new keys (delta, delta_dir,
        numeric_target, prefix, suffix, variant), so we simply pass through
        whatever matches the allowed set and drop the rest.
        """
        if not isinstance(spec, dict):
            return {"label": "", "value": str(spec)}
        allowed = {"label", "value", "delta", "delta_dir",
                   "numeric_target", "prefix", "suffix", "variant"}
        return {k: v for k, v in spec.items() if k in allowed}

    cards = []
    for s in specs:
        if isinstance(s, dict) and s.get("computable") is False:
            # Render na_card inline as a tx-card for layout consistency
            label = s.get("label", "")
            reason = s.get("na_reason", "Data unavailable")
            cards.append(
                f'<div class="tx-card tx-kpi">'
                f'<div class="lbl">{label}</div>'
                f'<div class="val"><span class="tx-kpi-val">N/A</span></div>'
                f'<div class="delta">{reason}</div>'
                f'</div>'
            )
        else:
            cards.append(kpi_card_html(**_to_kwargs(s)))

    st.markdown(kpi_row_html(cards), unsafe_allow_html=True)
    st.markdown(count_up_runtime_script(), unsafe_allow_html=True)


def na_card(label, reason, tooltip=None):
    """Render a KPI card whose value cannot be computed honestly. Replaces any
    pattern of fabricating placeholder numbers."""
    try:
        from components.drawers import _tt
    except ModuleNotFoundError:
        from dashboard.components.drawers import _tt
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
