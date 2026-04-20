"""Single source of truth for design tokens and the full CSS string.

Tokens are values; inject_css(mode) returns the <style>...</style> block
to drop into st.markdown(unsafe_allow_html=True).
"""
from typing import Literal

Mode = Literal["light", "dark"]

_BRAND_GOLD = "#FFC907"
_BRAND_GREEN = "#2d8a3e"
_DANGER = "#dc2626"

_LIGHT = {
    "bg_page": "#f5f5f7",
    "bg_surface": "#ffffff",
    "bg_subtle": "#fafafa",
    "border": "#ececec",
    "border_input": "#d2d2d7",
    "text_primary": "#111111",
    "text_muted": "#888888",
    "text_secondary": "#666666",
    "brand_gold": _BRAND_GOLD,
    "brand_green": _BRAND_GREEN,
    "danger": _DANGER,
    "tab_active_bg": _BRAND_GREEN,
    "tab_active_fg": "#ffffff",
    "hero_tint": "linear-gradient(180deg,#f0faf2 0%,#ffffff 100%)",
    "shadow_hover": "0 4px 12px rgba(0,0,0,0.04)",
    "focus_ring": "0 0 0 3px rgba(45,138,62,0.15)",
    "btn_primary_bg": _BRAND_GOLD,
    "btn_primary_fg": "#000000",
    "btn_primary_hover": "#f0bb00",
    "link_fg": "#0066cc",
    "danger_border": "#fecaca",
    "_plotly_template": "plotly_white",
}

_DARK = {
    "bg_page": "#000000",
    "bg_surface": "#1c1c1e",
    "bg_subtle": "#2c2c2e",
    "border": "#2c2c2e",
    "border_input": "#3a3a3c",
    "text_primary": "#ffffff",
    "text_muted": "#888888",
    "text_secondary": "#aaaaaa",
    "brand_gold": _BRAND_GOLD,
    "brand_green": _BRAND_GREEN,
    "danger": _DANGER,
    "tab_active_bg": _BRAND_GREEN,
    "tab_active_fg": "#ffffff",
    "hero_tint": "linear-gradient(180deg,#0f1f12 0%,#1c1c1e 100%)",
    "shadow_hover": "0 4px 12px rgba(0,0,0,0.5)",
    "focus_ring": "0 0 0 3px rgba(45,138,62,0.25)",
    "btn_primary_bg": _BRAND_GOLD,
    "btn_primary_fg": "#000000",
    "btn_primary_hover": "#f0bb00",
    "link_fg": "#7fbfff",
    "danger_border": "#7a1d1d",
    "_plotly_template": "plotly_dark",
}


def get_theme(mode: Mode) -> dict:
    if mode == "light":
        return dict(_LIGHT)
    if mode == "dark":
        return dict(_DARK)
    raise ValueError(f"Unknown theme mode: {mode!r}")


_FONT_UI = "-apple-system, 'SF Pro Text', 'Inter', system-ui, sans-serif"
_FONT_SERIF = "Georgia, 'Times New Roman', serif"


def inject_css(mode: Mode) -> str:
    """Return a <style>...</style> block for the chosen mode.

    Includes:
      - CSS custom properties for every token
      - Streamlit chrome overrides (hide sidebar, toolbar, footer)
      - Component classes (.tx-topbar, .tx-tabs, .tx-card, .tx-kpi, .tx-btn-*, etc.)
      - Keyframes and transitions, gated by prefers-reduced-motion
    """
    t = get_theme(mode)
    return f"""<style>
:root {{
  --bg-page: {t['bg_page']};
  --bg-surface: {t['bg_surface']};
  --bg-subtle: {t['bg_subtle']};
  --border: {t['border']};
  --border-input: {t['border_input']};
  --text-primary: {t['text_primary']};
  --text-muted: {t['text_muted']};
  --text-secondary: {t['text_secondary']};
  --brand-gold: {t['brand_gold']};
  --brand-green: {t['brand_green']};
  --danger: {t['danger']};
  --tab-active-bg: {t['tab_active_bg']};
  --tab-active-fg: {t['tab_active_fg']};
  --hero-tint: {t['hero_tint']};
  --shadow-hover: {t['shadow_hover']};
  --focus-ring: {t['focus_ring']};
  --btn-primary-bg: {t['btn_primary_bg']};
  --btn-primary-fg: {t['btn_primary_fg']};
  --btn-primary-hover: {t['btn_primary_hover']};
  --link-fg: {t['link_fg']};
  --danger-border: {t['danger_border']};
  --font-ui: {_FONT_UI};
  --font-serif: {_FONT_SERIF};
  --ease-out: cubic-bezier(0.16, 1, 0.3, 1);
  --ease-spring: cubic-bezier(0.32, 0.72, 0, 1);
}}

/* ===== Streamlit chrome ===== */
html, body, [data-testid="stAppViewContainer"] {{
  background: var(--bg-page) !important;
  color: var(--text-primary) !important;
  font-family: var(--font-ui) !important;
  transition: background 200ms ease, color 200ms ease;
}}
section[data-testid="stSidebar"], header[data-testid="stHeader"], footer {{ display: none !important; }}
[data-testid="stToolbar"] {{ display: none !important; }}
.block-container {{
  padding-top: 0.75rem !important;
  max-width: 1200px !important;
  animation: tx-page-in 220ms var(--ease-out);
}}

/* ===== Topbar ===== */
.tx-topbar {{
  display: flex; align-items: center; justify-content: space-between;
  padding: 10px 14px; background: var(--bg-surface);
  border: 1px solid var(--border); border-radius: 12px;
  margin-bottom: 12px;
}}
.tx-brand {{
  display: flex; align-items: center; gap: 8px;
  font-family: var(--font-serif); font-weight: 700; font-size: 16px;
  letter-spacing: 0.02em; color: var(--text-primary);
}}
.tx-leaf {{
  width: 16px; height: 10px; background: var(--brand-gold);
  border-radius: 50% 50% 50% 0; transform: rotate(-25deg); display: inline-block;
}}
.tx-topright {{ display: flex; align-items: center; gap: 10px; }}
.tx-toggle {{
  display: inline-flex; background: var(--bg-page); border: 1px solid var(--border);
  border-radius: 99px; padding: 2px;
}}
.tx-toggle a {{
  padding: 4px 10px; font-size: 11px; border-radius: 99px;
  color: var(--text-secondary); text-decoration: none;
}}
.tx-toggle a.on {{
  background: var(--bg-surface); color: var(--text-primary);
  box-shadow: 0 1px 2px rgba(0,0,0,0.06);
}}

/* ===== Tab strip ===== */
.tx-tabs {{
  display: flex; gap: 2px; background: var(--bg-surface);
  border: 1px solid var(--border); border-radius: 12px; padding: 6px;
  margin-bottom: 12px; overflow-x: auto;
}}
.tx-tab {{
  padding: 7px 12px; font-size: 12px; color: var(--text-secondary);
  border-radius: 8px; text-decoration: none; white-space: nowrap;
  transition: background 100ms ease, color 100ms ease;
}}
.tx-tab:hover {{ background: var(--bg-page); }}
.tx-tab.on {{ background: var(--tab-active-bg); color: var(--tab-active-fg); font-weight: 500; }}

/* ===== Cards / KPIs ===== */
.tx-card {{
  background: var(--bg-surface); border: 1px solid var(--border);
  border-radius: 12px; padding: 14px;
  transition: transform 120ms ease, box-shadow 120ms ease;
}}
.tx-card:hover {{ transform: translateY(-1px); box-shadow: var(--shadow-hover); }}
.tx-kpi {{ position: relative; overflow: hidden; }}
.tx-kpi .lbl {{ font-size: 10px; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.06em; }}
.tx-kpi .val {{ font-size: 22px; font-weight: 600; margin-top: 4px; letter-spacing: -0.01em; font-variant-numeric: tabular-nums; }}
.tx-kpi .delta {{ font-size: 11px; margin-top: 2px; }}
.tx-kpi .delta.up {{ color: var(--brand-green); font-weight: 600; }}
.tx-kpi .delta.down {{ color: var(--danger); }}
.tx-kpi.hero {{ background: var(--hero-tint); }}
.tx-kpi.hero::before {{ content: ''; position: absolute; left: 0; top: 0; bottom: 0; width: 3px; background: var(--brand-green); }}
.tx-kpi.warn::before {{ content: ''; position: absolute; left: 0; top: 0; bottom: 0; width: 3px; background: var(--brand-gold); }}

/* ===== Tables ===== */
.tx-table {{ background: var(--bg-surface); border: 1px solid var(--border); border-radius: 12px; overflow: hidden; }}
.tx-table table {{ width: 100%; border-collapse: collapse; font-size: 12px; }}
.tx-table th {{
  text-align: left; padding: 8px 12px; background: var(--bg-subtle);
  color: var(--text-muted); font-weight: 500; font-size: 10px;
  text-transform: uppercase; letter-spacing: 0.05em; border-bottom: 1px solid var(--border);
}}
.tx-table td {{ padding: 8px 12px; border-top: 1px solid var(--border); color: var(--text-primary); }}
.tx-table tr:first-child td {{ border-top: 0; }}
.tx-table tr:hover td {{ background: var(--bg-subtle); }}

/* ===== Buttons ===== */
.tx-btn {{
  display: inline-block; padding: 8px 16px; font-family: var(--font-ui);
  font-size: 12px; font-weight: 500; border-radius: 8px; cursor: pointer;
  border: 1px solid transparent; text-decoration: none; transition: background 100ms ease;
}}
.tx-btn-primary {{ background: var(--btn-primary-bg); color: var(--btn-primary-fg); font-weight: 600; }}
.tx-btn-primary:hover {{ background: var(--btn-primary-hover); }}
.tx-btn-secondary {{ background: var(--bg-surface); color: var(--text-primary); border-color: var(--border-input); }}
.tx-btn-secondary:hover {{ background: var(--bg-subtle); }}
.tx-btn-ghost {{ background: transparent; color: var(--link-fg); }}
.tx-btn-danger {{ background: var(--bg-surface); color: var(--danger); border-color: var(--danger-border); }}
.tx-btn-icon {{ padding: 7px; background: var(--bg-subtle); border-color: var(--border); }}

/* ===== Streamlit native button override (so st.button matches secondary) ===== */
[data-testid="stButton"] > button {{
  background: var(--bg-surface) !important; color: var(--text-primary) !important;
  border: 1px solid var(--border-input) !important; border-radius: 8px !important;
  font-family: var(--font-ui) !important; font-size: 12px !important; font-weight: 500 !important;
  padding: 8px 16px !important; transition: background 100ms ease;
}}
[data-testid="stButton"] > button:hover {{ background: var(--bg-subtle) !important; }}
[data-testid="stButton"] > button:focus {{ box-shadow: var(--focus-ring) !important; outline: none !important; }}

/* ===== Inputs ===== */
[data-baseweb="input"] input, [data-baseweb="select"] {{
  background: var(--bg-surface) !important; color: var(--text-primary) !important;
  border-radius: 8px !important;
}}
[data-baseweb="input"] {{ border-color: var(--border-input) !important; }}

/* ===== Badges ===== */
.tx-badge {{ display: inline-block; padding: 2px 8px; border-radius: 99px; font-size: 10px; font-weight: 600; }}
.tx-badge.gold {{ background: var(--brand-gold); color: #000; }}
.tx-badge.green {{ background: rgba(45,138,62,0.10); color: var(--brand-green); border: 1px solid var(--brand-green); }}
.tx-badge.muted {{ background: var(--bg-page); color: var(--text-secondary); }}

/* ===== Section titles + breadcrumbs ===== */
.tx-section-title {{ font-size: 15px; font-weight: 600; margin: 16px 0 8px; letter-spacing: -0.01em; }}
.tx-breadcrumb {{ font-size: 11px; color: var(--text-muted); }}
.tx-breadcrumb b {{ color: var(--text-primary); font-weight: 500; }}

/* ===== Filter chips (active filter pills from filters.py) ===== */
.filter-chips-row {{
  display: flex; flex-wrap: wrap; gap: 6px;
  margin-top: 6px; margin-bottom: 6px;
}}
.filter-chip {{
  display: inline-flex; align-items: center; gap: 4px;
  padding: 3px 10px; background: rgba(45,138,62,0.10);
  border: 1px solid var(--brand-green); border-radius: 99px;
  font-size: 11px; color: var(--brand-green);
  font-family: var(--font-ui); font-weight: 500;
  white-space: nowrap; transition: background 100ms ease;
}}
.filter-chip:hover {{ background: rgba(45,138,62,0.18); }}

/* ===== Login screen ===== */
.tx-login-bg {{ background: var(--bg-page); padding: 60px 0; min-height: 70vh; display: flex; align-items: center; justify-content: center; }}
.tx-login-panel {{
  width: 100%; max-width: 320px; background: var(--bg-surface);
  border: 1px solid var(--border); border-radius: 14px;
  padding: 32px 28px; text-align: center;
  box-shadow: 0 4px 20px rgba(0,0,0,0.04);
}}

/* ===== Loading screen ===== */
.tx-loading-overlay {{
  position: fixed; inset: 0; background: var(--bg-page); z-index: 9999;
  display: flex; flex-direction: column; align-items: center; justify-content: center;
  animation: tx-fade-in 200ms ease;
}}
.tx-loading-bar {{
  width: 240px; height: 2px; background: var(--bg-subtle); border-radius: 99px;
  margin-top: 24px; overflow: hidden; position: relative;
}}
.tx-loading-bar::after {{
  content: ''; position: absolute; left: -40%; top: 0; bottom: 0; width: 40%;
  background: var(--brand-green); border-radius: 99px;
  animation: tx-loading-slide 1.4s ease-in-out infinite;
}}
@keyframes tx-loading-slide {{ 0% {{ left: -40%; }} 100% {{ left: 100%; }} }}

/* ===== Skeleton shimmer ===== */
.tx-skeleton {{
  background: linear-gradient(90deg, var(--bg-subtle) 0%, var(--border) 50%, var(--bg-subtle) 100%);
  background-size: 200% 100%; animation: tx-shimmer 1.6s linear infinite;
  border-radius: 8px;
}}
@keyframes tx-shimmer {{ 0% {{ background-position: 200% 0; }} 100% {{ background-position: -200% 0; }} }}

/* ===== Page transition ===== */
@keyframes tx-page-in {{ from {{ opacity: 0; transform: translateY(4px); }} to {{ opacity: 1; transform: translateY(0); }} }}
@keyframes tx-fade-in {{ from {{ opacity: 0; }} to {{ opacity: 1; }} }}

/* ===== Reduced motion guard ===== */
@media (prefers-reduced-motion: reduce) {{
  *, *::before, *::after {{
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
  }}
}}
</style>"""


def normalize_mode(value) -> str:
    """Coerce any value into 'light' or 'dark'. Default 'light'."""
    if value in ("light", "dark"):
        return value
    return "light"


def toggle_mode(mode: str) -> str:
    return "dark" if normalize_mode(mode) == "light" else "light"


def current_theme() -> str:
    """Read current theme from Streamlit session_state, default 'light'.

    Reads ?theme= query param on first call to support cross-page persistence.
    Updates session_state from query param. Subsequent calls just read state.
    """
    import streamlit as st
    if "theme" not in st.session_state:
        try:
            qp = st.query_params.get("theme")
        except Exception:
            qp = None
        st.session_state["theme"] = normalize_mode(qp)
    return st.session_state["theme"]


def set_theme(mode: str) -> None:
    import streamlit as st
    mode = normalize_mode(mode)
    st.session_state["theme"] = mode
    try:
        st.query_params["theme"] = mode
    except Exception:
        pass
