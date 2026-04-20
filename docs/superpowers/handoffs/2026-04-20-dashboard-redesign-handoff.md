# Handoff — Dashboard Redesign (Apple-clean + Texicon brand)

**Date:** 2026-04-20
**Author:** Session ended at the visual-fix loop. Resume from this doc.
**Branch state:** `feat/dashboard-redesign` is **26 commits ahead of `main`** — **not pushed, not merged, not deployed**. Dev server confirmed running locally.

---

## What shipped (local, on branch only)

A full visual redesign of the 7-page Streamlit dashboard:

- **Apple/Linear-clean** language: soft greys, Inter UI, Georgia serif for the `TEXICON` wordmark, 1px borders, generous whitespace, 8px grid.
- **Real Texicon brand colors** sampled from the logo on `texiconagri.com`:
  - **Gold `#FFC907`** — primary action button, "TOP" badges, warning bars.
  - **Green `#2d8a3e`** — active tab fill, hero KPI accent stripe, positive deltas, "GROWING" badges, progress fills.
  - Black `#000` for type, `#dc2626` for negative deltas.
- **Top-tab navigation** (replaces the sidebar). 7 tabs for Owner, 3 for Sales (Sales Home, Reconnect, Data).
- **Light + dark mode toggle** in the topbar (segmented `☀ Light | ☾ Dark`). Persists via `?theme=` query param + `st.session_state`. Dark mode = `#000` page bg, `#1c1c1e` cards, brand colors unchanged.
- **Apple-style motion**: page-in fade-slide (220ms), full-screen loading overlay with indeterminate green bar (auto-hides at 900ms), skeleton shimmer, hover lifts on cards, KPI count-up animation. All gated by `prefers-reduced-motion: reduce`.
- **Centered-card login** with TEXICON serif wordmark + gold leaf above a `tx-login-panel` form card.
- **Single source of truth** for design tokens: `dashboard/components/theme.py`. The legacy 1654-line `dashboard/assets/style.css` was deleted.

---

## Design + plan references

- **Spec:** `docs/superpowers/specs/2026-04-20-dashboard-redesign-design.md`
- **Plan:** `docs/superpowers/plans/2026-04-20-dashboard-redesign.md`
- **Brainstorm mockups (gitignored):** `.superpowers/brainstorm/78524-1776699254/content/`

The design was decided across 5 visual-companion screens (visual direction → login + buttons → layout → accents v1 → accents v3) with the user picking each step.

---

## File map

### Created
- `dashboard/components/theme.py` — design tokens (`_LIGHT`, `_DARK` dicts), `get_theme(mode)`, `inject_css(mode)` returning the full `<style>...</style>` block, plus `normalize_mode`, `toggle_mode`, `current_theme`, `set_theme` for persistence. **All CSS lives here.**
- `dashboard/components/motion.py` — `loading_overlay_html`, `hide_loading_script`, `skeleton_block`, `count_up_value`, `count_up_runtime_script` (vanilla-JS animation gated by `prefers-reduced-motion`).
- `dashboard/tests/test_theme.py` — 13 tests (token contract, CSS contract, mode helpers; parametrized over light/dark).
- `dashboard/tests/test_motion.py` — 5 tests for HTML string generators.
- `dashboard/tests/test_drawers.py` — 9 tests (topbar/nav/badge/breadcrumb HTML + `styled_table` regression coverage for `num_cols`/`green_cols`/`red_cols`/`row_classes`).

### Modified
- `dashboard/components/auth.py` — `render_login()` rewritten as a centered-column form with `tx-login-title` brand markup above and `[data-testid="stForm"]` styled as the panel. **Auth logic untouched.**
- `dashboard/components/drawers.py` — appended v9 helpers: `top_bar_html`, `render_nav_html`, `render_top_bar`, `badge_html`, `breadcrumb_html`, `kpi_card_html`, `kpi_row_html`, `_NAV_PAGES_OWNER`, `_NAV_PAGES_SALES`. Replaced `styled_table()` body with new card-chrome + preserved-kwargs version. **Old helpers (`top_bar`, `render_nav`, `kpi_card`, `hero_kpi`, etc.) still exist** — pages no longer call `top_bar`/`render_nav` but `kpi_card`/`hero_kpi`/`mini_card`/`compare_card`/etc. are still called from inside the page bodies.
- `dashboard/components/kpi_cards.py` — `render_kpi_row` rewritten to call `kpi_card_html` + emit `count_up_runtime_script`. `na_card` legacy still works.
- `dashboard/components/charts.py` — added `apply_theme(fig, mode)` and `_BRAND_PALETTE`; wired into 8 chart factories (`bar_chart`, `horizontal_bar`, `donut_chart`, `line_bar_combo`, `stacked_bar`, `area_chart`, `funnel_chart`, `treemap_chart`).
- `dashboard/app.py` — head replaced with `inject_css(current_theme())` + `loading_overlay_html()`; old `render_nav` and both `top_bar` calls removed; `render_top_bar(active_page="Revenue")` added; `hide_loading_script()` appended at end.
- `dashboard/pages/0_Sales_Home.py` … `6_Data_Explorer.py` — head replaced with `inject_css(current_theme())` + `render_top_bar(active_page=...)`; old `render_nav`/`top_bar` calls removed.
- `dashboard/components/filters.py` — **no edits needed**; existing `render_top_filters()` already used native Streamlit widgets and theme-aware classes (`filter-chip`, `filter-chips-row`). Those classes were re-added to `theme.py`.

### Deleted
- `dashboard/assets/style.css` — 1654 lines, fully replaced by `theme.py inject_css()`.

---

## Tests

```
32 passed in 0.62s
```

Distribution:
- `test_theme.py` — 13 (token contract, CSS contract, mode helpers, dark/light parametrized)
- `test_motion.py` — 5 (HTML/JS string contracts)
- `test_drawers.py` — 9 (topbar/nav/badge/breadcrumb HTML + `styled_table` num_cols/green_cols/red_cols/row_classes)
- `test_sales_analytics.py` — 5 (pre-existing, untouched)

---

## Commits (26 total on branch)

```
802bb13 feat(theme): legacy-component compat CSS so v9 styling reaches old helpers
1431fc4 fix(imports): dual-path imports inside render_kpi_row
1df6c70 fix(theme): gold primary button, darker placeholders, neutral password eye
ec24eb7 fix(imports): dual-path imports in auth.render_login + drawers helpers
20a4a3f fix(ui): auto-hide loading overlay + make login form visibly enclosed
5082e6e chore: remove legacy style.css now covered by theme.py
9ff0fae … 1344711 ebb9dc6  feat(pages): wire 7 pages × one commit each
96ebc3b feat(app): wire theme injection, loading overlay, new topbar+tabs
c7fbde2 feat(theme): add filter-chip classes so chips survive style.css deletion
2b8a1db feat(charts): wire Plotly templates to current theme + brand palette
0ad1d76 fix(table): honor num_cols/green_cols/red_cols/row_classes kwargs
08a4825 feat(table): rewrite styled_table with new card chrome
948df99 feat(kpi): rewrite KPI cards with hero stripe + count-up animation
b81dc6b feat(drawers): add v9 topbar, tab strip, badge, breadcrumb helpers
243d15e feat(auth): rewrite login as centered card with brand wordmark
04c71a5 feat(motion): add loading overlay, skeleton shimmer, KPI count-up
5cf11f7 feat(theme): mode normalization, toggle, session/query persistence
95bb3e4 refactor(theme): tokenize link/danger-border, dedupe .block-container
5647ad8 feat(theme): add theme tokens module + CSS generator
9989b60 chore: gitignore .superpowers/ brainstorm cache
```

---

## How to resume

```bash
cd /Users/dxp/Desktop/Personal/07_KKP/01_Texicon
git checkout feat/dashboard-redesign
git status                               # should be clean
python3.11 -m pytest dashboard/tests/   # 32 passing
cd dashboard && python3.11 -m streamlit run app.py --server.port 8765
# then open http://127.0.0.1:8765
```

**Login credentials** are in `dashboard/.streamlit/secrets.toml` (gitignored). See the role-based-login handoff for current values:
- Owner: `owner@texicon.com` / `gGv9Pa04JBdDwYI4`
- Sales: `sales@texicon.com` / `DUD7Sp0GY4QlnaRb`

---

## Known visual issues — to fix next session

These are confirmed-visible issues from the QA pass at end of session (last screenshot was the Owner Revenue page):

### 1. Form chrome inconsistencies
- [ ] **Sign in button**: was Streamlit-default green; now overridden to gold (commit `1df6c70`). Verify it stays gold across dark mode and other forms (e.g., the filter form uses Streamlit submit buttons too).
- [ ] **Filter buttons** (Q1 2025 / Q1 2026 / Full Period / Custom / Reset): the active "Full Period" pill is gold, others are outlined. Confirm hover states are visible in both modes.
- [ ] **Log out button**: the `user_chip()` row still appears as plain Streamlit chrome below the tab strip. Move it into the topbar or restyle it as a small ghost/secondary button.

### 2. Underlines on tab links
- [ ] Tabs (Sales Home / Cash / Operations / Reconnect / Intel / Data) had default-anchor underlines. Commit `802bb13` adds `.tx-tab { text-decoration: none !important; }`. **Verify the underline is gone after refresh.** If still present, Streamlit may be applying `text-decoration: underline` via a parent selector — try targeting `.tx-tabs a` instead.

### 3. Section headers / hierarchy
- [ ] "Executive Dashboard", "Q1 2025-2026 Performance Overview", "Key Insights", "Monthly Revenue", "Product Category Mix" rendered as plain stacked text in the QA screenshot. Commit `802bb13` adds `.section-h2`, `.section-eyebrow`, `.section-header`, `.section-card` styling. **Verify visual hierarchy is restored.**

### 4. Hero KPI not visually distinct
- [ ] The big "₱636.0M Net Revenue" hero on the Owner Revenue page rendered as plain text (no card, no big number). `802bb13` styles `.hero-kpi`/`.hero-kpi-value`/`.hero-kpi-meta`. **Verify the hero card now has the green left-stripe and 36px tabular-num value.**

### 5. Mini-card / compare-card text mashed together
- [ ] "Net Revenue ₱636.0M→7,209 txns3,378 invoices" lost its separators. The `mini_card` / `compare_card` legacy markup might emit values without proper separators. Re-render after `802bb13` and check; if still broken, the helpers themselves need a fix (look at `dashboard/components/drawers.py` lines 178–200).

### 6. Plotly chart polish
- [ ] **Donut chart legend text colour** — was muted grey-on-grey, hard to read. Verify `apply_theme()` is setting `legend.font.color`.
- [ ] **`funnel_chart` connector lines** use a hardcoded light-mode `BORDER` constant — wrong colour in dark mode. Located in `dashboard/components/charts.py`.
- [ ] **Donut categories label** — there's a stray "categories" label visible in the centre of the donut on the Revenue page. Investigate and either remove or style it.

### 7. Insights / alert callouts
- [ ] "Key Insights" bullet list (• Net revenue reached ₱636.0M…) is plain text. The `insight_card` helper emits `.insight-info`/`.insight-warning`/`.insight-critical` — `802bb13` styles those. Verify they show the coloured left-stripe card now.

### 8. Concentration bar (`conc_bar`)
- [ ] Used in some pages as a horizontal stacked bar. Verify the new `.conc-bar` styling renders correctly.

### 9. Risk cards / All-clear box
- [ ] Verify `.risk-card`, `.all-clear-box`, `.risk-count-badge` styling on pages that show them (Reconnect, Operations).

### 10. Dark mode walkthrough
- [ ] Click ☾ Dark in topbar. Walk all 7 pages (Owner) and all 3 pages (Sales). Look for: white card backgrounds left over, low-contrast text, broken Plotly templates, charts that don't follow brand palette in dark mode.

### 11. Sales role page subset
- [ ] Log in as Sales. Tab strip should show **only** Sales Home, Reconnect, Data. Direct nav to `/Revenue_Sales` should show "Not authorized".

### 12. Reduced motion
- [ ] Enable macOS Reduce Motion (Settings → Accessibility → Display → Reduce Motion). Confirm: no page-in slide, no KPI count-up, no card hover lifts, loading overlay still functional.

### 13. Lighthouse contrast audit
- [ ] Run Chrome DevTools Lighthouse Accessibility on light mode + dark mode. Goal: zero AA contrast violations.

---

## Plan for next session

The user wants a dedicated **visual-fix session driven by a real browser**, not by code-reading alone. Recommended workflow:

### Setup
1. **Pick a browser-automation tool.** Options:
   - **Chrome DevTools MCP** (`@chrome-devtools/mcp` if installed) — read DOM, computed styles, take screenshots.
   - **Playwright MCP** — full browser automation including click/type/screenshot.
   - **Manual + screenshot loop** — user opens browser, drops screenshots into chat, agent diagnoses + fixes.

2. **Confirm dev server**:
   ```bash
   cd /Users/dxp/Desktop/Personal/07_KKP/01_Texicon/dashboard
   python3.11 -m streamlit run app.py --server.port 8765
   ```

### Iteration loop (per page)
For each of: login → app.py (Revenue) → Sales Home → Cash → Operations → Reconnect → Intel → Data:

1. Capture screenshot in **light** mode.
2. Walk the visual checklist (sections 1–9 above).
3. Fix any issue inline by editing `dashboard/components/theme.py` (CSS) or the relevant helper.
4. Hot-reload the browser; re-capture; verify.
5. Switch to **dark** mode (`?theme=dark`) and repeat.
6. Commit each fix with a focused message.

### Special focus areas
- **Buttons**: the user wants every button to have visible white-on-dark-or-coloured text, with matching hover/focus states. Audit `[data-testid="stButton"]`, `[data-testid="stFormSubmitButton"]`, `[kind="primary"]`, `[kind="secondary"]`, and any `<a class="tx-btn-*">` instances.
- **Boxes**: every card-like element (KPI, table, insight, risk, mini, compare, alert, all-clear, section-card, login-panel) should have consistent `tx-card` chrome — 1px border, 12px radius, 14px padding, hover lift.
- **Theme colours**: nothing outside the 8 token colours (`bg-page`, `bg-surface`, `bg-subtle`, `border`, `text-primary`, `text-muted`, `text-secondary`, plus the three brand colours). Grep `dashboard/components/` for any remaining hex literals other than the brand pair: `grep -rn "#[0-9a-fA-F]\{3,6\}" dashboard/components/`.
- **Tabs / link underlines**: confirm `text-decoration: none` wins everywhere. Check Streamlit version's anchor specificity with DevTools.

### Each button must work properly
Every interactive element should be tested: click, observe state change, verify URL/session_state. Specifically:
- Theme toggle (☀/☾) — query-param round-trip
- Tab strip — page navigation
- Filter row (Q1 2025 / Q1 2026 / Full Period / Custom / Reset / More Filters) — state changes
- Sign in / Log out — auth flow
- Export CSV (where present) — download
- Tooltip icons (`.tooltip-icon`) — hover behaviour

### Plan-writing
Use **superpowers:writing-plans** to convert the checklist above into a numbered task plan **before** starting fixes. Invoke **superpowers:subagent-driven-development** for execution.

---

## Risks / things to watch

- **Streamlit version specificity**: Many of our `!important` overrides target `[data-testid="stButton"]` etc. A Streamlit upgrade could change those test-IDs. Pin the version in `requirements.txt` if it isn't already.
- **Hot-reload may cache CSS**: if a CSS change doesn't appear, hard-reload (Cmd+Shift+R) and clear Streamlit's cache.
- **Dual-path imports**: every time a module under `dashboard/components/` imports another `dashboard.components.*` module, it MUST use the try/except pattern:
  ```python
  try:
      from components.x import y
  except ModuleNotFoundError:
      from dashboard.components.x import y
  ```
  This pattern caught us four times this session. New imports should follow it from the start.
- **Brainstorm cache**: `.superpowers/` is gitignored. The visual mockups inside it are reference material only — do not try to commit them.

---

## Do not push without

1. Visual QA passing on **all 7 owner pages + 3 sales pages**, in **both light + dark**, in **Chrome + Safari** (Streamlit Cloud users use both).
2. Reduced-motion verified.
3. Test suite green.
4. User explicit "yes, push it".
5. Once approved: `git push origin feat/dashboard-redesign`, open PR with the spec + plan + this handoff in the description, then merge with the same flip-public-then-back trick used for previous private-repo Streamlit Cloud deploys (see `project_deployment.md` memory).
