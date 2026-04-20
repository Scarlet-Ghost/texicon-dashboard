import streamlit as st
import html as html_mod


def _tt(tooltip):
    """Return data-tooltip attribute string if tooltip is provided."""
    if tooltip:
        return f' data-tooltip="{html_mod.escape(tooltip)}"'
    return ""


# --- Page Navigation Mapping (role-aware) ---
_NAV_PAGES_OWNER = [
    ("Executive", "app"),
    ("Revenue", "1_Revenue_Sales"),
    ("Cash", "2_Cash_Collections"),
    ("Operations", "3_Operations_Delivery"),
    ("Reconnect", "4_Customer_Reconnection"),
    ("Intel", "5_Sales_Intelligence"),
    ("Data", "6_Data_Explorer"),
]

_NAV_PAGES_SALES = [
    ("Sales Home", "0_Sales_Home"),
    ("Reconnect", "4_Customer_Reconnection"),
    ("Intel", "5_Sales_Intelligence"),
]


def _nav_pages_for_role(role):
    if role == "sales":
        return _NAV_PAGES_SALES
    return _NAV_PAGES_OWNER


def render_nav(active_page="app", risk_count=0, role=None):
    """Render the top navigation bar, filtered by role.

    `role` — "owner" | "sales" | None. If None, defaults to owner nav.
    `risk_count` — accepted for signature compatibility; not rendered as a badge.
    """
    pages = _nav_pages_for_role(role)
    with st.container(border=False):
        cols = st.columns([1] * len(pages))
        for i, (label, page_id) in enumerate(pages):
            with cols[i]:
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


def styled_table(headers, rows, title: str = "",
                 actions_html: str = "",
                 green_cols=None, red_cols=None,
                 row_classes=None, num_cols=None):
    """Render a styled table card.

    headers: list[str]
    rows: list[list[str]]  (already-formatted cells; HTML allowed)
    title: optional header label above the table
    actions_html: optional HTML for right-side action buttons in the header
    green_cols: column indices whose cells get brand-green styling
    red_cols: column indices whose cells get danger-red styling
    num_cols: column indices that should right-align + tabular-nums (header + cells)
    row_classes: optional list[str] — one class per row
    """
    import streamlit as st
    green_set = set(green_cols or [])
    red_set = set(red_cols or [])
    num_set = set(num_cols or [])

    def _th(i, h):
        style = 'text-align:right;font-variant-numeric:tabular-nums;' if i in num_set else ''
        return f'<th style="{style}">{h}</th>' if style else f'<th>{h}</th>'

    head_row = "".join(_th(i, h) for i, h in enumerate(headers))

    def _td(i, c):
        styles = []
        if i in num_set:
            styles.append('text-align:right')
            styles.append('font-variant-numeric:tabular-nums')
        if i in green_set:
            styles.append('color:var(--brand-green)')
            styles.append('font-weight:600')
        elif i in red_set:
            styles.append('color:var(--danger)')
            styles.append('font-weight:600')
        style_attr = f' style="{";".join(styles)}"' if styles else ''
        return f'<td{style_attr}>{c}</td>'

    body_rows_list = []
    for ri, r in enumerate(rows):
        cls = ""
        if row_classes and ri < len(row_classes) and row_classes[ri]:
            cls = f' class="{row_classes[ri]}"'
        cells = "".join(_td(i, c) for i, c in enumerate(r))
        body_rows_list.append(f'<tr{cls}>{cells}</tr>')
    body_rows = "".join(body_rows_list)

    header_html = (
        f'<div style="padding:10px 14px;font-size:12px;font-weight:600;'
        f'border-bottom:1px solid var(--border);'
        f'display:flex;justify-content:space-between;align-items:center;">'
        f'<span>{title}</span><div style="display:flex;gap:6px;">{actions_html}</div>'
        f'</div>'
    ) if (title or actions_html) else ""

    st.markdown(
        f'<div class="tx-card tx-table" style="padding:0;">'
        f'{header_html}'
        f'<table><thead><tr>{head_row}</tr></thead>'
        f'<tbody>{body_rows}</tbody></table>'
        f'</div>',
        unsafe_allow_html=True,
    )


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
        f'<span class="{count_cls}">{total}</span> '
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


# ===== New v9 redesign helpers =====
# Note: nav page lists are defined at module top (_NAV_PAGES_OWNER/_NAV_PAGES_SALES)
# using Streamlit page IDs — navigation goes through st.page_link to preserve
# session state (raw <a> links drop the WebSocket session and log users out).


def top_bar_html(theme: str, role_label: str = "", primary_action: str = "") -> str:
    """Topbar HTML: serif TEXICON wordmark, role chip, optional action.

    The theme toggle is NOT rendered here. render_top_bar (below) emits a
    session-preserving st.button separately — a plain <a href="?theme=..."> in
    the topbar HTML would reload the page and drop Streamlit's WebSocket
    session, logging the user out.

    (The ``theme`` parameter is retained for the ``.tx-toggle`` data hook so
    existing tests and any legacy callers don't break.)
    """
    _ = theme  # reserved for future visual treatments
    role_chip = (
        f'<span class="tx-badge muted" style="margin-right:6px;">{role_label}</span>'
        if role_label else ""
    )
    return (
        '<div class="tx-topbar">'
        '<div class="tx-brand">TEXICON<span class="tx-leaf"></span></div>'
        '<div class="tx-topright">'
        f'{role_chip}'
        f'{primary_action}'
        '</div>'
        '</div>'
    )


def _label_to_page_id(label: str, role: str) -> str:
    """Map a human label ('Revenue') to a nav page_id ('1_Revenue_Sales')."""
    pages = _NAV_PAGES_SALES if role == "sales" else _NAV_PAGES_OWNER
    for l, pid in pages:
        if l == label:
            return pid
    return label


def badge_html(text: str, variant: str = "muted") -> str:
    if variant not in ("gold", "green", "muted"):
        variant = "muted"
    return f'<span class="tx-badge {variant}">{text}</span>'


def breadcrumb_html(parts: list) -> str:
    if not parts:
        return ""
    head = f"<b>{parts[0]}</b>"
    tail = " · ".join(parts[1:])
    sep = " · " if tail else ""
    return f'<div class="tx-breadcrumb">{head}{sep}{tail}</div>'


def render_top_bar(active_page: str):
    """Streamlit wrapper: read theme + role, emit topbar + nav. Call at top of every page.

    `active_page` accepts either a label ('Revenue') or page_id ('1_Revenue_Sales').
    Nav uses st.page_link to preserve session state across navigation.
    Theme toggle uses a hidden st.button overlaying the visual toggle — a
    plain <a href="?theme=..."> would reload the page and drop session_state.
    """
    import streamlit as st
    try:
        from components.theme import current_theme, set_theme
        from components.auth import current_role
    except ModuleNotFoundError:
        from dashboard.components.theme import current_theme, set_theme
        from dashboard.components.auth import current_role
    role = current_role() or "owner"
    role_label = "Owner" if role == "owner" else "Sales"
    theme = current_theme()
    st.markdown(top_bar_html(theme=theme, role_label=role_label),
                unsafe_allow_html=True)

    # Log out button — CSS-positioned into the topbar card (right side).
    st.markdown('<div class="tx-logout-slot">', unsafe_allow_html=True)
    if st.button("Log out", key=f"topbar_logout_{active_page}"):
        st.session_state.clear()
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

    page_id = _label_to_page_id(active_page, role)
    render_nav(active_page=page_id, risk_count=0, role=role)

    # Theme toggle — fixed bottom-left FAB. Session-preserving st.button
    # (a plain <a href="?theme="> would drop the WebSocket and log users out).
    other = "dark" if theme == "light" else "light"
    label = "☾ Dark" if theme == "light" else "☀ Light"
    st.markdown('<div class="tx-theme-fab">', unsafe_allow_html=True)
    if st.button(label, key=f"theme_toggle_{active_page}"):
        set_theme(other)
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)


def kpi_card_html(label: str, value: str, delta: str = "",
                  delta_dir: str = "neutral", numeric_target: float = None,
                  prefix: str = "", suffix: str = "",
                  variant: str = "default") -> str:
    """Render a single KPI card.

    variant: 'default' | 'hero' | 'warn' (controls left stripe + bg tint)
    delta_dir: 'up' | 'down' | 'neutral'
    numeric_target: if provided, animate count-up; otherwise render value as-is.
    """
    try:
        from components.motion import count_up_value
    except ModuleNotFoundError:
        from dashboard.components.motion import count_up_value
    cls_extra = " hero" if variant == "hero" else (" warn" if variant == "warn" else "")
    if numeric_target is not None:
        val_html = count_up_value(label, value, numeric_target, prefix, suffix)
    else:
        val_html = f'<span class="tx-kpi-val">{value}</span>'
    delta_class = delta_dir if delta_dir in ("up", "down") else ""
    delta_html = f'<div class="delta {delta_class}">{delta}</div>' if delta else ""
    return (
        f'<div class="tx-card tx-kpi{cls_extra}">'
        f'<div class="lbl">{label}</div>'
        f'<div class="val">{val_html}</div>'
        f'{delta_html}'
        '</div>'
    )


def kpi_row_html(cards: list) -> str:
    """Render a horizontal grid of kpi_card_html strings."""
    n = len(cards) or 1
    return (
        f'<div style="display:grid;grid-template-columns:repeat({n},1fr);'
        f'gap:8px;margin-bottom:12px;">'
        + "".join(cards)
        + '</div>'
    )
