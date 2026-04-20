# Role-Based Login & Sales View — Design Spec

**Date:** 2026-04-20
**Status:** Approved for planning

## Goal

Add a login gate to the Texicon dashboard with two roles:

1. **Owner** — full access to the current 7-page exec dashboard (unchanged behavior).
2. **Sales** — restricted view for the sales team, focused on reconnection and sales intelligence. No financial sensitivity (no margin/cost, no AR/cash, no ops, no raw data).

Two shared passwords (one per role), stored in Streamlit secrets.

## Role Boundaries

### Owner sees (unchanged)
Exec Home (`app.py`), Revenue/Sales (p1), Cash/Collections (p2), Operations/Delivery (p3), Customer Reconnection (p4), Sales Intelligence (p5), Data Explorer (p6).

### Sales sees
- **Sales Home** — new landing page: active-customer KPI hero, mini-KPIs for new / at-risk (30d) / dormant (90d+), top 10 customers by YTD revenue table, top 10 items sold YTD table. No cost/margin columns.
- **Customer Reconnection (p4)** — unchanged.
- **Sales Intelligence (p5)** — with margin analysis section conditionally hidden when `role == "sales"`. Q1 YoY comparison, bundles, customer habits, date breakdowns remain.

### Sales never sees
Revenue/Sales page 1 (page is owner-only; its top-customer/item data is surfaced in Sales Home instead), Cash/Collections, Operations/Delivery, Data Explorer, margin analysis inside page 5.

### Sensitivity rule
Sales CAN see: revenue ₱ per customer, order counts, item qty, customer status.
Sales CANNOT see: unit cost, margin %, profit, AR aging, DSO, warehouse ops, cycle time, raw table dumps.

## Architecture

### Login gate
`app.py` ordering (critical):
1. `st.set_page_config(...)` and CSS load (lines 8–19 of current `app.py`) stay at top.
2. **Login gate runs BEFORE the 4 `load_*()` data calls** so wrong passwords don't pay the Excel-load cost.
3. If `st.session_state.role` unset → render login form inside `st.form("login")` (role dropdown + password input + `form_submit_button`), then `st.stop()`.
4. On submit, compare with `hmac.compare_digest(entered.encode(), st.secrets["auth"]["owner_password"].encode())` (and same for sales). On match set `st.session_state.role`, `st.session_state.authed_at`, and `st.rerun()`.
5. After gate: `if role == "sales": render_sales_home(); st.stop()` — ensures owner data loads never run for sales users.
6. Otherwise (role=owner) continue with existing `app.py` body.
7. If `st.secrets["auth"]` is missing or keys absent → render "Auth not configured — contact admin" stop-screen (don't crash).

### Page guards
Every file in `pages/` gets the guard **AFTER** `st.set_page_config(...)` and the CSS+sidebar-hide block, **BEFORE** any data loading or rendering:
```python
from components.auth import require_role
require_role(allowed=["owner"])  # or ["owner", "sales"] for p4, p5; ["sales"] for page 0
```
`require_role(allowed)`:
- If `role` unset → render "Please log in" message with link to `app`, then `st.stop()`.
- If `role` not in `allowed` → render "Not authorized for your role" message, then `st.stop()`.
- Always ends in `st.stop()` on the denial path so nothing below executes.
- Streamlit multi-page routing fact: hitting `/Cash_Collections` directly runs only that page's script — `app.py` does NOT execute first. The guard is therefore the sole security boundary on direct URL access.

### Nav
`render_nav(active_page, risk_count, role)` in `components/drawers.py` filters page_links by role.
- Owner nav: 7 items (current).
- Sales nav: Sales Home · Reconnection · Sales Intelligence (3 items).
- Signature ripple: **every `render_nav(...)` call site updates to pass role** — `app.py` + all 6 `pages/*.py` = 7 call sites.
- Breadcrumb (`render_breadcrumb`) becomes role-aware: sales breadcrumbs anchor to `Sales_Home`, not exec home.

### Conditional sections & alert suppression
- Page 5 **margin block (lines 375–468 of `5_Sales_Intelligence.py`, all of Section 4 including its `section_divider`)** wrapped in `if current_role() == "owner":`. Block simply doesn't render for sales — no placeholders.
- **`global_alert_strip` and `compute_global_risks` are NEVER called on sales-facing pages** (Sales Home, p4, p5 when viewed as sales). Every current risk (Credit Exposure, Delivery Performance, Fulfillment Gap) references forbidden metrics. For sales sessions, `render_nav` receives `risk_count=0` and the alert strip is skipped entirely.
- **`components/insights.py`**: `generate_cash_insights`, `generate_operations_insights`, `generate_executive_insights` MUST NOT be imported by Sales Home or rendered on p4/p5 in sales role. `generate_reconnection_insights` and `generate_revenue_insights` are sales-safe.

### Top bar
Adds a separate `user_chip()` component (role label + "Log out" button) rendered beside existing `top_bar()`. `top_bar` signature unchanged — avoids rippling to 7 call sites. Logout body: `st.session_state.clear(); st.rerun()` — clears ALL session keys, not just `role`.

## Components

### New
- `components/auth.py` — `render_login()` (uses `st.form`), `require_role(allowed)` (ends in `st.stop()`), `logout_button()`, `current_role()`, `user_chip()`. Graceful handling if `st.secrets["auth"]` missing.
- `pages/0_Sales_Home.py` — Sales landing page, guarded `require_role(["sales"])`. Owner has its own exec home at `app.py`.

### Modified
- `app.py` — login gate inserted after `st.set_page_config`/CSS load but BEFORE `load_*()` calls (lines 46–49); role branch: `if role=="sales": render_sales_home(); st.stop()` before owner body runs. Adds `user_chip()` render near `top_bar`.
- `pages/1_Revenue_Sales.py` — `require_role(["owner"])` after page_config+CSS block, before data loads. Update `render_nav(..., role=...)` call.
- `pages/2_Cash_Collections.py` — same pattern.
- `pages/3_Operations_Delivery.py` — same pattern.
- `pages/4_Customer_Reconnection.py` — `require_role(["owner", "sales"])`; remove `global_alert_strip` call when role=="sales"; pass `risk_count=0` to `render_nav` when role=="sales"; role-aware breadcrumb.
- `pages/5_Sales_Intelligence.py` — `require_role(["owner", "sales"])`; wrap margin Section 4 (lines 375–468) in owner check; same alert-strip/breadcrumb treatment as p4.
- `pages/6_Data_Explorer.py` — `require_role(["owner"])`.
- `components/drawers.py` — `render_nav` gains `role` parameter, filters `_NAV_PAGES` to allowed pages for role, injects `0_Sales_Home` entry for sales role. `render_breadcrumb` becomes role-aware. `top_bar` unchanged.
- `data/analytics.py` — add sales-home helpers: `get_top_customers_ytd(sr, n=10)`, `get_top_items_ytd(sr, n=10)`, `get_active_customers_this_month(sr)`, `get_new_customers_this_month(sr)`. Reuse `data/reconnection.build_reconnection_data` for at-risk/falling-out counts (use existing `RECON_THRESHOLDS` segmentation; don't invent new 30/90d).
- `.streamlit/secrets.toml` — new `[auth]` section (local).
- Streamlit Cloud secrets — same `[auth]` section (production).
- `.gitignore` — add `.streamlit/secrets.toml` if not already excluded.

## Secrets shape

```toml
[auth]
owner_password = "..."
sales_password = "..."
```

## Session state keys

- `role` — `"owner"` | `"sales"` | unset
- `authed_at` — timestamp (for optional future timeout; not enforced in v1)

## Sales Home data sources

- **Active customers this month** → `sr` filtered to current month, distinct customer count. New helper `get_active_customers_this_month`.
- **New customers this month** → customers whose first-ever order date is in current month. New helper `get_new_customers_this_month`.
- **At Risk / Falling Out counts** → reuse `data/reconnection.build_reconnection_data` with existing `RECON_THRESHOLDS` segmentation. Labels match page 4 exactly ("High Potential", "At Risk", "Falling Out") — do NOT invent new 30/90d thresholds that would disagree with the reconnection page.
- **Top 10 customers by YTD revenue** → `sr` grouped by customer, summed, sorted. New helper `get_top_customers_ytd`.
- **Top 10 items by YTD qty/revenue** → `sr` grouped by item. New helper `get_top_items_ytd`.

All helpers live in `data/analytics.py` (shared with owner pages so numbers agree). No cost/margin columns surfaced anywhere.

## Non-goals (v1)

- No per-user accounts, no user management UI, no audit log.
- No session timeout / auto-logout (`authed_at` stored but unused in v1).
- No password reset flow (rotate via Streamlit Cloud secrets).
- No 2FA.
- No rate-limiting on login (Streamlit Cloud private repo is already gated).
- **Password rotation does NOT force active sessions to re-authenticate.** Rotating `sales_password` while a sales user has the dashboard open: they keep access until their browser tab closes. Accepted for v1.
- **Each tab/window = its own session.** Streamlit session state is per-websocket; opening a new tab requires a fresh login. Document for sales users.

## Testing

- Manual: log in as owner → see 7-page nav, margin analysis visible. Log in as sales → see 3-page nav, no margin block in p5, URL-typing to `/Cash_Collections` shows "Not authorized."
- Log out → back to login screen.
- Wrong password → error message, no session set.

## Risks & mitigations

- **URL bypass:** page guards are the real security boundary; hidden nav is UX only. Every `pages/*.py` MUST have `require_role(...)` as the first code after `st.set_page_config`+CSS. Add a simple grep-based check (CI or pre-commit) to enforce.
- **Shared password leak:** rotate via Streamlit Cloud secrets; no code change needed. Active sessions persist until tab closes (accepted).
- **Sales Home data drift:** reuse central `data/analytics.py` and existing `RECON_THRESHOLDS` so owner and sales see consistent numbers.
- **Timing attack on password:** `hmac.compare_digest` used for comparison.
- **Missing secrets crash:** `components/auth.py` wraps `st.secrets["auth"][...]` access in try/except and renders a graceful stop-screen.
- **New sensitive section added later leaks to sales:** all role checks use a uniform helper (`current_role()` or `owner_only()` context manager) so future code review can grep for the pattern.
