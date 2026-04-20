# Texicon Dashboard Redesign — Design Spec

**Date:** 2026-04-20
**Status:** Approved (visual direction), pending implementation plan
**Supersedes:** V6 Linear-style (`feedback_dashboard_style.md`), V7 chart refinements, V8 CEO-view polish

## Purpose

Redesign the entire 7-page Streamlit dashboard with an Apple/Linear-clean visual language, real Texicon brand accents (gold + green), industry-standard buttons and login, and a light/dark mode toggle. Retain all existing tables, KPIs, filters, and analytics — this is a visual + interaction redesign, not a data redesign.

## Approved Decisions

| Decision | Choice | Notes |
|---|---|---|
| Visual direction | **A · Apple / Linear** | Soft greys, generous whitespace, 1px borders, Inter UI |
| Login layout | **A · Centered card** | Single panel on `#f5f5f7` background, classic Apple-ID style |
| Main layout | **B · Top tabs** | All 7 pages as a tab strip; more horizontal real estate for tables |
| Theme toggle | Segmented pill, top-right | Persists per-user via session_state + cookie/query-param |
| Accent strategy | **B1 · Gold = action, Green = structure** | See palette below |

## Brand Palette

Sourced directly from `texiconagri.com` logo (sampled `#FFC907` from leaf, ~13K matching pixels).

| Role | Hex | Usage |
|---|---|---|
| Brand black | `#000000` | TEXICON wordmark, body type |
| Brand gold | `#FFC907` | Primary buttons (with black text), "TOP" badge, warning progress bars, hero KPI accent stripe on **money** KPIs in dark mode |
| Brand green | `#2d8a3e` | Active tab fill, hero KPI left-stripe + tinted bg, positive deltas, "GROWING" badge, progress fills |
| Negative | `#dc2626` | Negative deltas, destructive button outline |
| Background | `#f5f5f7` (light), `#000000` (dark) | Page background |
| Surface | `#ffffff` (light), `#1c1c1e` (dark) | Card / table background |
| Border | `#ececec` (light), `#2c2c2e` (dark) | All 1px borders |
| Muted text | `#888888` (light), `#888888` (dark) | Labels, subtitles |

**Color discipline:**
- Gold `#FFC907` may appear at most 1× in primary action role per page (Export button) plus discrete badges/bars. Never as a fill for entire cards.
- Green `#2d8a3e` is the structural accent — active tab, positive deltas, hero KPI stripe.
- All other UI is monochrome (black/white/grey).

## Typography

| Element | Font |
|---|---|
| Wordmark in topbar | Georgia / Times serif, 700, all caps, letter-spacing `0.02em` (mirrors logo) |
| UI body, KPIs, tables | `-apple-system, "SF Pro Text", Inter, system-ui` |
| Numeric values | Same UI stack, `font-variant-numeric: tabular-nums` |

No mono font. No icon font — use unicode glyphs (▲ ▼ ⌕ ⚙ ↓ ☀ ☾) for the few needed icons.

## Layout

### Topbar (sticky)
- Left: serif `TEXICON` wordmark + small gold leaf glyph (CSS shape: `border-radius: 50% 50% 50% 0; transform: rotate(-25deg); background: #FFC907`)
- Center: optional breadcrumb (`Revenue · Q1 2026`)
- Right: theme toggle (segmented pill `☀ Light | ☾ Dark`), user avatar, primary action button (page-specific, e.g. `Export CSV`)
- Background: `#fff` (light) / `#1c1c1e` (dark), `1px solid` border

### Tab strip
- 7 tabs in their existing order: Sales Home · Revenue · Cash · Operations · Reconnect · Intel · Data
- Background: `#fff` card with `1px solid #ececec`, padding `6px`, gap `2px`
- Active tab: filled `#2d8a3e` background, white text, `border-radius: 6px`
- Inactive: `#666` text, hover `background: #f5f5f7`
- Sales role: only Sales Home + Reconnect + Data visible (per existing role-gating)

### Page body
- Page width: 1200px max, centered
- Vertical rhythm: 8px grid (gap-1=8px, gap-2=16px, gap-3=24px)
- KPI strip: `display: grid; grid-template-columns: repeat(N, 1fr); gap: 8px`
- Hero KPI (first card): green left-stripe + faint green-to-white gradient background
- Tables: `#fff` card, 1px border, header row `#fafafa` with `9px uppercase` labels
- Cards: borderless interior — only the outer card has the 1px border. No shadows except on hover (`0 4px 12px rgba(0,0,0,0.04)`).

### Login screen
- Background: `#f5f5f7` full-bleed
- Centered panel: `max-width: 280px`, `#fff`, `1px solid #ececec`, `border-radius: 14px`, `padding: 28px 22px`
- Logo block on top (36×36 black square with white "T", or actual logo PNG)
- Title (18px serif "Texicon Dashboard") + subtitle ("Sign in to continue")
- Username + password inputs (10×12 padding, 1px `#d2d2d7` border, 8px radius)
- Primary "Sign in" button (full-width, black bg)
- Role pills below: `Owner` `Sales` (visual hint only)

## Button System

| Variant | Style | Use |
|---|---|---|
| Primary | `#FFC907` bg, `#000` text, `8px` radius, `font-weight: 600` | One per page max — the main action (Export, Save, Sign in) |
| Secondary | `#fff` bg, `1px #d2d2d7` border, `#111` text | Cancel, Filter, Date range |
| Ghost | Transparent bg, `#0066cc` text | Reset filters, View all |
| Destructive | `#fff` bg, `1px #fecaca` border, `#dc2626` text | Sign out, Remove |
| Icon | `#f5f5f7` bg, `1px #ececec` border, square 28×28 | Settings, search trigger |
| Tab | Inline in tab strip (see Layout) | Page nav |
| Chip | `#f5f5f7` bg, `99px` radius, 11px text | Status, filter values |

Sizes: only one size (8px vertical, 16px horizontal padding, 12px font). No size variants — keeps the system tight.

**Note on login primary button:** the login panel uses `#000` bg (not gold) so it reads as a system action, not a brand action. Gold becomes the primary button color *inside* the dashboard.

## Dark Mode

- Toggle in topbar (segmented pill, `☀ Light | ☾ Dark`)
- Persists via Streamlit `session_state` keyed by username; restored on next login
- All borders shift `#ececec → #2c2c2e`; surfaces `#fff → #1c1c1e`; page bg `#f5f5f7 → #000`
- Brand gold and green keep the **same hex** in dark mode — both meet WCAG AA against `#1c1c1e`
- Plotly charts: switch template `plotly_white → plotly_dark`, axis colors flip, brand accent unchanged

## Components Affected

Existing component files in `dashboard/components/`:
- `auth.py` → `render_login()` rewritten with new centered-card markup
- `drawers.py` → `top_bar()`, `render_nav()`, `kpi_card()`, `hero_kpi()`, `styled_table()`, `action_button_row()`, `badge()`, `section_header()`, `breadcrumb` rewritten
- `kpi_cards.py` → `render_kpi_row()` updated with green hero stripe + gold money-KPI accent option
- `charts.py` → all Plotly templates wired to current theme; brand colors as default series palette
- `filters.py` → `render_top_filters()` restyled to match new button system
- `formatting.py` → unchanged
- `insights.py` → restyled card chrome only

New file:
- `components/theme.py` — single source of truth for colors, fonts, spacing tokens; exposes `get_theme(mode: str) -> dict` and `inject_css(mode: str)`

The single `assets/style.css` is replaced by a Python-generated CSS string (so theme tokens are reusable in inline component HTML).

## Motion & Loading

Apple-style motion language: subtle, purposeful, never showy. All animations honor `prefers-reduced-motion: reduce`.

### Page transitions
- Fade + 4px upward slide on page mount: `opacity: 0→1, translateY(4px→0)` over `220ms cubic-bezier(0.16, 1, 0.3, 1)` (Apple's "ease-out-expo")
- Tab switch: active-tab pill animates position via CSS transform (`200ms` same easing); content fades in below

### Loading screen
- Full-screen overlay on initial app boot (while data loads): `#f5f5f7` bg with centered serif `TEXICON` wordmark + gold leaf, plus a 2px-tall progress bar beneath that fills `#2d8a3e` left-to-right indeterminate (CSS `@keyframes` 1.4s loop)
- Per-page data loads (after auth): a 2px green progress bar pinned to the topbar bottom edge, indeterminate, auto-hides when `t1 = time.time()` finishes
- Skeleton loaders for KPI cards and tables: 1px-border placeholder shapes with a `linear-gradient` shimmer animating `200%` left→right over `1.6s`

### Hover & focus
- Cards: lift `translateY(-1px)` + shadow `0 4px 12px rgba(0,0,0,0.04)` over `120ms`
- Buttons: subtle bg darken (gold `#FFC907 → #f0bb00`, secondary `#fff → #fafafa`) over `100ms`
- Inputs: focus ring `0 0 0 3px rgba(45,138,62,0.15)` (green at 15% alpha) over `100ms`
- Tabs: hover bg fade-in `100ms`

### Number animation
- KPI values count up from 0 to final on mount (`450ms` ease-out, only on first render per session — not on filter change which would feel laggy)
- Delta arrows pop in `150ms` after the number settles

### Theme switch
- Light↔dark transitions: all bg, border, text colors animate `200ms ease` simultaneously. No flash.

### Modal / drawer
- Drawer slides in from right `280ms cubic-bezier(0.32, 0.72, 0, 1)` (Apple's spring)
- Backdrop fades `200ms`

### What we don't do
- No bouncing, no spinning logos, no parallax, no scroll-triggered reveals
- No transitions over `300ms` except modals
- No gradient sweeps or "shine" effects on buttons

## Out of Scope

- No data model changes
- No new pages
- No changes to risk engine, analytics, or transformer logic
- No changes to role-based login *logic* (only restyle the login screen and topbar role chip)
- No mobile/responsive work beyond what Streamlit gives by default

## Success Criteria

1. All 7 pages render with the new visual language and pass a side-by-side review against the approved mockups.
2. Light/dark toggle works and persists across page navigation.
3. All existing tables, KPIs, filters, and exports work identically (no data regressions).
4. Login screen matches the centered-card mockup.
5. Owner and Sales roles still see the correct page subset.
6. Lighthouse contrast check on light + dark modes: no AA violations on text or interactive elements.
7. Page transitions, loading bar, hover lifts, KPI count-up, and theme-switch fade all work; nothing animates if `prefers-reduced-motion: reduce`.

## Open Questions

None at spec-time. (Real logo PNG can be swapped in for the CSS leaf glyph during implementation if user provides a transparent-bg version.)
