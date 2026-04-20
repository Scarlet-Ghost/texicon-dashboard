# Handoff — Role-Based Login (Owner + Sales)

**Date:** 2026-04-20
**Author:** Session ended here; resume from this doc.
**Branch state:** `main` is 17 commits ahead of `origin/main` — **not yet pushed to GitHub, not yet deployed to Streamlit Cloud**.

---

## What shipped (local, not deployed)

Two-role login gate on the Texicon dashboard:

- **Owner** sees the full 7-page exec dashboard (unchanged).
- **Sales** sees a 3-page view: Sales Home (new) · Customer Reconnection · Sales Intelligence (with the Margin & Pricing section hidden). Alert strip and cross-page risks are suppressed on sales sessions.

Login is email + password. Two accounts:

| Role  | Email                | Password           |
|-------|----------------------|--------------------|
| Owner | owner@texicon.com    | `gGv9Pa04JBdDwYI4` |
| Sales | sales@texicon.com    | `DUD7Sp0GY4QlnaRb` |

Stored in `dashboard/.streamlit/secrets.toml` (git-ignored). **Never committed.** Rotate by editing that file locally and by updating Streamlit Cloud app Secrets when deployed.

---

## Design + plan references

- Spec: `docs/superpowers/specs/2026-04-20-role-based-login-design.md`
- Plan: `docs/superpowers/plans/2026-04-20-role-based-login.md`

Both were reviewed by three parallel agents (auth security, data leakage, codebase integration) before implementation, then amended, then verified.

---

## File map

**Created**
- `dashboard/components/auth.py` — `render_login`, `require_role(allowed)`, `current_role`, `user_chip`, `logout_button`, `_role_for_email`. Uses `hmac.compare_digest`. Login uses `st.form`.
- `dashboard/pages/0_Sales_Home.py` — Sales landing page. Guarded `["sales"]` only.
- `dashboard/tests/test_sales_analytics.py` — 5 pytest cases for the new analytics helpers.
- `dashboard/.streamlit/secrets.toml` — git-ignored; contains real credentials locally.

**Modified**
- `dashboard/app.py` — login gate above data loads; sales users redirected via `st.switch_page("pages/0_Sales_Home.py")`; owner-only `require_role` after; `user_chip()` added.
- `dashboard/components/drawers.py` — `_NAV_PAGES_OWNER` (7) and `_NAV_PAGES_SALES` (3); `render_nav` now takes `role=None`.
- `dashboard/data/analytics.py` — appended `_resolve_columns`, `get_active_customers_this_month`, `get_new_customers_this_month`, `get_top_customers_ytd`, `get_top_items_ytd`. Resolves real columns as customer=`CLIENT`, item=`ITEM`, date=`DATE`, revenue=`NET SALES`, qty auto-detected.
- `dashboard/pages/1_Revenue_Sales.py`, `2_Cash_Collections.py`, `3_Operations_Delivery.py`, `6_Data_Explorer.py` — `require_role(["owner"])` guard, `user_chip()` after top_bar, `role=current_role()` on render_nav.
- `dashboard/pages/4_Customer_Reconnection.py` — `require_role(["owner","sales"])`; on sales sessions, `compute_global_risks` is skipped, `global_alert_strip` is not called, breadcrumb anchors to "Sales Home".
- `dashboard/pages/5_Sales_Intelligence.py` — same sales-suppression pattern as p4; **Section 4 MARGIN & PRICING ANALYSIS block (roughly lines 394–491) is wrapped in `if _role == "owner":`** so sales never sees margin/cost data.
- `.gitignore` — excludes `.streamlit/secrets.toml` and `dashboard/.streamlit/secrets.toml`.

---

## Verification status

| What | Status |
|------|--------|
| Syntax check across all 11 touched files | Pass |
| pytest `tests/test_sales_analytics.py` (5 cases) | 5/5 pass |
| Manual browser: owner login | **Untested** |
| Manual browser: sales login + redirect to Sales Home | Confirmed working after two fixes below |
| Manual browser: margin block hidden for sales | **Untested** |
| Manual browser: alert strip suppressed on p4/p5 for sales | **Untested** |
| Manual browser: URL-bypass blocked for sales | **Untested** |
| Manual browser: logout clears session | **Untested** |
| Deploy to Streamlit Cloud | **Not done** |

### Bugs found and fixed during this session

1. **Sales login landed on `/` and saw "Not authorized"** → fixed by `st.switch_page("pages/0_Sales_Home.py")` in `app.py` before `require_role`. Commit `cfa7eb1`.
2. **`styled_table(DataFrame)` raised `TypeError: missing 1 required positional argument: 'rows'`** → the component takes `(headers, rows)`. Fixed both call sites in Sales Home to pass `list(display.columns)` and `display.values.tolist()`. Commit `4fda2ce`.

---

## Open items for next session

### Must-do before deploy
1. **Finish manual browser verification.** Checklist (Task 10 of the plan):
   - Owner login → 7-item nav, margin section visible on Intel, alert strip visible where risks exist, logout works.
   - Sales login → lands on Sales Home, 3-item nav, tables render, no margin section on Intel, no alert strip on p4/p5, breadcrumb says "Sales Home".
   - While logged in as sales, type `/1_Revenue_Sales`, `/2_Cash_Collections`, `/3_Operations_Delivery`, `/6_Data_Explorer`, `/` — each must show "Not authorized".
   - While logged in as owner, type `/0_Sales_Home` — must show "Not authorized".
   - Logout → Back button returns to login, not previous page.
2. **Push `main` to `origin`.** Currently 17 commits ahead. User approved the merge but has not yet approved the push. Command: `/usr/bin/git push origin main`.
3. **Add secrets to Streamlit Cloud.** In the app settings for `texicon-dashboard.streamlit.app` → Secrets, paste:
   ```toml
   [auth]
   owner_email = "owner@texicon.com"
   owner_password = "gGv9Pa04JBdDwYI4"
   sales_email = "sales@texicon.com"
   sales_password = "DUD7Sp0GY4QlnaRb"
   ```
4. **Trigger redeploy.** Per memory note `project_deployment.md`: private-repo redeploy may need the flip-public-then-back trick if the new commits don't pick up automatically.
5. **Smoke-test production** at https://texicon-dashboard.streamlit.app.

### UX question raised, not resolved
Sales Home's "Active Customers This Month" and "New This Month" both showed **0** in local testing because the data is 4 days old and today is April 20 with likely no April orders yet.

Decide: keep as-is (honest about stale data), or change those KPIs to "Latest month in data" / "New in latest month". User opinion pending.

### Not-in-scope for this feature (noted in spec Non-goals)
- No per-user accounts or audit log
- No session timeout (`authed_at` is captured but unused)
- No rate-limiting on login attempts
- Password rotation does not force active sessions to re-authenticate
- Each browser tab is its own session

### Not deleted this session
- `dashboard/.env.profile` — untracked file at project root. Left alone; appears unrelated to this feature.

---

## How to resume

1. `cd /Users/dxp/Desktop/Personal/07_KKP/01_Texicon`
2. Read this handoff.
3. Start local app: `cd dashboard && /opt/homebrew/bin/python3.11 -m streamlit run app.py`
4. Walk the verification checklist above.
5. When green, push and deploy.

Memory updated: `project_role_based_login.md` entry exists in auto-memory and reflects this state.
