import streamlit as st
import html as html_mod


def _tt(tooltip):
    """Return data-tooltip attribute string if tooltip is provided."""
    if tooltip:
        return f' data-tooltip="{html_mod.escape(tooltip)}"'
    return ""


# --- Page Navigation Mapping ---
_NAV_PAGES = [
    ("Executive", "app"),
    ("Revenue", "1_Revenue_Sales"),
    ("Cash", "2_Cash_Collections"),
    ("Operations", "3_Operations_Delivery"),
    ("Reconnect", "4_Customer_Reconnection"),
    ("Intel", "5_Sales_Intelligence"),
    ("Data", "6_Data_Explorer"),
]


def render_nav(active_page="app", risk_count=0):
    """Render the modern top navigation bar using st.page_link for routing.

    `risk_count` is accepted for signature compatibility but no longer shown
    as a badge — the dedicated `global_alert_strip` below the nav already
    communicates active warnings, and the brand label stays clean."""
    with st.container(border=True):
        cols = st.columns([1.4] + [1] * len(_NAV_PAGES))

        with cols[0]:
            st.markdown(
                '<div class="nav-brand-inline">Texicon</div>',
                unsafe_allow_html=True,
            )

        for i, (label, page_id) in enumerate(_NAV_PAGES):
            with cols[i + 1]:
                if page_id == active_page:
                    st.markdown(
                        f'<div class="nav-pill-active">{label}</div>',
                        unsafe_allow_html=True,
                    )
                else:
                    path = "app.py" if page_id == "app" else f"pages/{page_id}.py"
                    st.page_link(path, label=label, use_container_width=True)


def hero_kpi(label, value, sub_value=None, trend=None, delta=None, delta_label=None,
             tooltip=None, value_class="", spark_color="#00D68F"):
    """Render the focal hero metric at the top of a page. 3-4x taller than
    supporting KPIs. One per page — the single headline a CEO should see first.

    Note: `trend` and `spark_color` are retained for backward compatibility
    but intentionally not rendered — the hero keeps its focus on value +
    sub-text + delta label. Trend context lives in the page's monthly chart."""
    val_cls = f"hero-kpi-value {value_class}" if value_class else "hero-kpi-value"

    sub_html = ""
    if sub_value:
        sub_html = f'<span class="hero-kpi-sub">{sub_value}</span>'

    delta_html = ""
    if delta_label:
        cls = "positive"
        if delta is not None:
            cls = "positive" if delta >= 0 else "negative"
        elif value_class in ("danger", "warning"):
            cls = "warning" if value_class == "warning" else "negative"
        delta_html = f'<span class="hero-kpi-delta {cls}">{delta_label}</span>'

    meta_html = f'<div class="hero-kpi-meta">{sub_html}{delta_html}</div>' if (sub_html or delta_html) else ""

    html = (
        f'<div class="hero-kpi"{_tt(tooltip)}>'
        f'<div class="hero-kpi-label">{label}</div>'
        f'<div class="{val_cls}">{value}</div>'
        f'{meta_html}'
        f'</div>'
    )
    st.markdown(html, unsafe_allow_html=True)


def section_divider(title, eyebrow=None):
    """Visual rest between major analytic sections. Used between Sales Intel's
    5 analytic blocks and anywhere else the page needs a breath."""
    eyebrow_html = f'<div class="section-eyebrow">{eyebrow}</div>' if eyebrow else ""
    st.markdown(
        f'{eyebrow_html}'
        f'<h2 class="section-h2">{title}</h2>'
        f'<hr class="section-rule">',
        unsafe_allow_html=True,
    )


def _mom_chip_html(trend_data, lower_is_better=False):
    """Compute a MoM delta chip from the last two entries of a monthly trend.
    Returns '' if a meaningful delta can't be produced (too few points,
    zero baseline, NaN). Semantic color flips for lower-is-better metrics."""
    if not trend_data or len(trend_data) < 2:
        return ""
    curr, prev = trend_data[-1], trend_data[-2]
    if curr is None or prev is None:
        return ""
    try:
        curr_f, prev_f = float(curr), float(prev)
    except (TypeError, ValueError):
        return ""
    if prev_f != prev_f or curr_f != curr_f:  # NaN check
        return ""
    if abs(prev_f) < 1e-9:
        return ""
    delta_pct = (curr_f - prev_f) / abs(prev_f) * 100
    if abs(delta_pct) < 0.5:
        arrow, cls = "→", "muted"
    elif delta_pct > 0:
        arrow = "↑"
        cls = "negative" if lower_is_better else "positive"
    else:
        arrow = "↓"
        cls = "positive" if lower_is_better else "negative"
    return f'<div class="kpi-delta {cls}">{arrow} {abs(delta_pct):.1f}% MoM</div>'


def kpi_card(label, value, delta=None, delta_label=None, value_class="", sub_text=None,
             icon=None, icon_class="", tooltip=None, card_class="", trend_data=None,
             lower_is_better=False):
    """Render a KPI card. Icons are intentionally dropped from rendering — kept in
    the signature for backward compatibility but visually ignored.

    Meta-row priority: explicit delta > MoM chip from trend_data > sub_text.
    Sub_text always renders as a muted secondary line when present alongside
    a primary meta."""
    val_cls = f"kpi-value {value_class}" if value_class else "kpi-value"
    card_cls = f"kpi-card {card_class}" if card_class else "kpi-card"

    primary_meta = ""
    if delta is not None and delta_label:
        cls = "positive" if delta >= 0 else "negative"
        primary_meta = f'<div class="kpi-delta {cls}">{delta_label}</div>'
    elif trend_data:
        primary_meta = _mom_chip_html(trend_data, lower_is_better=lower_is_better)

    sub_html = ""
    if sub_text:
        sub_html = f'<div class="kpi-delta muted">{sub_text}</div>'
    # If no primary meta was produced but sub_text exists, sub_text becomes primary
    if not primary_meta and sub_html:
        primary_meta, sub_html = sub_html, ""

    html = (
        f'<div class="{card_cls}"{_tt(tooltip)}>'
        f'<div class="kpi-label">{label}</div>'
        f'<div class="{val_cls}">{value}</div>'
        f'{primary_meta}'
        f'{sub_html}'
        f'</div>'
    )
    st.markdown(html, unsafe_allow_html=True)


def mini_card(label, value, icon=None, tooltip=None):
    """Render a small summary card. Icon arg is ignored (kept for API compatibility)."""
    html = (
        f'<div class="mini-card"{_tt(tooltip)}>'
        f'<div class="mini-content">'
        f'<div class="mini-label">{label}</div>'
        f'<div class="mini-value">{value}</div>'
        f'</div>'
        f'</div>'
    )
    st.markdown(html, unsafe_allow_html=True)


def compare_card(label, current, previous, delta_text, delta_up=True, tooltip=None):
    """Render a comparison card: current -> previous with delta."""
    cls = "up" if delta_up else "down"
    html = (
        f'<div class="compare-card"{_tt(tooltip)}>'
        f'<div class="compare-label">{label}</div>'
        f'<span class="compare-main">{current}</span>'
        f'<span class="compare-arrow">&rarr;</span>'
        f'<span class="compare-prev">{previous}</span>'
        f'<span class="compare-delta {cls}">{delta_text}</span>'
        f'</div>'
    )
    st.markdown(html, unsafe_allow_html=True)


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


def section_card_header(title, subtitle=None, tooltip=None):
    """Render a section card header inside a st.container(border=True)."""
    tooltip_html = ""
    if tooltip:
        tooltip_html = f'<span class="tooltip-icon" data-tooltip="{html_mod.escape(tooltip)}">i</span>'
    sub = f'<div class="section-card-subtitle">{subtitle}</div>' if subtitle else ""
    st.markdown(f"""<div class="section-card-title">{title}{tooltip_html}</div>
        {sub}
        <div style="border-bottom: 1px solid var(--hairline); margin-bottom: var(--s-3);"></div>""", unsafe_allow_html=True)


def alert_banner(message, alert_type="amber", tooltip=None):
    st.markdown(f'<div class="alert-banner alert-{alert_type}"{_tt(tooltip)}>{message}</div>', unsafe_allow_html=True)


def risk_card(title, description, risk_type="danger", tooltip=None):
    cls = "warning" if risk_type == "warning" else ""
    st.markdown(f"""
    <div class="risk-card {cls}"{_tt(tooltip)}>
        <div class="risk-title">{title}</div>
        <div class="risk-desc">{description}</div>
    </div>""", unsafe_allow_html=True)


def _risk_type(r):
    """Read the severity type out of a risk record. Risks may be dicts ({'type': ...})
    or tuples (title, desc, type). Returns 'warning' / 'danger' / 'info' / None."""
    if isinstance(r, dict):
        return r.get("type")
    if isinstance(r, (tuple, list)) and len(r) >= 3:
        return r[2]
    return None


def _max_severity(risks):
    """Return the highest severity present: 'danger' > 'warning' > 'info' > 'clear'."""
    if not risks:
        return "clear"
    types = {_risk_type(r) for r in risks}
    if "danger" in types:
        return "danger"
    if "warning" in types:
        return "warning"
    if "info" in types:
        return "info"
    return "clear"


def severity_badge(count, severity):
    """Return HTML for a count pill colored by severity. Single source of truth
    so global_alert_strip and risk_section_header can never disagree."""
    if count <= 0 or severity == "clear":
        return f'<span class="risk-count-badge clear">{max(count, 0)}</span>'
    if severity == "warning":
        return f'<span class="risk-count-badge warning">{count}</span>'
    return f'<span class="risk-count-badge">{count}</span>'


def risk_section_header(title, count=0, severity="danger", risks=None):
    """Render a risk section header with count badge.
    Either pass `count` + `severity` directly, or pass `risks` and let the helper
    derive both. Passing `risks` is preferred for new code.
    """
    if risks is not None:
        count = len(risks)
        severity = _max_severity(risks)
    badge_html = severity_badge(count, severity)
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


def insight_card(message, insight_type="info", tooltip=None):
    st.markdown(f'<div class="insight-card insight-{insight_type}"{_tt(tooltip)}>{message}</div>', unsafe_allow_html=True)


def badge(text, badge_type="green"):
    return f'<span class="badge badge-{badge_type}">{text}</span>'


def concentration_bar(segments):
    """Render a concentration bar. segments = [(label, pct, color), ...]"""
    parts = ""
    for label, pct, color in segments:
        parts += f'<div class="seg" style="width:{pct}%;background:{color};">{label}</div>'
    st.markdown(f'<div class="conc-bar">{parts}</div>', unsafe_allow_html=True)


def styled_table(headers, rows, green_cols=None, red_cols=None, row_classes=None, num_cols=None):
    """Render a styled HTML table matching dark theme.
    num_cols: list of column indices to render as right-aligned tabular numbers."""
    green_cols = green_cols or []
    red_cols = red_cols or []
    row_classes = row_classes or []
    num_cols = num_cols or []

    th_parts = []
    for i, h in enumerate(headers):
        th_cls = ' class="num"' if i in num_cols else ""
        th_parts.append(f"<th{th_cls}>{h}</th>")
    th = "".join(th_parts)

    tbody = ""
    for ri, row in enumerate(rows):
        row_cls = f' class="{row_classes[ri]}"' if ri < len(row_classes) and row_classes[ri] else ""
        tds = ""
        for i, cell in enumerate(row):
            classes = []
            if i in num_cols:
                classes.append("num")
            if i in red_cols:
                classes.append("val-red")
            elif i in green_cols:
                classes.append("val-green")
            cls = f' class="{" ".join(classes)}"' if classes else ""
            tds += f"<td{cls}>{cell}</td>"
        tbody += f"<tr{row_cls}>{tds}</tr>"
    st.markdown(f"""
    <table class="styled-table">
        <thead><tr>{th}</tr></thead>
        <tbody>{tbody}</tbody>
    </table>""", unsafe_allow_html=True)


def top_bar(data_date, current_time, freshness_hours=None, compute_ms=None):
    """Render the top data timestamp bar with freshness indicator."""
    fresh_html = ""
    if freshness_hours is not None:
        if freshness_hours < 24:
            fresh_html = '<span class="freshness-badge freshness-fresh"><span class="freshness-dot"></span>Fresh</span>'
        else:
            days = int(freshness_hours // 24)
            fresh_html = f'<span class="freshness-badge freshness-stale">{days}d old</span>'

    compute_html = ""
    if compute_ms is not None:
        compute_html = f'<span class="top-bar-compute">{compute_ms}ms</span>'

    html = (
        f'<div class="top-bar">'
        f'<div class="top-bar-left"><span>Data as of <strong style="color: var(--text-primary);">{data_date}</strong></span>{fresh_html}</div>'
        f'<div class="top-bar-right"><span>{current_time}</span>{compute_html}</div>'
        f'</div>'
    )
    st.markdown(html, unsafe_allow_html=True)


# --- NEW COMPONENTS ---

def empty_state(message="No data matches the current filters.", sub_text="Try adjusting your date range or filter criteria."):
    """Render an empty state placeholder when filters return no results."""
    html = (
        f'<div class="empty-state">'
        f'<div class="empty-state-message">{message}</div>'
        f'<div class="empty-state-sub">{sub_text}</div>'
        f'</div>'
    )
    st.markdown(html, unsafe_allow_html=True)


def scroll_to_top_button():
    """Render a floating scroll-to-top button that fades in after scrolling.
    Arrow is drawn with CSS (transformed borders) — no glyph."""
    html = (
        '<a href="#" id="scroll-top-btn-el" class="scroll-top-btn" '
        'onclick="window.scrollTo({top:0,behavior:\'smooth\'});return false;" '
        'aria-label="Scroll to top"><span class="scroll-top-chevron"></span></a>'
        '<script>'
        '(function() {'
        '  var btn = document.getElementById(\'scroll-top-btn-el\');'
        '  if (!btn || window._scrollTopBound) return;'
        '  window._scrollTopBound = true;'
        '  var scrollTarget = window.parent || window;'
        '  function onScroll() {'
        '    var y = scrollTarget.scrollY || scrollTarget.document.documentElement.scrollTop || 0;'
        '    if (y > 400) btn.classList.add(\'visible\');'
        '    else btn.classList.remove(\'visible\');'
        '  }'
        '  try { scrollTarget.addEventListener(\'scroll\', onScroll, { passive: true }); } catch(e) {}'
        '  window.addEventListener(\'scroll\', onScroll, { passive: true });'
        '  onScroll();'
        '})();'
        '</script>'
    )
    st.markdown(html, unsafe_allow_html=True)


def executive_summary_panel(insights):
    """Render an executive summary panel with auto-generated insights."""
    if not insights:
        return
    items = "".join(f"<li>{i}</li>" for i in insights)
    html = (
        f'<div class="exec-summary">'
        f'<div class="exec-summary-title">Key Insights</div>'
        f'<ul class="exec-summary-list">{items}</ul>'
        f'</div>'
    )
    st.markdown(html, unsafe_allow_html=True)


def global_alert_strip(risks):
    """Render a thin alert strip showing global risk count. Color is derived via
    _max_severity(risks) so this and risk_section_header always agree."""
    if not risks:
        return
    danger_count = sum(1 for r in risks if _risk_type(r) == "danger")
    warning_count = sum(1 for r in risks if _risk_type(r) == "warning")
    total = len(risks)

    parts = []
    if danger_count:
        parts.append(f"{danger_count} critical")
    if warning_count:
        parts.append(f"{warning_count} warning")
    text = ", ".join(parts)

    severity = _max_severity(risks)
    if severity == "warning":
        strip_cls = "alert-strip alert-strip-warning"
        count_cls = "alert-strip-count alert-strip-count-warning"
    else:
        strip_cls = "alert-strip"
        count_cls = "alert-strip-count"

    html = (
        f'<div class="{strip_cls}">'
        f'<span class="{count_cls}">{total}</span>'
        f'Active alerts: {text} &mdash; check Executive Dashboard for details'
        f'</div>'
    )
    st.markdown(html, unsafe_allow_html=True)


def render_breadcrumb(items):
    """Render a breadcrumb trail. items = [("Label", "page_id_or_None"), ...]
    page_id: "app" for home, else the file slug (e.g. "1_Revenue_Sales")."""
    parts = []
    for label, path in items:
        if path:
            # Streamlit strips leading number+underscore; home is "/"
            if path == "app":
                href = "/"
            else:
                slug = path.split("_", 1)[1] if path[0].isdigit() else path
                href = f"/{slug}"
            parts.append(f'<a href="{href}" target="_self" class="bc-link">{label}</a>')
        else:
            parts.append(f'<span class="bc-current">{label}</span>')
    sep = '<span class="bc-sep">/</span>'
    st.markdown(f'<div class="breadcrumb">{sep.join(parts)}</div>', unsafe_allow_html=True)


def glossary_panel(definitions):
    """Render a collapsible metric definitions glossary."""
    with st.expander("Metric Definitions", expanded=False):
        html_items = ""
        for name, info in definitions.items():
            threshold_html = ""
            if info.get("threshold"):
                threshold_html = f'<div class="glossary-threshold">{info["threshold"]}</div>'
            html_items += f"""
            <div class="glossary-item">
                <div class="glossary-name">{name}</div>
                <div class="glossary-formula">{info["formula"]}</div>
                <div class="glossary-desc">{info["description"]}</div>
                {threshold_html}
            </div>"""
        st.markdown(f'<div class="glossary-grid">{html_items}</div>', unsafe_allow_html=True)


def action_button_row():
    """Render quick action buttons on the Executive Dashboard."""
    cols = st.columns(4)
    with cols[0]:
        st.page_link("pages/4_Customer_Reconnection.py", label="View At-Risk Customers", use_container_width=True)
    with cols[1]:
        st.page_link("pages/1_Revenue_Sales.py", label="Drill Into Revenue", use_container_width=True)
    with cols[2]:
        st.page_link("pages/5_Sales_Intelligence.py", label="Compare Q1 Performance", use_container_width=True)
    with cols[3]:
        st.page_link("pages/6_Data_Explorer.py", label="Explore Raw Data", use_container_width=True)


def _sparkline_svg(values, width=70, height=22, color=None, stroke_width=1.5):
    """Inline SVG sparkline. Direction is communicated by the delta pill — the line
    itself stays neutral (fg-2) by default. Hero sparkline passes the accent color."""
    if not values or len(values) < 2:
        return ""
    v_min = min(values)
    v_max = max(values)
    v_range = v_max - v_min if v_max != v_min else 1
    pad = 2
    w = width - 2 * pad
    h = height - 2 * pad
    n = len(values)
    points = []
    for i, v in enumerate(values):
        x = pad + (i / (n - 1)) * w
        y = pad + h - ((v - v_min) / v_range) * h
        points.append(f"{x:.1f},{y:.1f}")
    pts = " ".join(points)

    stroke = color if color else "#8A8F98"

    return f"""<div class="kpi-sparkline"><svg width="{width}" height="{height}" viewBox="0 0 {width} {height}">
        <polyline points="{pts}" fill="none" stroke="{stroke}" stroke-width="{stroke_width}" stroke-linecap="round" stroke-linejoin="round"/>
    </svg></div>"""
