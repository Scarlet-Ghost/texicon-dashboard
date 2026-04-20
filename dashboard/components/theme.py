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
  /* Typography scale — TEXT */
  --fs-display: 28px;
  --fs-h1:      20px;
  --fs-h2:      15px;
  --fs-eyebrow: 11px;
  --fs-body:    13px;
  --fs-caption: 12px;
  --fs-micro:   11px;
  /* Typography scale — NUMERIC VALUES (KPIs) */
  --fv-hero:    36px;
  --fv-lg:      22px;
  --fv-md:      16px;
  /* Weights */
  --fw-bold:     700;
  --fw-semibold: 600;
  --fw-medium:   500;
  --fw-regular:  400;
  /* Letter-spacing */
  --ls-eyebrow: 0.06em;
  --ls-tight:  -0.01em;
  --ls-display:-0.02em;
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
/* Legacy .tx-topbar (kept for top_bar_html fallback callers) */
.tx-topbar {{
  display: flex; align-items: center; justify-content: space-between;
  padding: 14px 20px; background: var(--bg-surface);
  border: 1px solid var(--border); border-radius: 12px;
  margin-bottom: 12px; position: relative;
}}
.tx-brand {{
  display: inline-flex; align-items: center; gap: 10px;
  font-family: var(--font-serif); font-weight: var(--fw-medium); font-size: var(--fs-h1);
  letter-spacing: 0.03em; color: var(--text-primary);
}}
.tx-leaf {{
  width: 18px; height: 11px; background: var(--brand-gold);
  border-radius: 50% 50% 50% 0; transform: rotate(-25deg); display: inline-block;
}}
.tx-topright {{ display: flex; align-items: center; gap: 10px; }}
.tx-topright .tx-badge {{ font-size: 11px; padding: 4px 10px; }}

/* New topbar: real st.container holding brand + role chip + theme + logout.
   Targeted via :has(.tx-brand-row) so only this specific vertical block
   becomes the topbar card; other containers keep their native layout. */
[data-testid="stVerticalBlock"]:has(> [data-testid="stHorizontalBlock"] .tx-brand-row) {{
  background: var(--bg-surface); border: 1px solid var(--border);
  border-radius: 12px; padding: 10px 16px; margin-bottom: 12px;
}}
.tx-brand-row {{
  display: flex; align-items: center; gap: 12px;
  min-height: 36px;
}}
.tx-role-chip {{
  display: inline-block; padding: 3px 10px; border-radius: 99px;
  font-size: 10px; font-weight: 600; letter-spacing: 0.04em;
  text-transform: uppercase;
  background: var(--bg-page); color: var(--text-secondary);
}}
/* Compact button treatment inside the topbar card */
[data-testid="stVerticalBlock"]:has(> [data-testid="stHorizontalBlock"] .tx-brand-row) [data-testid="stButton"] > button {{
  padding: 6px 12px !important; font-size: 11px !important;
  min-height: 0 !important; line-height: 1.4 !important;
}}
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

/* ===== v9 page-link nav (st.page_link + .nav-pill-active) ===== */
[data-testid="stPageLink"] a {{
  font-size: var(--fs-body) !important;
  font-weight: var(--fw-medium) !important;
  color: var(--text-primary) !important;
  background: transparent !important;
  border-radius: 8px !important;
  padding: 6px 12px !important;
  min-height: 36px !important;
  display: flex !important;
  justify-content: center !important;
  align-items: center !important;
  text-align: center !important;
  opacity: 0.72;
  transition: background 100ms ease, opacity 100ms ease, color 100ms ease !important;
}}
[data-testid="stPageLink"] a:hover {{
  background: var(--bg-subtle) !important;
  color: var(--text-primary) !important;
  opacity: 1;
}}
/* Force every descendant to inherit the anchor's color — Streamlit wraps the
   label in nested div/p/span in some versions; any one of them with its own
   color wins against the <a> rule. Also strip any default button-like bg so
   the nav doesn't render as dark boxes on dark mode. */
[data-testid="stPageLink"] a,
[data-testid="stPageLink"] a *,
[data-testid="stPageLink"] a p,
[data-testid="stPageLink"] a span,
[data-testid="stPageLink"] a div {{
  color: var(--text-primary) !important;
  background: transparent !important;
  margin: 0 !important;
  font-size: inherit !important;
  font-weight: inherit !important;
}}
.nav-pill-active {{
  display: inline-block; padding: 6px 12px; border-radius: 8px;
  background: var(--brand-green); color: #fff; font-size: 13px;
  font-weight: 500; text-align: center; letter-spacing: -0.005em;
}}

/* ===== Cards / KPIs ===== */
.tx-card {{
  background: var(--bg-surface); border: 1px solid var(--border);
  border-radius: 12px; padding: 16px;
  transition: transform 120ms ease, box-shadow 120ms ease;
}}
.tx-card:hover {{ transform: translateY(-1px); box-shadow: var(--shadow-hover); }}
.tx-kpi {{ position: relative; overflow: hidden; }}
.tx-kpi .lbl {{ font-size: var(--fs-eyebrow); font-weight: var(--fw-medium); color: var(--text-muted); text-transform: uppercase; letter-spacing: var(--ls-eyebrow); }}
.tx-kpi .val {{ font-size: var(--fv-lg); font-weight: var(--fw-semibold); letter-spacing: var(--ls-tight); font-variant-numeric: tabular-nums; }}
.tx-kpi .delta {{ font-size: var(--fs-caption); }}
.tx-kpi .delta.up {{ color: var(--brand-green); font-weight: 600; }}
.tx-kpi .delta.down {{ color: var(--danger); }}
.tx-kpi.hero {{ background: var(--hero-tint); }}
.tx-kpi.hero::before {{ content: ''; position: absolute; left: 0; top: 0; bottom: 0; width: 3px; background: var(--brand-green); }}
.tx-kpi.warn::before {{ content: ''; position: absolute; left: 0; top: 0; bottom: 0; width: 3px; background: var(--brand-gold); }}

/* ===== Tables ===== */
.tx-table {{ background: var(--bg-surface); border: 1px solid var(--border); border-radius: 12px; overflow: hidden; }}
.tx-table table {{ width: 100%; border-collapse: collapse; font-size: var(--fs-body); }}
.tx-table th {{
  text-align: left; padding: 8px 12px; background: var(--bg-subtle);
  color: var(--text-muted); font-weight: var(--fw-medium); font-size: var(--fs-eyebrow);
  text-transform: uppercase; letter-spacing: var(--ls-eyebrow); border-bottom: 1px solid var(--border);
}}
.tx-table td {{ padding: 8px 12px; border-top: 1px solid var(--border); color: var(--text-primary); font-size: var(--fs-body); }}
.tx-table tr:first-child td {{ border-top: 0; }}
.tx-table tr:hover td {{ background: var(--bg-subtle); }}

/* ===== Buttons ===== */
.tx-btn {{
  display: inline-block; padding: 8px 16px; font-family: var(--font-ui);
  font-size: var(--fs-body); font-weight: var(--fw-medium); border-radius: 8px; cursor: pointer;
  border: 1px solid transparent; text-decoration: none; transition: background 100ms ease;
}}
.tx-btn-primary {{ background: var(--btn-primary-bg); color: var(--btn-primary-fg); font-weight: var(--fw-semibold); }}
.tx-btn-primary:hover {{ background: var(--btn-primary-hover); }}
.tx-btn-secondary {{ background: var(--bg-surface); color: var(--text-primary); border-color: var(--border-input); }}
.tx-btn-secondary:hover {{ background: var(--bg-subtle); }}
.tx-btn-ghost {{ background: transparent; color: var(--link-fg); }}
.tx-btn-danger {{ background: var(--bg-surface); color: var(--danger); border-color: var(--danger-border); }}
.tx-btn-icon {{ padding: 7px; background: var(--bg-subtle); border-color: var(--border); }}

/* ===== Streamlit native button override (so st.button matches secondary) ===== */
[data-testid="stButton"] > button,
[data-testid="stDownloadButton"] > button,
[data-testid="stFormSubmitButton"] > button {{
  font-family: var(--font-ui) !important;
  font-size: var(--fs-body) !important;
  font-weight: var(--fw-medium) !important;
  padding: 8px 14px !important;
  min-height: 36px !important;
  border-radius: 8px !important;
  background: var(--bg-surface) !important;
  color: var(--text-primary) !important;
  border: 1px solid var(--border-input) !important;
  transition: background 100ms ease, border-color 100ms ease;
}}
[data-testid="stButton"] > button:hover,
[data-testid="stDownloadButton"] > button:hover {{ background: var(--bg-subtle) !important; }}
[data-testid="stButton"] > button:focus {{ box-shadow: var(--focus-ring) !important; outline: none !important; }}

/* ===== Form submit (primary) — use brand gold instead of Streamlit's default ===== */
[data-testid="stFormSubmitButton"] > button,
[data-testid="stButton"] > button[kind="primary"],
[data-testid="stFormSubmitButton"] > button[kind="primary"] {{
  background: var(--btn-primary-bg) !important;
  color: var(--btn-primary-fg) !important;
  border: 1px solid var(--btn-primary-bg) !important;
  font-weight: 600 !important;
}}
[data-testid="stFormSubmitButton"] > button:hover,
[data-testid="stFormSubmitButton"] > button[kind="primary"]:hover,
[data-testid="stButton"] > button[kind="primary"]:hover {{
  background: var(--btn-primary-hover) !important;
  border-color: var(--btn-primary-hover) !important;
}}
/* Hide the "Press Enter to submit form" caption */
[data-testid="InputInstructions"] {{ display: none !important; }}

/* ===== Inputs ===== */
[data-baseweb="input"] input, [data-baseweb="select"] {{
  background: var(--bg-surface) !important; color: var(--text-primary) !important;
  border-radius: 8px !important; font-size: 13px !important;
}}
[data-baseweb="input"] {{
  border-color: var(--border-input) !important;
  border-radius: 8px !important;
}}
[data-baseweb="input"] input::placeholder,
[data-baseweb="textarea"] textarea::placeholder {{
  color: var(--text-secondary) !important; opacity: 0.8 !important;
}}
/* Password show/hide eye button — neutral chrome */
[data-baseweb="input"] button {{
  background: transparent !important; border: none !important;
  color: var(--text-secondary) !important;
}}

/* ===== Badges ===== */
.tx-badge {{ display: inline-block; padding: 2px 8px; border-radius: 99px; font-size: var(--fs-eyebrow); font-weight: var(--fw-semibold); }}
.tx-badge.gold {{ background: var(--brand-gold); color: #000; }}
.tx-badge.green {{ background: rgba(45,138,62,0.10); color: var(--brand-green); border: 1px solid var(--brand-green); }}
.tx-badge.muted {{ background: var(--bg-page); color: var(--text-secondary); }}

/* ===== Section titles + breadcrumbs ===== */
.tx-section-title {{ font-size: var(--fs-h2); font-weight: 600; margin: 16px 0 8px; letter-spacing: -0.01em; }}
.tx-breadcrumb {{ font-size: var(--fs-caption); color: var(--text-muted); }}
.tx-breadcrumb b {{ color: var(--text-primary); font-weight: 500; }}

/* ===== Tab anchor: kill default underline (Streamlit's a:hover specificity) ===== */
.tx-tab, .tx-tab:hover, .tx-tab:visited, .tx-tab:active {{
  text-decoration: none !important;
}}

/* ===== Legacy component compatibility =====
   These classes are emitted by drawers.py legacy helpers (hero_kpi,
   section_header, mini_card, compare_card, kpi_card, insight_card,
   alert_banner, risk_card, all_clear_box, badge, top_bar, freshness_badge,
   section-card, executive summary). Re-style them in the v9 language so
   pages look correct without rewriting every helper. */

/* Hero KPI (executive landing) */
.hero-kpi {{
  background: var(--bg-surface); border: 1px solid var(--border);
  border-left: 3px solid var(--brand-green);
  border-radius: 12px; padding: 20px 24px; margin: 14px 0;
}}
.hero-kpi-label {{ font-size: var(--fs-eyebrow); font-weight: var(--fw-medium); color: var(--text-muted); text-transform: uppercase; letter-spacing: var(--ls-eyebrow); }}
.hero-kpi-value {{ font-size: var(--fv-hero); font-weight: var(--fw-bold); letter-spacing: var(--ls-display); font-variant-numeric: tabular-nums; color: var(--text-primary); }}
.hero-kpi-value.critical {{ color: var(--danger); }}
.hero-kpi-meta {{ font-size: var(--fs-caption); color: var(--text-secondary); display: flex; gap: 12px; flex-wrap: wrap; }}
.hero-kpi-sub {{ color: var(--text-secondary); }}
.hero-kpi-delta {{ font-size: var(--fs-caption); font-weight: 600; }}
.hero-kpi-delta.up {{ color: var(--brand-green); }}
.hero-kpi-delta.down {{ color: var(--danger); }}

/* Section headers / titles / rules */
.section-eyebrow {{ font-size: var(--fs-eyebrow); font-weight: var(--fw-medium); color: var(--text-muted); text-transform: uppercase; letter-spacing: var(--ls-eyebrow); margin-top: 18px; }}
.section-h2 {{ font-size: var(--fs-h1); font-weight: var(--fw-semibold); margin: 4px 0 8px; letter-spacing: var(--ls-tight); color: var(--text-primary); }}
.section-rule {{ display: none; }}
.section-header {{ font-size: var(--fs-h2); font-weight: var(--fw-semibold); color: var(--text-primary); margin: 18px 0 8px; letter-spacing: -0.01em; }}
.section-card {{ background: var(--bg-surface); border: 1px solid var(--border); border-radius: 12px; padding: 14px 16px; margin: 12px 0; }}
.section-card-title {{ font-size: var(--fs-h2); font-weight: var(--fw-semibold); color: var(--text-primary); margin-bottom: 4px; }}
.section-card-subtitle {{ font-size: var(--fs-caption); color: var(--text-muted); }}

/* Legacy KPI card */
.kpi-card, .kpi-card-na {{
  background: var(--bg-surface); border: 1px solid var(--border);
  border-radius: 12px; padding: 16px; transition: transform 120ms ease, box-shadow 120ms ease;
}}
.kpi-card:hover {{ transform: translateY(-1px); box-shadow: var(--shadow-hover); }}
.kpi-card.danger-glow {{ border-left: 3px solid var(--danger); }}
.kpi-card.warning-glow {{ border-left: 3px solid var(--brand-gold); }}
.kpi-label {{ font-size: var(--fs-eyebrow); font-weight: var(--fw-medium); color: var(--text-muted); text-transform: uppercase; letter-spacing: var(--ls-eyebrow); }}
.kpi-value {{ font-size: var(--fv-lg); font-weight: var(--fw-semibold); letter-spacing: var(--ls-tight); font-variant-numeric: tabular-nums; color: var(--text-primary); }}
.kpi-value--na {{ color: var(--text-muted); }}
.kpi-value.critical {{ color: var(--danger); }}
.kpi-delta {{ font-size: var(--fs-caption); }}
.kpi-delta.up {{ color: var(--brand-green); font-weight: 600; }}
.kpi-delta.down {{ color: var(--danger); }}
.kpi-delta.muted {{ color: var(--text-muted); }}

/* Mini card */
.mini-card {{ background: var(--bg-surface); border: 1px solid var(--border); border-radius: 10px; padding: 10px 12px; }}
.mini-content {{ display: flex; flex-direction: column; gap: 2px; }}
.mini-label {{ font-size: var(--fs-eyebrow); font-weight: var(--fw-medium); color: var(--text-muted); text-transform: uppercase; letter-spacing: var(--ls-eyebrow); }}
.mini-value {{ font-size: var(--fv-md); font-weight: var(--fw-semibold); color: var(--text-primary); font-variant-numeric: tabular-nums; }}

/* Compare card */
.compare-card {{ background: var(--bg-surface); border: 1px solid var(--border); border-radius: 10px; padding: 10px 12px; display: flex; flex-direction: column; gap: 4px; }}
.compare-label {{ font-size: var(--fs-eyebrow); font-weight: var(--fw-medium); color: var(--text-muted); text-transform: uppercase; letter-spacing: var(--ls-eyebrow); }}
.compare-main {{ font-size: var(--fv-md); font-weight: var(--fw-semibold); color: var(--text-primary); font-variant-numeric: tabular-nums; }}
.compare-arrow {{ margin: 0 6px; color: var(--text-muted); }}
.compare-prev {{ font-size: var(--fs-caption); color: var(--text-secondary); }}
.compare-delta {{ font-size: var(--fs-caption); margin-left: 6px; font-weight: 600; }}
.compare-delta.up {{ color: var(--brand-green); }}
.compare-delta.down {{ color: var(--danger); }}
.compare-delta.muted {{ color: var(--text-muted); }}

/* Insight + alert + risk + all-clear */
.insight-card {{ background: var(--bg-surface); border: 1px solid var(--border); border-left: 3px solid var(--brand-green); border-radius: 10px; padding: 10px 14px; margin: 8px 0; font-size: var(--fs-caption); color: var(--text-primary); }}
.insight-info {{ border-left-color: var(--brand-green); }}
.insight-warning {{ border-left-color: var(--brand-gold); }}
.insight-critical {{ border-left-color: var(--danger); }}
.alert-banner {{ background: var(--bg-surface); border: 1px solid var(--border); border-radius: 10px; padding: 10px 14px; margin: 8px 0; font-size: var(--fs-caption); }}
.alert-info {{ border-left: 3px solid var(--brand-green); }}
.alert-warning {{ border-left: 3px solid var(--brand-gold); }}
.alert-danger {{ border-left: 3px solid var(--danger); color: var(--danger); }}
.risk-card {{ background: var(--bg-surface); border: 1px solid var(--border); border-left: 3px solid var(--brand-gold); border-radius: 10px; padding: 12px 14px; margin: 8px 0; }}
.risk-card.critical {{ border-left-color: var(--danger); }}
.risk-title {{ font-size: var(--fs-h2); font-weight: var(--fw-semibold); color: var(--text-primary); margin-bottom: 4px; }}
.risk-desc {{ font-size: var(--fs-caption); color: var(--text-secondary); line-height: 1.4; }}
.all-clear-box {{ background: var(--bg-surface); border: 1px solid var(--border); border-left: 3px solid var(--brand-green); border-radius: 10px; padding: 12px 14px; font-size: var(--fs-caption); color: var(--text-secondary); }}
.all-clear-sub {{ color: var(--text-muted); margin-top: 2px; }}
.risk-header {{ font-size: 14px; font-weight: 600; color: var(--text-primary); margin: 16px 0 8px; }}
.risk-count-badge {{ display: inline-block; padding: 2px 8px; border-radius: 99px; font-size: var(--fs-eyebrow); font-weight: var(--fw-semibold); background: var(--bg-page); color: var(--text-secondary); margin-left: 6px; }}
.risk-count-badge.warning {{ background: var(--brand-gold); color: #000; }}
.risk-count-badge.clear {{ background: rgba(45,138,62,0.10); color: var(--brand-green); border: 1px solid var(--brand-green); }}

/* Legacy badge */
.badge {{ display: inline-block; padding: 2px 8px; border-radius: 99px; font-size: var(--fs-eyebrow); font-weight: var(--fw-semibold); background: var(--bg-page); color: var(--text-secondary); }}
.badge-success {{ background: rgba(45,138,62,0.10); color: var(--brand-green); border: 1px solid var(--brand-green); }}
.badge-warning {{ background: var(--brand-gold); color: #000; }}
.badge-danger {{ background: rgba(220,38,38,0.10); color: var(--danger); border: 1px solid var(--danger); }}
.badge-info {{ background: var(--bg-page); color: var(--text-secondary); }}

/* Card layout: flex column + min-height so neighboring cards align */
.kpi-card, .kpi-card-na {{
  display: flex;
  flex-direction: column;
  justify-content: flex-start;
  gap: 6px;
  min-height: 104px;
}}
.hero-kpi {{
  display: flex;
  flex-direction: column;
  justify-content: center;
  gap: 8px;
  min-height: 112px;
}}
.tx-card.tx-kpi {{
  display: flex;
  flex-direction: column;
  justify-content: flex-start;
  gap: 6px;
  min-height: 96px;
}}
.mini-card {{
  display: flex;
  flex-direction: column;
  justify-content: center;
  min-height: 64px;
}}
.compare-card {{
  min-height: 72px;
}}

/* Make Streamlit column children stretch to row height so cards in a row are equal */
[data-testid="stHorizontalBlock"] > [data-testid="column"] {{
  display: flex;
  flex-direction: column;
}}
[data-testid="stHorizontalBlock"] > [data-testid="column"] > [data-testid="stVerticalBlock"] {{
  flex: 1;
}}
[data-testid="stHorizontalBlock"] > [data-testid="column"] .kpi-card,
[data-testid="stHorizontalBlock"] > [data-testid="column"] .hero-kpi,
[data-testid="stHorizontalBlock"] > [data-testid="column"] .tx-card.tx-kpi,
[data-testid="stHorizontalBlock"] > [data-testid="column"] .mini-card {{
  flex: 1;
}}

/* Top-bar (legacy data-as-of strip — small text in section above tabs if used) */
.top-bar {{ display: flex; justify-content: space-between; align-items: center; font-size: 11px; color: var(--text-muted); padding: 6px 0; }}
.top-bar-left, .top-bar-right {{ display: flex; align-items: center; gap: 8px; }}
.freshness-badge {{ display: inline-flex; align-items: center; gap: 4px; padding: 2px 8px; border-radius: 99px; font-size: var(--fs-eyebrow); font-weight: var(--fw-semibold); }}
.freshness-fresh {{ background: rgba(45,138,62,0.10); color: var(--brand-green); }}
.freshness-stale {{ background: var(--brand-gold); color: #000; }}
.freshness-dot {{ width: 6px; height: 6px; border-radius: 50%; background: currentColor; display: inline-block; }}
.top-bar-compute {{ color: var(--text-muted); }}

/* Concentration bar */
.conc-bar {{ display: flex; height: 18px; border-radius: 6px; overflow: hidden; margin: 8px 0; border: 1px solid var(--border); }}
.conc-bar .seg {{ display: flex; align-items: center; justify-content: center; font-size: 10px; color: #fff; font-weight: 600; }}

/* Empty state */
.empty-state {{ background: var(--bg-surface); border: 1px dashed var(--border); border-radius: 12px; padding: 24px; text-align: center; color: var(--text-muted); font-size: var(--fs-caption); }}

/* Tooltip icon */
.tooltip-icon {{ display: inline-block; width: 14px; height: 14px; line-height: 14px; text-align: center; border-radius: 50%; background: var(--bg-subtle); color: var(--text-muted); font-size: 9px; margin-left: 6px; cursor: help; border: 1px solid var(--border); }}

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

/* ===== Period segmented control + Reset slot =====
   Marker divs emitted by render_top_filters(): .tx-segmented wraps the 4
   period pills in a grouped container; .tx-reset-slot wraps the Reset
   button as a visually distinct ghost/danger tertiary. Streamlit places
   each marker div as a sibling before the stHorizontalBlock that holds
   the actual buttons, so we target the following-sibling block with :has. */

/* Group background for the 4-pill cluster. We target the stHorizontalBlock
   that immediately follows the .tx-segmented marker div. */
.tx-segmented + div [data-testid="stHorizontalBlock"],
[data-testid="stVerticalBlock"]:has(> .tx-segmented) [data-testid="stHorizontalBlock"]:first-of-type {{
  background: var(--bg-subtle);
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 2px;
  gap: 2px !important;
}}

/* Inactive period pill: borderless, compact, muted text. */
[data-testid="stVerticalBlock"]:has(> .tx-segmented) [data-testid="stButton"] > button {{
  background: transparent !important;
  border: 1px solid transparent !important;
  color: var(--text-secondary) !important;
  font-size: 12px !important;
  font-weight: 400 !important;
  padding: 6px 10px !important;
  min-height: 0 !important;
  border-radius: 6px !important;
  box-shadow: none !important;
  transition: background 120ms ease, color 120ms ease;
}}
[data-testid="stVerticalBlock"]:has(> .tx-segmented) [data-testid="stButton"] > button:hover {{
  background: var(--bg-surface) !important;
  color: var(--text-primary) !important;
}}

/* Active period pill (Streamlit renders type="primary" as kind="primary"). */
[data-testid="stVerticalBlock"]:has(> .tx-segmented) [data-testid="stButton"] > button[kind="primary"] {{
  background: var(--brand-green) !important;
  color: #ffffff !important;
  font-weight: 500 !important;
  border-color: var(--brand-green) !important;
  box-shadow: 0 1px 2px rgba(0,0,0,0.06) !important;
}}
[data-testid="stVerticalBlock"]:has(> .tx-segmented) [data-testid="stButton"] > button[kind="primary"]:hover {{
  background: var(--brand-green) !important;
  color: #ffffff !important;
  filter: brightness(1.05);
}}

/* Reset slot: ghost/danger tertiary. Clearly separated from period pills. */
[data-testid="stVerticalBlock"]:has(> .tx-reset-slot) [data-testid="stButton"] > button {{
  background: transparent !important;
  border: 1px solid transparent !important;
  color: var(--danger) !important;
  font-size: 12px !important;
  font-weight: 500 !important;
  padding: 6px 10px !important;
  min-height: 0 !important;
  border-radius: 6px !important;
  box-shadow: none !important;
  transition: background 120ms ease;
}}
[data-testid="stVerticalBlock"]:has(> .tx-reset-slot) [data-testid="stButton"] > button:hover {{
  background: rgba(220,38,38,0.08) !important;
  border-color: var(--danger-border) !important;
  color: var(--danger) !important;
}}

/* ===== Login screen ===== */
/* Streamlit renders st.form as [data-testid="stForm"]; style it as the card panel. */
[data-testid="stForm"] {{
  background: var(--bg-surface);
  border: 1px solid var(--border);
  border-radius: 14px;
  padding: 28px 22px;
  box-shadow: 0 4px 20px rgba(0,0,0,0.04);
}}
.tx-login-title {{
  text-align: center; font-family: var(--font-serif); font-weight: 700;
  font-size: 26px; letter-spacing: 0.02em; margin: 40px 0 6px;
  display: flex; align-items: center; justify-content: center; gap: 10px;
}}
.tx-login-sub {{
  text-align: center; font-size: 12px; color: var(--text-muted);
  margin-bottom: 20px;
}}

/* ===== Loading screen ===== */
.tx-loading-overlay {{
  position: fixed; inset: 0; background: var(--bg-page); z-index: 9999;
  display: flex; flex-direction: column; align-items: center; justify-content: center;
  animation: tx-fade-in 200ms ease, tx-loading-autohide 300ms ease 900ms forwards;
  pointer-events: none;
}}
@keyframes tx-loading-autohide {{ to {{ opacity: 0; visibility: hidden; }} }}
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

/* ===== Breadcrumb (render_breadcrumb) ===== */
.breadcrumb {{
  font-size: var(--fs-caption); color: var(--text-muted);
  margin: 4px 0 8px; display: flex; align-items: center; flex-wrap: wrap;
  font-family: var(--font-ui);
}}
.breadcrumb .bc-link {{
  color: var(--link-fg); text-decoration: none;
}}
.breadcrumb .bc-link:hover {{ text-decoration: underline; }}
.breadcrumb .bc-current {{
  color: var(--text-primary); font-weight: 500;
}}
.breadcrumb .bc-sep {{
  color: var(--text-muted); margin: 0 8px;
}}

/* ===== Alert strip (global_alert_strip) ===== */
.alert-strip {{
  background: var(--bg-surface); border: 1px solid var(--border);
  border-left: 3px solid var(--text-muted);
  border-radius: 10px; padding: 8px 12px; margin: 6px 0 10px;
  font-size: var(--fs-caption); color: var(--text-secondary);
  display: flex; align-items: center; gap: 8px;
}}
.alert-strip-warning {{ border-left-color: var(--brand-gold); }}
.alert-strip-danger {{ border-left-color: var(--danger); }}
.alert-strip-count {{
  display: inline-block; padding: 2px 8px; border-radius: 99px;
  font-size: var(--fs-eyebrow); font-weight: var(--fw-semibold); background: var(--bg-page);
  color: var(--text-secondary);
}}
.alert-strip-count-warning {{ background: var(--brand-gold); color: #000; }}
.alert-strip-count-danger {{
  background: rgba(220,38,38,0.10); color: var(--danger);
  border: 1px solid var(--danger);
}}

/* ===== Section gaps (emitted by app.py + pages as <div class="section-gap">) ===== */
.section-gap    {{ height: 24px; }}
.section-gap-sm {{ height: 12px; }}

/* ===== Page title / subtitle ===== */
.page-title {{
  font-size: var(--fs-display); font-weight: var(--fw-semibold); color: var(--text-primary);
  letter-spacing: var(--ls-display); margin: 10px 0 2px;
}}
.page-subtitle {{
  font-size: var(--fs-caption); color: var(--text-muted);
  margin-bottom: 12px;
}}

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
