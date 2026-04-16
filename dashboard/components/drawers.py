import streamlit as st


def kpi_card(label, value, delta=None, delta_label=None, value_class="", sub_text=None, icon=None, icon_class=""):
    """Render a dark-themed KPI card matching SMIFP style."""
    val_cls = f"kpi-value {value_class}" if value_class else "kpi-value"

    icon_html = ""
    if icon:
        ic = f"kpi-icon-box {icon_class}" if icon_class else "kpi-icon-box"
        icon_html = f'<div class="{ic}">{icon}</div>'

    delta_html = ""
    if delta is not None and delta_label:
        cls = "positive" if delta >= 0 else "negative"
        delta_html = f'<div class="kpi-delta {cls}">{delta_label}</div>'
    elif sub_text:
        delta_html = f'<div class="kpi-delta muted">{sub_text}</div>'

    st.markdown(f"""
    <div class="kpi-card">
        {icon_html}
        <div class="kpi-label">{label}</div>
        <div class="{val_cls}">{value}</div>
        {delta_html}
    </div>""", unsafe_allow_html=True)


def mini_card(label, value, icon=None):
    """Render a small summary card."""
    icon_html = f'<div class="mini-icon-box">{icon}</div>' if icon else ""
    st.markdown(f"""
    <div class="mini-card">
        {icon_html}
        <div>
            <div class="mini-label">{label}</div>
            <div class="mini-value">{value}</div>
        </div>
    </div>""", unsafe_allow_html=True)


def compare_card(label, current, previous, delta_text, delta_up=True):
    """Render a comparison card: current -> previous with delta."""
    cls = "up" if delta_up else "down"
    st.markdown(f"""
    <div class="compare-card">
        <div class="compare-label">{label}</div>
        <span class="compare-main">{current}</span>
        <span class="compare-arrow">&rarr;</span>
        <span class="compare-prev">{previous}</span>
        <span class="compare-delta {cls}">{delta_text}</span>
    </div>""", unsafe_allow_html=True)


def section_card_start(title, subtitle=None):
    """Start a section card (call section_card_end after content).
    NOTE: This does not reliably wrap Streamlit elements due to HTML isolation.
    Prefer st.container(border=True) + section_card_header() instead."""
    sub = f'<div class="section-card-subtitle">{subtitle}</div>' if subtitle else ""
    st.markdown(f"""<div class="section-card">
        <div class="section-card-title">{title}</div>
        {sub}""", unsafe_allow_html=True)


def section_card_end():
    st.markdown("</div>", unsafe_allow_html=True)


def section_card_header(title, subtitle=None):
    """Render a section card header inside a st.container(border=True)."""
    sub = f'<div class="section-card-subtitle">{subtitle}</div>' if subtitle else ""
    st.markdown(f"""<div class="section-card-title">{title}</div>
        {sub}
        <div style="border-bottom: 1px solid #2E4A34; margin-bottom: 0.8rem;"></div>""", unsafe_allow_html=True)


def alert_banner(message, alert_type="amber"):
    st.markdown(f'<div class="alert-banner alert-{alert_type}">{message}</div>', unsafe_allow_html=True)


def risk_card(title, description, risk_type="danger"):
    cls = "warning" if risk_type == "warning" else ""
    st.markdown(f"""
    <div class="risk-card {cls}">
        <div class="risk-title">{title}</div>
        <div class="risk-desc">{description}</div>
    </div>""", unsafe_allow_html=True)


def risk_section_header(title, count=0):
    """Render a risk section header with count badge."""
    if count > 0:
        badge_html = f'<span class="risk-count-badge">{count}</span>'
    else:
        badge_html = '<span class="risk-count-badge clear">0</span>'
    st.markdown(f'<div class="risk-header">{title} {badge_html}</div>', unsafe_allow_html=True)


def all_clear_box(message="No significant risks detected for the current period."):
    """Render a green 'all clear' box when no risks are present."""
    st.markdown(f"""
    <div class="all-clear-box">
        {message}
        <div class="all-clear-sub">All key metrics are within normal ranges</div>
    </div>""", unsafe_allow_html=True)


def section_header(title):
    st.markdown(f'<div class="section-header">{title}</div>', unsafe_allow_html=True)


def insight_card(message, insight_type="info"):
    st.markdown(f'<div class="insight-card insight-{insight_type}">{message}</div>', unsafe_allow_html=True)


def badge(text, badge_type="green"):
    return f'<span class="badge badge-{badge_type}">{text}</span>'


def concentration_bar(segments):
    """Render a concentration bar. segments = [(label, pct, color), ...]"""
    parts = ""
    for label, pct, color in segments:
        parts += f'<div class="seg" style="width:{pct}%;background:{color};">{label}</div>'
    st.markdown(f'<div class="conc-bar">{parts}</div>', unsafe_allow_html=True)


def styled_table(headers, rows, green_cols=None):
    """Render a styled HTML table matching dark theme."""
    green_cols = green_cols or []
    th = "".join(f"<th>{h}</th>" for h in headers)
    tbody = ""
    for row in rows:
        tds = ""
        for i, cell in enumerate(row):
            cls = ' class="val-green"' if i in green_cols else ""
            tds += f"<td{cls}>{cell}</td>"
        tbody += f"<tr>{tds}</tr>"
    st.markdown(f"""
    <table class="styled-table">
        <thead><tr>{th}</tr></thead>
        <tbody>{tbody}</tbody>
    </table>""", unsafe_allow_html=True)


def top_bar(data_date, current_time):
    st.markdown(f"""
    <div class="top-bar">
        <span>Data as of: <strong>{data_date}</strong></span>
        <span>{current_time}</span>
    </div>""", unsafe_allow_html=True)
