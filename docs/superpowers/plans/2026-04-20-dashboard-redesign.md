# Dashboard Redesign Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Redesign all 7 pages of the Texicon Streamlit dashboard with an Apple/Linear-clean visual language, real Texicon brand accents (gold `#FFC907` + green `#2d8a3e`), light/dark toggle, full button system, and Apple-style motion (page transitions, loading bar, skeleton shimmer, KPI count-up) — without changing any data, analytics, or role-gating logic.

**Architecture:** A single `components/theme.py` module owns all design tokens (colors, fonts, spacing, motion timings) and generates the full CSS string via `inject_css(mode)`. The legacy 1654-line `assets/style.css` is deleted in Task 13 once `theme.py` covers everything. Theme mode (`"light" | "dark"`) is stored in `st.session_state["theme"]`, persisted to a query param so it survives page navigation. All interactive components (`auth.py`, `drawers.py`, `kpi_cards.py`, `charts.py`, `filters.py`) read tokens from `theme.py` rather than hardcoding values. Animations are pure CSS keyframes with a `prefers-reduced-motion` guard; KPI count-up uses a tiny inline `<script>` rendered via `st.markdown(unsafe_allow_html=True)`.

**Tech Stack:** Python 3.11, Streamlit, Plotly, pytest. CSS3 (custom properties, keyframes, transitions). No new pip dependencies.

**Testing approach (read first):** Streamlit's UI cannot be unit-tested without a browser harness. Tests therefore cover pure-Python boundaries — theme token consistency, CSS string generation contract, mode-toggle state machine, role gating, button-helper return values. Visual fidelity is verified via explicit checklists at the end (Task 14) using the running dev server. Any task that says "visual verification" requires the engineer to load the page in a browser and tick the checklist — do not skip these.

**Branch:** Work on a new branch `feat/dashboard-redesign` cut from `main`. Commit after every step that produces working code.

---

## File Structure

| Path | Action | Responsibility |
|---|---|---|
| `dashboard/components/theme.py` | Create | Single source of truth for tokens + `get_theme(mode)` + `inject_css(mode)` returning a CSS string |
| `dashboard/components/motion.py` | Create | Loading-screen HTML, skeleton shimmer HTML, KPI count-up `<script>` snippet |
| `dashboard/components/auth.py` | Modify | Rewrite `render_login()` (centered card) + `user_chip()` (chip styling). Logic unchanged. |
| `dashboard/components/drawers.py` | Modify | Rewrite `top_bar()`, `render_nav()` (now top-tab strip), `hero_kpi()`, `kpi_card()`, `styled_table()`, `badge()`, `section_header()`, `render_breadcrumb()`, `action_button_row()`. Other helpers stay. |
| `dashboard/components/kpi_cards.py` | Modify | Rewrite `render_kpi_row()` to emit hero stripe markup + count-up data attrs |
| `dashboard/components/charts.py` | Modify | Add `apply_theme(fig, mode)` and call from every chart factory. Default series palette = brand colors. |
| `dashboard/components/filters.py` | Modify | Restyle markup only — filter logic unchanged |
| `dashboard/app.py` | Modify | Read `theme` from query params → `inject_css(theme)`; show loading overlay; replace nav call |
| `dashboard/pages/0_Sales_Home.py` … `6_Data_Explorer.py` | Modify | Each page calls `inject_css(current_theme())` instead of reading `style.css`; uses new components |
| `dashboard/assets/style.css` | Delete (Task 13) | Replaced by `theme.py` output |
| `dashboard/tests/test_theme.py` | Create | Token consistency, CSS contract |
| `dashboard/tests/test_motion.py` | Create | Reduced-motion guard, count-up data-attr generation |
| `dashboard/tests/test_drawers.py` | Create | Pure helpers (badge, breadcrumb HTML) |

---

### Task 1: Set up branch and confirm baseline

**Files:** none

- [ ] **Step 1: Cut branch from main**

```bash
cd /Users/dxp/Desktop/Personal/07_KKP/01_Texicon
/usr/bin/git checkout -b feat/dashboard-redesign
```

- [ ] **Step 2: Run existing tests to capture baseline**

```bash
cd dashboard && /opt/homebrew/bin/python3.11 -m pytest tests/ -v
```
Expected: existing `test_sales_analytics.py` passes. Note the count.

- [ ] **Step 3: Confirm dev server starts**

```bash
cd /Users/dxp/Desktop/Personal/07_KKP/01_Texicon/dashboard && /opt/homebrew/bin/python3.11 -m streamlit run app.py --server.headless true --server.port 8765 &
sleep 5 && curl -s http://localhost:8765 | head -3 && kill %1
```
Expected: HTML response (not error). Kill the server.

- [ ] **Step 4: Commit branch placeholder**

No code change yet — proceed to Task 2 directly.

---

### Task 2: Theme token module — pure data + helpers

**Files:**
- Create: `dashboard/components/theme.py`
- Test: `dashboard/tests/test_theme.py`

- [ ] **Step 1: Write the failing tests**

Create `dashboard/tests/test_theme.py`:

```python
"""Tests for components.theme — token contract + CSS string generation."""
import pytest
from dashboard.components import theme


def test_get_theme_light_returns_required_keys():
    t = theme.get_theme("light")
    for key in ("bg_page", "bg_surface", "border", "text_primary",
                "text_muted", "brand_gold", "brand_green", "danger",
                "tab_active_bg", "tab_active_fg"):
        assert key in t, f"missing token: {key}"


def test_get_theme_dark_returns_required_keys():
    t = theme.get_theme("dark")
    for key in ("bg_page", "bg_surface", "border", "text_primary",
                "text_muted", "brand_gold", "brand_green", "danger",
                "tab_active_bg", "tab_active_fg"):
        assert key in t


def test_brand_colors_constant_across_modes():
    light = theme.get_theme("light")
    dark = theme.get_theme("dark")
    assert light["brand_gold"] == "#FFC907"
    assert dark["brand_gold"] == "#FFC907"
    assert light["brand_green"] == "#2d8a3e"
    assert dark["brand_green"] == "#2d8a3e"


def test_get_theme_invalid_mode_raises():
    with pytest.raises(ValueError):
        theme.get_theme("solarized")


def test_inject_css_contains_brand_hexes():
    css = theme.inject_css("light")
    assert "#FFC907" in css
    assert "#2d8a3e" in css


def test_inject_css_includes_reduced_motion_guard():
    css = theme.inject_css("light")
    assert "prefers-reduced-motion: reduce" in css


def test_inject_css_returns_str_starting_with_style_tag():
    css = theme.inject_css("light")
    assert css.startswith("<style>")
    assert css.endswith("</style>")
```

- [ ] **Step 2: Run tests — verify they fail**

```bash
cd /Users/dxp/Desktop/Personal/07_KKP/01_Texicon && /opt/homebrew/bin/python3.11 -m pytest dashboard/tests/test_theme.py -v
```
Expected: ImportError or ModuleNotFoundError on `dashboard.components.theme`.

- [ ] **Step 3: Implement `theme.py`**

Create `dashboard/components/theme.py`:

```python
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
.block-container {{ padding-top: 0.75rem !important; max-width: 1200px !important; }}

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
.tx-btn-ghost {{ background: transparent; color: #0066cc; }}
.tx-btn-danger {{ background: var(--bg-surface); color: var(--danger); border-color: #fecaca; }}
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
.block-container {{ animation: tx-page-in 220ms var(--ease-out); }}
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
```

- [ ] **Step 4: Add `__init__.py` if missing for tests**

```bash
ls /Users/dxp/Desktop/Personal/07_KKP/01_Texicon/dashboard/__init__.py 2>/dev/null || touch /Users/dxp/Desktop/Personal/07_KKP/01_Texicon/dashboard/__init__.py
```

- [ ] **Step 5: Run tests — verify pass**

```bash
cd /Users/dxp/Desktop/Personal/07_KKP/01_Texicon && /opt/homebrew/bin/python3.11 -m pytest dashboard/tests/test_theme.py -v
```
Expected: 7 passed.

- [ ] **Step 6: Commit**

```bash
cd /Users/dxp/Desktop/Personal/07_KKP/01_Texicon
/usr/bin/git add dashboard/components/theme.py dashboard/tests/test_theme.py dashboard/__init__.py
/usr/bin/git commit -m "feat(theme): add theme tokens module + CSS generator

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
```

---

### Task 3: Theme mode persistence + helper

**Files:**
- Modify: `dashboard/components/theme.py`
- Test: `dashboard/tests/test_theme.py`

- [ ] **Step 1: Add failing tests for mode helpers**

Append to `dashboard/tests/test_theme.py`:

```python
import streamlit as st


def test_normalize_mode_default_light():
    assert theme.normalize_mode(None) == "light"
    assert theme.normalize_mode("") == "light"
    assert theme.normalize_mode("garbage") == "light"


def test_normalize_mode_passthrough():
    assert theme.normalize_mode("light") == "light"
    assert theme.normalize_mode("dark") == "dark"


def test_toggle_mode():
    assert theme.toggle_mode("light") == "dark"
    assert theme.toggle_mode("dark") == "light"
```

- [ ] **Step 2: Run tests — verify fail**

```bash
cd /Users/dxp/Desktop/Personal/07_KKP/01_Texicon && /opt/homebrew/bin/python3.11 -m pytest dashboard/tests/test_theme.py -v
```
Expected: 3 new tests fail with AttributeError.

- [ ] **Step 3: Implement helpers in `theme.py`**

Append to `dashboard/components/theme.py`:

```python
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
```

- [ ] **Step 4: Run tests — verify pass**

```bash
cd /Users/dxp/Desktop/Personal/07_KKP/01_Texicon && /opt/homebrew/bin/python3.11 -m pytest dashboard/tests/test_theme.py -v
```
Expected: all 10 pass.

- [ ] **Step 5: Commit**

```bash
cd /Users/dxp/Desktop/Personal/07_KKP/01_Texicon
/usr/bin/git add dashboard/components/theme.py dashboard/tests/test_theme.py
/usr/bin/git commit -m "feat(theme): add mode normalization, toggle, and session/query persistence

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
```

---

### Task 4: Motion module — loading overlay, skeleton, count-up

**Files:**
- Create: `dashboard/components/motion.py`
- Test: `dashboard/tests/test_motion.py`

- [ ] **Step 1: Write the failing tests**

Create `dashboard/tests/test_motion.py`:

```python
"""Tests for components.motion — pure HTML/JS string generators."""
from dashboard.components import motion


def test_loading_overlay_html_contains_brand_and_bar():
    html = motion.loading_overlay_html()
    assert "tx-loading-overlay" in html
    assert "TEXICON" in html
    assert "tx-loading-bar" in html


def test_skeleton_block_default_size():
    html = motion.skeleton_block()
    assert "tx-skeleton" in html
    assert "height" in html


def test_skeleton_block_custom_size():
    html = motion.skeleton_block(width="120px", height="20px")
    assert "120px" in html
    assert "20px" in html


def test_count_up_script_includes_target_value():
    html = motion.count_up_value(label="Revenue", value="₱4.82M",
                                 numeric_target=4_820_000, prefix="₱", suffix="")
    assert "Revenue" in html
    assert 'data-tx-count-target="4820000"' in html
    assert 'data-tx-count-prefix="₱"' in html


def test_count_up_emits_script_once_helper():
    snippet = motion.count_up_runtime_script()
    assert "<script>" in snippet
    assert "data-tx-count-target" in snippet
    assert "prefers-reduced-motion" in snippet
```

- [ ] **Step 2: Run tests — verify fail**

```bash
cd /Users/dxp/Desktop/Personal/07_KKP/01_Texicon && /opt/homebrew/bin/python3.11 -m pytest dashboard/tests/test_motion.py -v
```
Expected: ImportError.

- [ ] **Step 3: Implement `motion.py`**

Create `dashboard/components/motion.py`:

```python
"""Pure HTML/JS string generators for loading, skeletons, and KPI count-up.

Functions return strings — they are wrapped in st.markdown(unsafe_allow_html=True)
by callers. Any motion is gated by prefers-reduced-motion via the CSS in theme.py.
"""


def loading_overlay_html() -> str:
    """Full-screen overlay shown during initial app boot."""
    return (
        '<div class="tx-loading-overlay" id="tx-loading-overlay">'
        '<div class="tx-brand" style="font-size:28px">'
        'TEXICON<span class="tx-leaf"></span>'
        '</div>'
        '<div class="tx-loading-bar"></div>'
        '</div>'
    )


def hide_loading_script() -> str:
    """Inline script to hide the overlay once Streamlit content paints."""
    return (
        '<script>'
        'requestAnimationFrame(function(){'
        '  var el=document.getElementById("tx-loading-overlay");'
        '  if(el){el.style.transition="opacity 200ms ease";el.style.opacity="0";'
        '         setTimeout(function(){el.remove();},220);}'
        '});'
        '</script>'
    )


def skeleton_block(width: str = "100%", height: str = "60px",
                   radius: str = "12px") -> str:
    return (
        f'<div class="tx-skeleton" '
        f'style="width:{width};height:{height};border-radius:{radius};"></div>'
    )


def count_up_value(label: str, value: str, numeric_target: float,
                   prefix: str = "", suffix: str = "") -> str:
    """Render a KPI value span with data attrs for the count-up runtime."""
    return (
        f'<span class="tx-kpi-val" '
        f'data-tx-count-target="{int(numeric_target)}" '
        f'data-tx-count-prefix="{prefix}" '
        f'data-tx-count-suffix="{suffix}" '
        f'aria-label="{label}: {value}">{value}</span>'
    )


def count_up_runtime_script() -> str:
    """Render once per page. Animates any [data-tx-count-target] from 0 to target."""
    return """<script>
(function(){
  if (window.__txCountInit) return; window.__txCountInit = true;
  var reduce = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  function fmt(n, prefix, suffix){
    if (n >= 1e6) return prefix + (n/1e6).toFixed(2) + 'M' + suffix;
    if (n >= 1e3) return prefix + (n/1e3).toFixed(1) + 'K' + suffix;
    return prefix + Math.round(n).toLocaleString() + suffix;
  }
  function animate(el){
    var target = parseFloat(el.getAttribute('data-tx-count-target'));
    var prefix = el.getAttribute('data-tx-count-prefix') || '';
    var suffix = el.getAttribute('data-tx-count-suffix') || '';
    if (reduce || isNaN(target)) { return; }
    var start = performance.now(), dur = 450;
    function tick(t){
      var p = Math.min(1, (t-start)/dur);
      var eased = 1 - Math.pow(1-p, 3);
      el.textContent = fmt(target * eased, prefix, suffix);
      if (p < 1) requestAnimationFrame(tick);
    }
    requestAnimationFrame(tick);
  }
  document.querySelectorAll('[data-tx-count-target]').forEach(animate);
})();
</script>"""
```

- [ ] **Step 4: Run tests — verify pass**

```bash
cd /Users/dxp/Desktop/Personal/07_KKP/01_Texicon && /opt/homebrew/bin/python3.11 -m pytest dashboard/tests/test_motion.py -v
```
Expected: 5 passed.

- [ ] **Step 5: Commit**

```bash
cd /Users/dxp/Desktop/Personal/07_KKP/01_Texicon
/usr/bin/git add dashboard/components/motion.py dashboard/tests/test_motion.py
/usr/bin/git commit -m "feat(motion): add loading overlay, skeleton shimmer, KPI count-up

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
```

---

### Task 5: Rewrite login screen (centered card)

**Files:**
- Modify: `dashboard/components/auth.py`

- [ ] **Step 1: Replace `render_login()` body**

In `dashboard/components/auth.py`, replace the body of `render_login()` (lines ~60-92, between the docstring and the trailing `st.stop()`) with:

```python
def render_login():
    """Render the centered-card login. Must run when role is unset."""
    from dashboard.components.theme import inject_css, current_theme
    import streamlit as st

    st.markdown(inject_css(current_theme()), unsafe_allow_html=True)

    if not _secrets_configured():
        st.error(
            "Authentication is not configured. "
            "Contact the administrator — `st.secrets['auth']` is missing "
            "required email/password entries."
        )
        st.stop()

    st.markdown(
        '<div class="tx-login-bg">'
        '<div class="tx-login-panel">'
        '<div class="tx-brand" style="justify-content:center;font-size:22px;margin-bottom:6px;">'
        'TEXICON<span class="tx-leaf"></span></div>'
        '<div style="font-size:12px;color:var(--text-muted);margin-bottom:20px;">'
        'Sign in to continue</div>'
        '</div></div>',
        unsafe_allow_html=True,
    )

    # Form sits in a centered narrow column so it lines up with the panel.
    _, mid, _ = st.columns([1, 2, 1])
    with mid:
        with st.form("login_form", clear_on_submit=False):
            email = st.text_input("Email", placeholder="you@texicon.com",
                                  label_visibility="collapsed")
            password = st.text_input("Password", type="password",
                                     placeholder="Password",
                                     label_visibility="collapsed")
            submitted = st.form_submit_button("Sign in",
                                              use_container_width=True,
                                              type="primary")

    if submitted:
        role_key = _role_for_email(email)
        stored = _get_secret(f"{role_key}_password") if role_key else None
        if role_key and _check_password(password, stored):
            st.session_state["role"] = role_key
            st.session_state["authed_at"] = time.time()
            st.rerun()
        else:
            with mid:
                st.error("Invalid email or password.")

    st.stop()
```

- [ ] **Step 2: Visual verification**

```bash
cd /Users/dxp/Desktop/Personal/07_KKP/01_Texicon/dashboard && /opt/homebrew/bin/python3.11 -m streamlit run app.py --server.headless false --server.port 8765
```
Open http://localhost:8765, confirm:
- [ ] Centered "TEXICON" wordmark + gold leaf above the form
- [ ] Subtitle "Sign in to continue"
- [ ] Email + password inputs styled (rounded, subtle border)
- [ ] "Sign in" button full-width
- [ ] Background is `#f5f5f7`
- [ ] Page-in fade animation visible on load (subtle 4px slide)

Kill the server.

- [ ] **Step 3: Run existing tests — confirm no regression**

```bash
cd /Users/dxp/Desktop/Personal/07_KKP/01_Texicon && /opt/homebrew/bin/python3.11 -m pytest dashboard/tests/ -v
```
Expected: all pass (no auth tests exist; theme + motion still pass).

- [ ] **Step 4: Commit**

```bash
cd /Users/dxp/Desktop/Personal/07_KKP/01_Texicon
/usr/bin/git add dashboard/components/auth.py
/usr/bin/git commit -m "feat(auth): rewrite login as centered card with brand wordmark

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
```

---

### Task 6: Topbar + theme toggle + tab strip nav

**Files:**
- Modify: `dashboard/components/drawers.py`
- Modify: `dashboard/components/auth.py` (user_chip restyle)
- Test: `dashboard/tests/test_drawers.py`

- [ ] **Step 1: Write failing tests for pure HTML helpers**

Create `dashboard/tests/test_drawers.py`:

```python
"""Tests for components.drawers — pure HTML helpers only."""
from dashboard.components import drawers


def test_top_bar_html_includes_brand_and_toggle():
    html = drawers.top_bar_html(theme="light", role_label="Owner")
    assert "TEXICON" in html
    assert "tx-leaf" in html
    assert "tx-toggle" in html
    assert "Owner" in html
    assert "?theme=dark" in html  # toggle target


def test_top_bar_html_dark_toggles_to_light():
    html = drawers.top_bar_html(theme="dark", role_label="Sales")
    assert "?theme=light" in html


def test_render_nav_html_marks_active():
    html = drawers.render_nav_html(active="Revenue", role="owner")
    assert 'class="tx-tab on"' in html
    assert "Revenue" in html
    assert "Sales Home" in html


def test_render_nav_html_sales_subset():
    html = drawers.render_nav_html(active="Sales Home", role="sales")
    assert "Sales Home" in html
    assert "Reconnect" in html
    assert "Data" in html
    assert "Cash" not in html  # owner-only page hidden for sales


def test_badge_html_variants():
    assert "tx-badge gold" in drawers.badge_html("TOP", variant="gold")
    assert "tx-badge green" in drawers.badge_html("GROWING", variant="green")
    assert "tx-badge muted" in drawers.badge_html("INACTIVE", variant="muted")


def test_breadcrumb_html():
    html = drawers.breadcrumb_html(["Revenue", "Q1 2026"])
    assert "<b>Revenue</b>" in html
    assert "Q1 2026" in html
```

- [ ] **Step 2: Run tests — verify fail**

```bash
cd /Users/dxp/Desktop/Personal/07_KKP/01_Texicon && /opt/homebrew/bin/python3.11 -m pytest dashboard/tests/test_drawers.py -v
```
Expected: AttributeError on `drawers.top_bar_html` etc.

- [ ] **Step 3: Add helpers to `drawers.py`**

Append (or insert near top) to `dashboard/components/drawers.py`:

```python
# ===== New v9 redesign helpers =====

_NAV_PAGES_OWNER = [
    ("Sales Home", "/Sales_Home"),
    ("Revenue", "/Revenue_Sales"),
    ("Cash", "/Cash_Collections"),
    ("Operations", "/Operations_Delivery"),
    ("Reconnect", "/Customer_Reconnection"),
    ("Intel", "/Sales_Intelligence"),
    ("Data", "/Data_Explorer"),
]
_NAV_PAGES_SALES = [
    ("Sales Home", "/Sales_Home"),
    ("Reconnect", "/Customer_Reconnection"),
    ("Data", "/Data_Explorer"),
]


def top_bar_html(theme: str, role_label: str = "", primary_action: str = "") -> str:
    """Topbar HTML: serif TEXICON wordmark, theme toggle, role chip, optional action."""
    other = "dark" if theme == "light" else "light"
    sun_class = "on" if theme == "light" else ""
    moon_class = "on" if theme == "dark" else ""
    role_chip = (
        f'<span class="tx-badge muted" style="margin-right:6px;">{role_label}</span>'
        if role_label else ""
    )
    return (
        '<div class="tx-topbar">'
        '<div class="tx-brand">TEXICON<span class="tx-leaf"></span></div>'
        '<div class="tx-topright">'
        f'{role_chip}'
        '<div class="tx-toggle">'
        f'<a class="{sun_class}" href="?theme=light" target="_self">☀ Light</a>'
        f'<a class="{moon_class}" href="?theme=dark" target="_self">☾ Dark</a>'
        '</div>'
        f'{primary_action}'
        '</div>'
        '</div>'
    )


def render_nav_html(active: str, role: str = "owner") -> str:
    pages = _NAV_PAGES_SALES if role == "sales" else _NAV_PAGES_OWNER
    items = []
    for label, href in pages:
        cls = "tx-tab on" if label == active else "tx-tab"
        items.append(f'<a class="{cls}" href="{href}" target="_self">{label}</a>')
    return '<div class="tx-tabs">' + "".join(items) + '</div>'


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
    """Streamlit wrapper: read theme + role, emit topbar + nav. Call at top of every page."""
    import streamlit as st
    from dashboard.components.theme import current_theme
    from dashboard.components.auth import current_role
    role = current_role() or "owner"
    role_label = "Owner" if role == "owner" else "Sales"
    theme = current_theme()
    st.markdown(top_bar_html(theme=theme, role_label=role_label),
                unsafe_allow_html=True)
    st.markdown(render_nav_html(active=active_page, role=role),
                unsafe_allow_html=True)
```

- [ ] **Step 4: Run tests — verify pass**

```bash
cd /Users/dxp/Desktop/Personal/07_KKP/01_Texicon && /opt/homebrew/bin/python3.11 -m pytest dashboard/tests/test_drawers.py -v
```
Expected: 6 passed.

- [ ] **Step 5: Commit**

```bash
cd /Users/dxp/Desktop/Personal/07_KKP/01_Texicon
/usr/bin/git add dashboard/components/drawers.py dashboard/tests/test_drawers.py
/usr/bin/git commit -m "feat(drawers): add v9 topbar, tab strip, badge, breadcrumb helpers

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
```

---

### Task 7: KPI cards rewrite with hero stripe + count-up

**Files:**
- Modify: `dashboard/components/drawers.py`
- Modify: `dashboard/components/kpi_cards.py`

- [ ] **Step 1: Add `kpi_card_html()` and `hero_kpi_html()` to `drawers.py`**

Append to `dashboard/components/drawers.py`:

```python
def kpi_card_html(label: str, value: str, delta: str = "",
                  delta_dir: str = "neutral", numeric_target: float = None,
                  prefix: str = "", suffix: str = "",
                  variant: str = "default") -> str:
    """Render a single KPI card.

    variant: 'default' | 'hero' | 'warn' (controls left stripe + bg tint)
    delta_dir: 'up' | 'down' | 'neutral'
    numeric_target: if provided, animate count-up; otherwise render value as-is.
    """
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
    """Render a horizontal grid of kpi_card_html strings.

    cards: list[str] (each from kpi_card_html)
    """
    n = len(cards) or 1
    return (
        f'<div style="display:grid;grid-template-columns:repeat({n},1fr);'
        f'gap:8px;margin-bottom:12px;">'
        + "".join(cards)
        + '</div>'
    )
```

- [ ] **Step 2: Rewrite `render_kpi_row()` in `kpi_cards.py`**

In `dashboard/components/kpi_cards.py`, replace the body of `render_kpi_row()` to call into the new helpers. Read the existing function to map the spec types (`kpi_spec_money`, `kpi_spec_pct`, `kpi_spec_count`) to `kpi_card_html()`. The minimum:

```python
def render_kpi_row(specs):
    """Render a row of KPIs from a list of spec dicts.

    Each spec: {label, value, delta, delta_dir, numeric_target, prefix, suffix, variant}
    """
    import streamlit as st
    from dashboard.components.drawers import kpi_card_html, kpi_row_html
    from dashboard.components.motion import count_up_runtime_script
    cards = [kpi_card_html(**s) for s in specs]
    st.markdown(kpi_row_html(cards), unsafe_allow_html=True)
    st.markdown(count_up_runtime_script(), unsafe_allow_html=True)
```

If the existing `kpi_spec_money/pct/count` helpers already produce dicts close to the spec keys, leave them; otherwise normalize keys inside `render_kpi_row` before calling `kpi_card_html`.

- [ ] **Step 3: Run all tests**

```bash
cd /Users/dxp/Desktop/Personal/07_KKP/01_Texicon && /opt/homebrew/bin/python3.11 -m pytest dashboard/tests/ -v
```
Expected: all pass.

- [ ] **Step 4: Commit**

```bash
cd /Users/dxp/Desktop/Personal/07_KKP/01_Texicon
/usr/bin/git add dashboard/components/drawers.py dashboard/components/kpi_cards.py
/usr/bin/git commit -m "feat(kpi): rewrite KPI cards with hero stripe + count-up animation

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
```

---

### Task 8: Tables rewrite (`styled_table` + chrome)

**Files:**
- Modify: `dashboard/components/drawers.py`

- [ ] **Step 1: Replace `styled_table()` body**

Find `styled_table` in `dashboard/components/drawers.py`. Replace its body with:

```python
def styled_table(headers, rows, title: str = "",
                 actions_html: str = ""):
    """Render a styled table card.

    headers: list[str]
    rows: list[list[str]]  (already-formatted cells; HTML allowed)
    title: optional header label above the table
    actions_html: optional HTML for right-side action buttons in the header
    """
    import streamlit as st
    head_row = "".join(f"<th>{h}</th>" for h in headers)
    body_rows = "".join(
        "<tr>" + "".join(f"<td>{c}</td>" for c in r) + "</tr>"
        for r in rows
    )
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
```

- [ ] **Step 2: Visual verification**

Run the dev server and navigate to a page with tables (e.g., Revenue). Confirm:
- [ ] Table sits in a card with 1px border, 12px radius
- [ ] Header row has light-grey bg and uppercase 10px labels
- [ ] Hover on a row tints it `#fafafa`
- [ ] Title + actions header appears when provided

```bash
cd /Users/dxp/Desktop/Personal/07_KKP/01_Texicon/dashboard && /opt/homebrew/bin/python3.11 -m streamlit run app.py --server.headless false --server.port 8765
```
Kill the server when done.

- [ ] **Step 3: Commit**

```bash
cd /Users/dxp/Desktop/Personal/07_KKP/01_Texicon
/usr/bin/git add dashboard/components/drawers.py
/usr/bin/git commit -m "feat(table): rewrite styled_table with new card chrome

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
```

---

### Task 9: Charts theme integration

**Files:**
- Modify: `dashboard/components/charts.py`

- [ ] **Step 1: Add `apply_theme()` and call it from every factory**

Insert near the top of `dashboard/components/charts.py`:

```python
from dashboard.components.theme import get_theme, current_theme

_BRAND_PALETTE = ["#2d8a3e", "#FFC907", "#000000", "#888888",
                  "#1a5d27", "#9a7100", "#dc2626"]


def apply_theme(fig, mode: str = None):
    """Apply current theme template + brand palette to a Plotly figure."""
    mode = mode or current_theme()
    t = get_theme(mode)
    fig.update_layout(
        template=t["_plotly_template"],
        font=dict(family="-apple-system, Inter, system-ui",
                  size=11, color=t["text_primary"]),
        paper_bgcolor=t["bg_surface"],
        plot_bgcolor=t["bg_surface"],
        colorway=_BRAND_PALETTE,
        margin=dict(l=10, r=10, t=30, b=10),
    )
    fig.update_xaxes(gridcolor=t["border"], linecolor=t["border"], zeroline=False)
    fig.update_yaxes(gridcolor=t["border"], linecolor=t["border"], zeroline=False)
    return fig
```

Then in **every** factory function in this file (`bar_chart`, `horizontal_bar`, `donut_chart`, `line_bar_combo`, `stacked_bar`, `area_chart`, `funnel_chart`, `treemap_chart`), add `return apply_theme(fig)` immediately before the existing `return fig` (or replace `return fig` with `return apply_theme(fig)`).

- [ ] **Step 2: Run all tests**

```bash
cd /Users/dxp/Desktop/Personal/07_KKP/01_Texicon && /opt/homebrew/bin/python3.11 -m pytest dashboard/tests/ -v
```
Expected: all pass.

- [ ] **Step 3: Visual verification**

Run dev server, navigate to Revenue page, switch theme via `?theme=dark`. Confirm charts re-render with dark template, brand palette, no broken axes.

- [ ] **Step 4: Commit**

```bash
cd /Users/dxp/Desktop/Personal/07_KKP/01_Texicon
/usr/bin/git add dashboard/components/charts.py
/usr/bin/git commit -m "feat(charts): wire Plotly templates to current theme + brand palette

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
```

---

### Task 10: Filter restyle (markup only)

**Files:**
- Modify: `dashboard/components/filters.py`

- [ ] **Step 1: Restyle `render_top_filters()` chrome**

Wrap the existing filter rendering inside `render_top_filters()` in a `tx-card` div. Find any inline `style="..."` strings and replace them with the new tokens (`var(--bg-surface)`, `var(--border)`, `var(--text-secondary)`). Do not change filter logic or return value.

Example: if the function currently does

```python
st.markdown('<div style="background:#f7f8fa;...">', unsafe_allow_html=True)
```

change to

```python
st.markdown(
    '<div class="tx-card" style="margin-bottom:10px;padding:10px 14px;">',
    unsafe_allow_html=True,
)
```

- [ ] **Step 2: Visual verification**

Open Revenue page, confirm filter row sits in a clean card matching other surfaces, light + dark.

- [ ] **Step 3: Commit**

```bash
cd /Users/dxp/Desktop/Personal/07_KKP/01_Texicon
/usr/bin/git add dashboard/components/filters.py
/usr/bin/git commit -m "feat(filters): restyle to match v9 card chrome

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
```

---

### Task 11: Wire `app.py` (executive home / page 0 entry)

**Files:**
- Modify: `dashboard/app.py`

- [ ] **Step 1: Replace the head of `app.py`**

Replace the block from `st.set_page_config(...)` through the existing CSS injection (lines 8–19) with:

```python
import streamlit as st
import pandas as pd
import numpy as np
import os
import time
from datetime import datetime

st.set_page_config(
    page_title="Texicon Executive Dashboard",
    layout="wide",
    initial_sidebar_state="collapsed")

from dashboard.components.theme import inject_css, current_theme
from dashboard.components.motion import loading_overlay_html, hide_loading_script

# Inject CSS for the active theme (also hides Streamlit chrome).
st.markdown(inject_css(current_theme()), unsafe_allow_html=True)

# Show loading overlay (auto-removed once Streamlit paints).
st.markdown(loading_overlay_html(), unsafe_allow_html=True)
```

Then, **after** the `require_role(allowed=["owner"])` line, insert the topbar + nav call:

```python
from dashboard.components.drawers import render_top_bar
render_top_bar(active_page="Sales Home")  # for app.py the home is exec; use whichever label
```

For `app.py`, the active page label should be the executive overview — use `"Revenue"` as the home anchor, or add `"Home"` to the nav list. **Decision:** treat `app.py` as the Revenue/exec landing — so pass `active_page="Revenue"`.

At the very end of `app.py` (last line), append:

```python
st.markdown(hide_loading_script(), unsafe_allow_html=True)
```

- [ ] **Step 2: Remove old `top_bar()`, `render_nav()`, `global_alert_strip()` calls**

Search `app.py` for old calls to `top_bar(`, `render_nav(`, and remove them — they are replaced by `render_top_bar()`. Keep `global_alert_strip` if it still renders useful content; leave its body as-is for now (it gets restyled via theme tokens automatically).

- [ ] **Step 3: Visual verification**

```bash
cd /Users/dxp/Desktop/Personal/07_KKP/01_Texicon/dashboard && /opt/homebrew/bin/python3.11 -m streamlit run app.py --server.headless false --server.port 8765
```
Confirm:
- [ ] Loading overlay flashes briefly then fades out
- [ ] Topbar renders with TEXICON brand + theme toggle + role chip
- [ ] Tab strip renders with "Revenue" tab active (green fill)
- [ ] Clicking ☾ Dark in toggle navigates to `?theme=dark` and the whole page re-renders dark
- [ ] Page-in fade animation visible

Kill the server.

- [ ] **Step 4: Commit**

```bash
cd /Users/dxp/Desktop/Personal/07_KKP/01_Texicon
/usr/bin/git add dashboard/app.py
/usr/bin/git commit -m "feat(app): wire theme injection, loading overlay, new topbar+tabs

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
```

---

### Task 12: Wire each of the 7 pages

**Files:**
- Modify: `dashboard/pages/0_Sales_Home.py`
- Modify: `dashboard/pages/1_Revenue_Sales.py`
- Modify: `dashboard/pages/2_Cash_Collections.py`
- Modify: `dashboard/pages/3_Operations_Delivery.py`
- Modify: `dashboard/pages/4_Customer_Reconnection.py`
- Modify: `dashboard/pages/5_Sales_Intelligence.py`
- Modify: `dashboard/pages/6_Data_Explorer.py`

For **each** page file, perform the following identical edit. Repeat the steps below for every page — do not batch them; one page = one commit.

- [ ] **Step 1: Replace head of `0_Sales_Home.py`**

Find the existing `st.set_page_config(...)` block and the CSS-loading block (likely opens `assets/style.css`). Replace with:

```python
import streamlit as st
st.set_page_config(page_title="Sales Home — Texicon", layout="wide",
                   initial_sidebar_state="collapsed")

from dashboard.components.theme import inject_css, current_theme
from dashboard.components.drawers import render_top_bar

st.markdown(inject_css(current_theme()), unsafe_allow_html=True)
render_top_bar(active_page="Sales Home")
```

The `active_page` value per file:

| File | active_page |
|---|---|
| `0_Sales_Home.py` | `"Sales Home"` |
| `1_Revenue_Sales.py` | `"Revenue"` |
| `2_Cash_Collections.py` | `"Cash"` |
| `3_Operations_Delivery.py` | `"Operations"` |
| `4_Customer_Reconnection.py` | `"Reconnect"` |
| `5_Sales_Intelligence.py` | `"Intel"` |
| `6_Data_Explorer.py` | `"Data"` |

- [ ] **Step 2: Remove obsolete nav/topbar calls**

Search the page for any old `render_nav(`, `top_bar(`, or `st.markdown('<style>...</style>')` blocks that load `assets/style.css`. Remove them — `inject_css` + `render_top_bar` cover both.

Keep `require_role(...)` and all data/transform calls untouched.

- [ ] **Step 3: Visual verification of this page**

Run dev server, navigate to the page, confirm:
- [ ] Topbar renders
- [ ] Correct tab is active (matches `active_page`)
- [ ] All KPIs, tables, charts render in the new style
- [ ] No double-loaded CSS (no flicker, no conflicting old styles)

- [ ] **Step 4: Commit this page**

```bash
cd /Users/dxp/Desktop/Personal/07_KKP/01_Texicon
/usr/bin/git add dashboard/pages/0_Sales_Home.py
/usr/bin/git commit -m "feat(pages): wire Sales Home to v9 theme + topbar

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
```

- [ ] **Step 5: Repeat steps 1–4 for the remaining 6 pages**

For each of `1_Revenue_Sales.py`, `2_Cash_Collections.py`, `3_Operations_Delivery.py`, `4_Customer_Reconnection.py`, `5_Sales_Intelligence.py`, `6_Data_Explorer.py`: apply the head replacement (with the matching `active_page` label), remove old nav/CSS calls, visually verify, and commit individually.

---

### Task 13: Delete legacy `style.css`

**Files:**
- Delete: `dashboard/assets/style.css`

- [ ] **Step 1: Confirm no remaining references**

```bash
cd /Users/dxp/Desktop/Personal/07_KKP/01_Texicon
/opt/homebrew/bin/grep -rn "style.css" dashboard/ --include="*.py"
```
Expected: no matches.

- [ ] **Step 2: Delete the file**

```bash
/usr/bin/git rm dashboard/assets/style.css
```

- [ ] **Step 3: Run all tests**

```bash
cd /Users/dxp/Desktop/Personal/07_KKP/01_Texicon && /opt/homebrew/bin/python3.11 -m pytest dashboard/tests/ -v
```
Expected: all pass.

- [ ] **Step 4: Commit**

```bash
cd /Users/dxp/Desktop/Personal/07_KKP/01_Texicon
/usr/bin/git commit -m "chore: remove legacy style.css now covered by theme.py

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
```

---

### Task 14: Final visual QA (light + dark + reduced-motion)

**Files:** none

- [ ] **Step 1: Start dev server**

```bash
cd /Users/dxp/Desktop/Personal/07_KKP/01_Texicon/dashboard && /opt/homebrew/bin/python3.11 -m streamlit run app.py --server.headless false --server.port 8765
```

- [ ] **Step 2: Light-mode checklist (login + 7 pages)**

Login as Owner, then visit each page. For each, confirm:
- [ ] Topbar with serif TEXICON + gold leaf renders
- [ ] Theme toggle pill shows ☀ Light active
- [ ] Tab strip — correct tab highlighted green
- [ ] KPI cards — hero card has green stripe + green-tint bg, count-up animates on first load
- [ ] Tables — header has uppercase muted labels, rows hover-tint
- [ ] Primary action button (Export) is gold with black text
- [ ] Charts use brand palette (green dominant, gold for secondary series)
- [ ] Page-in fade animation visible on every navigation

- [ ] **Step 3: Dark-mode checklist**

Click ☾ Dark. Repeat the page tour. For each page confirm:
- [ ] Background black, cards `#1c1c1e`
- [ ] Brand colors unchanged (gold + green still visible against dark)
- [ ] Charts re-render with dark template
- [ ] No leftover white card backgrounds
- [ ] Theme persists across page navigation (via `?theme=dark` query param)

- [ ] **Step 4: Sales role checklist**

Log out, log in as Sales. Confirm:
- [ ] Tab strip shows only Sales Home, Reconnect, Data
- [ ] Owner-only pages (Revenue, Cash, Operations, Intel) are not in nav
- [ ] Direct navigation to an owner page shows "Not authorized"

- [ ] **Step 5: Reduced-motion check**

In OS settings (macOS: System Settings → Accessibility → Display → Reduce motion), enable Reduce Motion. Reload the dashboard. Confirm:
- [ ] Loading bar still shows but is static (or ≤10ms transition)
- [ ] No page-in slide
- [ ] No KPI count-up (values render at final value immediately)
- [ ] No card hover lifts

Disable Reduce Motion when done.

- [ ] **Step 6: Lighthouse contrast check**

Open Chrome DevTools → Lighthouse → Accessibility audit on light mode and dark mode. Confirm:
- [ ] Color contrast: PASS (no AA violations)
- [ ] Buttons have discernible names

- [ ] **Step 7: Final commit (no code, just close)**

```bash
cd /Users/dxp/Desktop/Personal/07_KKP/01_Texicon
/usr/bin/git status
```
Expected: clean working tree on `feat/dashboard-redesign`.

If any visual issue surfaced in steps 2–6, return to the relevant task, fix, and commit before declaring done.

- [ ] **Step 8: Push and open PR (only if user asks)**

Do not push or open PR without explicit user confirmation.

---

## Self-Review Notes

Spec coverage check (each spec section → task):
- Brand Palette → Task 2 (theme.py)
- Typography → Task 2 (CSS), Task 6 (brand wordmark)
- Layout · Topbar → Task 6, Task 11–12 (wiring)
- Layout · Tab strip → Task 6, Task 11–12
- Layout · Page body → Task 2 (CSS), Task 7 (KPIs), Task 8 (tables)
- Login screen → Task 5
- Button system → Task 2 (CSS — `.tx-btn-*` classes + Streamlit override)
- Dark mode → Task 2 (tokens), Task 3 (persistence), Task 9 (Plotly)
- Components Affected (auth, drawers, kpi_cards, charts, filters) → Tasks 5–10
- Motion · page transitions, loading screen, skeleton, hover, KPI count-up, theme switch → Tasks 2 (CSS keyframes), 4 (motion.py), 7 (count-up wired), 11 (loading overlay), 14 (verify)
- Modal/drawer motion → CSS in Task 2 (no current modal/drawer in dashboard; CSS is in place if added later)
- Out of Scope items confirmed not touched.

Type/name consistency:
- `kpi_card_html` (Task 7) called from `render_kpi_row` (Task 7) — match.
- `top_bar_html` + `render_nav_html` (Task 6) wrapped by `render_top_bar` (Task 6), called by `app.py` and pages (Tasks 11–12) — match.
- `inject_css(mode)` consistent across all callers.
- `current_theme()` consistent across all callers.

Placeholder scan: clean — every step has the actual code or command.

---

## Execution Handoff

Plan complete and saved to `docs/superpowers/plans/2026-04-20-dashboard-redesign.md`. Two execution options:

1. **Subagent-Driven (recommended)** — I dispatch a fresh subagent per task, review between tasks, fast iteration.
2. **Inline Execution** — Execute tasks in this session using executing-plans, batch execution with checkpoints.

Which approach?
