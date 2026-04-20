# Handoff — Visual QA pass (2026-04-21)

## Branch state

- Branch: `feat/dashboard-redesign` (28 commits ahead of `main`, **not pushed, not merged, not deployed**)
- Working tree: clean except `dashboard/.env.profile` (local only) and untracked `.playwright-mcp/` + `docs/visual-qa/`
- Dev server: `http://localhost:8501`, running in background (Streamlit 1.50)
- Tests: `32/32 pass` (`/opt/homebrew/bin/python3.11 -m pytest dashboard/tests -q`)

## What shipped this session

Single commit: **`30e3bf1 fix(nav,theme): restore session via st.page_link + drop dark-theme leaks`**

### The three loud bugs Playwright surfaced

1. **Nav clicks logged you out.** The v9 top-bar rendered `<a href target="_self">` tabs via `render_nav_html()`. Hard navigation dropped the Streamlit WebSocket, and with it `st.session_state["role"]`. Every tab click bounced to `"Please log in"`.
2. **Exec page highlighted "Revenue".** `app.py:82` passed `active_page="Revenue"`.
3. **Black fills + bright green chips in light mode.** `.streamlit/config.toml` was hardcoded to `backgroundColor = "#0A0A0B"`, `primaryColor = "#00D68F"`. Streamlit's native multiselect/expander widgets paint `secondaryBackgroundColor` directly — our `inject_css` tokens couldn't override them.

### The fixes

| File | Change |
|---|---|
| `dashboard/components/drawers.py` | Deleted `render_nav_html` + duplicate v9 `_NAV_PAGES_*`. Added `_label_to_page_id(label, role)`. Rewired `render_top_bar()` to call the existing `st.page_link`-based `render_nav()` (which honors `feedback_nav_routing.md`). Dropped the duplicate "Texicon" brand column from `render_nav()`. Added a single space between the count chip and "Active alerts:" text. |
| `dashboard/app.py` | `render_top_bar(active_page="Executive")`. `TOTAL QTY SOLD` KPI now puts `L/KG` in `sub_text` instead of inline in the value (unwraps the card). |
| `dashboard/components/theme.py` | Added CSS for `[data-testid="stPageLink"] a` (nav-link hover) and `.nav-pill-active` (green pill for the current page). |
| `dashboard/.streamlit/config.toml` | Rebased to neutral light: `base = "light"`, `backgroundColor = "#f5f5f7"`, `secondaryBackgroundColor = "#ffffff"`, `textColor = "#111111"`, `primaryColor = "#FFC907"`. `inject_css` still flips to dark cleanly. |
| `dashboard/tests/test_drawers.py` | Replaced the two deleted `render_nav_html` tests with `_label_to_page_id` coverage (owner + sales subset). |

### Verified in a real browser

Logged in as owner and clicked through Executive → Revenue → Cash → Operations → Reconnect → Intel. Session persists across every nav click; active pill renders; filter panels render on white with gold chips; no dark leaks. Screenshots live in `docs/visual-qa/2026-04-21/` (01-login-light, 02-exec-light-fixed, 03-revenue-fixed-v2, 04-cash, 05-operations, 06-reconnect, 07-intel).

## What still needs an eyes-on pass before pushing

These are carry-over or newly-surfaced and **not yet fixed**:

1. **Data Explorer (page 6) under owner** — not exercised in this session. All shared nav/theme fixes should cover it, but verify directly.
2. **Sales role** — sales login (`sales@texicon.com / DUD7Sp0GY4QlnaRb`) flow + 3-page subset (Sales Home, Reconnect, Intel) not walked.
3. **Dark mode** — only light mode was exercised. Toggle to dark, re-walk every page; expect surface/text tokens to flip via `inject_css` but confirm Plotly template also flips.
4. **Multiselect chip overflow** — when all filter options are pre-selected (the default), the last row in each filter column visibly clips (see `03-revenue-light-fixed.png`, bottom of the chip boxes). Streamlit multiselect has a fixed container height; either add `height: auto` or default the filters to empty lists.
5. **Peso glyph `₱` in serif hero** — renders as `P` with a single stroke in Georgia. If this bothers the CEO, swap the hero font to a UI font for currency values only or prefix with a CSS-rendered glyph.
6. **Theme toggle + logout** — both still use raw `<a href="?theme=dark">` + the existing logout button. The theme toggle triggers a query-param reload which in Streamlit happens to preserve session state, but this is implementation-dependent. Worth testing deliberately.

## Commands the next session will want

```bash
# Dev server (background)
cd /Users/dxp/Desktop/Personal/07_KKP/01_Texicon/dashboard
/opt/homebrew/bin/python3.11 -m streamlit run app.py --server.headless=true --server.port=8501

# Tests
/opt/homebrew/bin/python3.11 -m pytest dashboard/tests -q

# Git: this repo has a zsh `git` function that calls `_preflight`
# which is NOT defined in non-interactive shells. Bypass with:
command git <subcommand> ...
```

## Playwright MCP is now registered (user scope)

Registered via `claude mcp add playwright --scope user -- playwright-mcp` in `/Users/dxp/.claude-smifp/.claude.json`. Next session just needs to ensure Claude Code has booted with MCPs attached (`/mcp` should show `playwright ✓ connected`), then:

- Tools appear as `mcp__playwright__browser_*`, load via `ToolSearch select:...`
- Direct URL navigation via `browser_navigate` creates a fresh session — always go via the login form, then click nav links to stay authed
- Full snapshots on content-heavy pages (Reconnect, Data Explorer) can exceed the response-size cap. Use viewport screenshots + targeted evaluates instead of asking for a full accessibility snapshot after each click.

## Push checklist before merging to main

- [ ] Walk Data Explorer + all sales pages in browser
- [ ] Walk every page in dark mode
- [ ] Fix multiselect chip overflow (or default filters to empty)
- [ ] Decide on `₱` glyph in hero KPI
- [ ] `command git push origin feat/dashboard-redesign`
- [ ] Private-repo Streamlit Cloud redeploy trick (flip-public-then-back) per `project_deployment.md`
