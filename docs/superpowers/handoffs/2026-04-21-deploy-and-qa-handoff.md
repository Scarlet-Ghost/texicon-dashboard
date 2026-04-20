# Handoff — Deploy + QA pass (2026-04-21, end of day)

## Where things stand

- Branch: `main` is the live branch (merged `feat/dashboard-redesign` via fast-forward today, 29 commits).
- Last commits on `main`:
  - `8606a5b chore(deploy): move runtime.txt to repo root so Streamlit Cloud honors python-3.11`
  - `0f7f641 fix(theme,filters): session-preserving theme toggle + empty-default multiselects`
  - `e2325b8 docs: handoff for 2026-04-21 visual QA pass`
  - `30e3bf1 fix(nav,theme): restore session via st.page_link + drop dark-theme leaks`
- Remote: `github-personal:Scarlet-Ghost/texicon-dashboard.git` (repo is **public** — the flip-public-then-back trick is not needed; Cloud auto-rebuilds on push).
- Streamlit Cloud: app at `https://texicon-dashboard.streamlit.app`. User clicked Reboot after the last push; the first post-reboot build hit an `ImportError: cannot import name 'render_top_bar'` which was a stale snapshot. The reboot + `runtime.txt` relocation should resolve that on the next build. **Verify before assuming the demo URL works.**
- Dev server: `http://localhost:8501`, Streamlit 1.50, background process already running.
- Tests: **31/31 green** (`/opt/homebrew/bin/python3.11 -m pytest dashboard/tests -q`).

## What shipped today

Two commits on top of the morning's visual-QA work:

### `0f7f641` — theme toggle + multiselect overflow
- **`dashboard/components/drawers.py`** — deleted the `<a href="?theme=...">` toggle from `top_bar_html` (those anchors reloaded the whole page and blew the Streamlit WebSocket session, which wiped `st.session_state["role"]` — same failure as the nav bug fixed in `30e3bf1`). `render_top_bar` now emits the topbar HTML without the pill, then renders a session-preserving `st.button` in a right-aligned column that calls `set_theme()` + `st.rerun()`.
- **`dashboard/components/filters.py`** — changed the 4 multiselects (Area Group, Product Category, Payment Terms, Warehouse) from `default=all_options` to `default=[]` with `placeholder="All (N)"`. The apply helpers treat empty selection as "no filter applied" by materializing the full list back into the filter dict, so `_render_active_chips` and `get_active_filter_count` still compare equal sets and don't emit chips for the unselected-default state. Fixes the pre-selected-chip overflow reported in the morning handoff.
- **`dashboard/tests/test_drawers.py`** — replaced the two `?theme=` assertions with a single `top_bar_html` test that confirms no toggle anchors leak into the HTML.

### `8606a5b` — runtime.txt placement
- `git mv dashboard/runtime.txt runtime.txt`. Streamlit Cloud only reads `runtime.txt` from the repo root; the in-`dashboard/` copy was ignored and Cloud was defaulting to Python 3.14 (visible in the ImportError traceback). The pin (`python-3.11`) should now apply on the next build.

### Verified in the browser (light + dark)
- Owner login → walked Executive, Data Explorer, flipped to Dark, flipped back — session persisted across every toggle.
- Sales login → walked Sales Home, Reconnect, Intel — session persisted, nav shows the 3-page subset only.
- Multiselects in Data Explorer show `All (N)` placeholder, dataset count stays at 7,212 when no filter is applied.

Screenshots in `docs/visual-qa/2026-04-21/`:
- `08-exec-dark-fixed.png` — first pass with duplicate toggles (documented, fixed in next commit).
- `09-exec-dark-clean.png` — final dark mode after removing the duplicate visual pill.
- `10-exec-light-current.png` — current light-mode Executive page. **Use this as the reference for the three carry-over tasks below.**

## What the next session needs to fix

User's exact request: "fix the box + the executive/revenue sales here presentation & active alerts are not showing properly".

Look at `docs/visual-qa/2026-04-21/10-exec-light-current.png` for the visual:

1. **"The box"** — the standalone `☾ Dark` / `☀ Light` button now floats in its own row in the top-right, visually disconnected from the topbar. It should sit *inside* the `tx-topbar` next to the `Owner` chip. The underlying bug is that Streamlit renders `st.button` as a block element in a column and we can't easily nest it inside our existing markdown topbar div. Two reasonable paths:
   - Rebuild the topbar itself with `st.columns` so brand / theme-button / role-chip are all Streamlit widgets — cleanest, preserves the session-safe button behavior.
   - Keep the HTML topbar but absolutely-position the `st.button` over a placeholder slot via CSS (`.tx-theme-btn-wrap` class is already reserved).
   Recommend path 1 — simpler to reason about, no absolute-positioning fragility.

2. **Executive + Revenue Sales presentation** — the page titles (`Executive Dashboard`, `Q1 2025-2026 Performance Overview`, `Revenue & Sales Performance`, etc.) are currently rendered as plain `<div>`s at ~14-15px, indistinguishable from body copy. The README promised "Georgia serif font on page titles". Tokens exist (`--font-serif` in `theme.py:111`) but aren't being applied. Fix: add a `.page-title` / `.page-eyebrow` style pair in `theme.py` and wire the existing page-title renders (in `app.py` and `pages/1_Revenue_Sales.py`) to emit those classes. Same treatment for the subtitle / eyebrow.

3. **Active alerts are not showing properly** — the Executive page has a `Risk Alerts (2)` section rendered near the bottom-middle (via `global_alert_strip`), but on sub-pages the alerts appear as a cramped single-line strip like "`2 Active alerts: 2 warning — check Executive Dashboard for details`" shoved between the breadcrumb and the page content (seen on Data Explorer earlier today). The strip is emitted by `global_alert_strip` from `components/drawers.py` — check the markup + the surrounding CSS in `theme.py`. Likely wants its own card-style container and probably should not render on sub-pages at all, only on Executive. Confirm the intended behavior with the user before implementing — this is a product question, not just a style fix.

## Commands the next session will want

```bash
# Dev server (probably already running — check lsof -i :8501 first)
cd /Users/dxp/Desktop/Personal/07_KKP/01_Texicon/dashboard
/opt/homebrew/bin/python3.11 -m streamlit run app.py --server.headless=true --server.port=8501

# Tests
/opt/homebrew/bin/python3.11 -m pytest dashboard/tests -q

# Git — zsh wraps `git` in a `_preflight` function that's undefined in non-interactive shells.
# Always write via:
command git <subcommand> ...

# Logins (owner has full nav; sales gets Sales Home + Reconnect + Intel only)
# owner@texicon.com / gGv9Pa04JBdDwYI4
# sales@texicon.com / DUD7Sp0GY4QlnaRb
```

## Still-open items from earlier handoffs (not regressed, not fixed either)

- Logout UX: after clicking "Log out", the topbar still renders with a default `Owner` badge and the full 7-tab nav for a single render before the "Please log in" page takes over. Source: `render_top_bar` uses `role = current_role() or "owner"` as a fallback, which masks the logged-out state. Low-priority; the content panel is already correct.
- Peso glyph `₱`: verified in the browser — renders fine in Inter across KPI cards, tables, tooltips. The morning handoff's "looks like a P with a stroke" concern was about a serif treatment that *doesn't currently ship*. If we re-introduce serif page titles (task 2 above), test the glyph there and consider swapping to a UI font for the currency span only.

## Memory updates (committed in this session)

- `project_dashboard_v9_visual_qa.md` — final state of the 2026-04-21 QA pass, now includes the deploy-day theme-toggle fix.
- `project_deployment.md` — clarified that the flip-public-then-back trick is only for *private* repos; Scarlet-Ghost/texicon-dashboard is currently public so push-to-main triggers a Cloud rebuild automatically. Added note about `runtime.txt` location requirement.

## Deployment punch list (already done today, recorded for traceability)

- [x] Walked Data Explorer + all sales pages in the browser
- [x] Walked Executive page in dark mode; session preserved
- [x] Fixed multiselect chip overflow
- [x] Confirmed `₱` glyph renders OK in Inter
- [x] `command git push origin feat/dashboard-redesign`
- [x] Fast-forward merged `feat/dashboard-redesign` → `main`
- [x] `command git push origin main`
- [x] Moved `runtime.txt` to repo root, pushed
- [ ] **Verify the live Streamlit Cloud build once reboot completes** — next session should hit the URL and confirm no ImportError before closing the loop.
