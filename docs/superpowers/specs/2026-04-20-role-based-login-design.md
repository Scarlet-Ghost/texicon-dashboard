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
`app.py` entry:
1. If `st.session_state.role` unset → render login form (role dropdown + password field) and `st.stop()`.
2. On submit, compare password against `st.secrets["auth"]["owner_password"]` / `["sales_password"]`. On match set `st.session_state.role` and `st.rerun()`.
3. On role `owner` → render current exec dashboard (existing `app.py` body).
4. On role `sales` → render Sales Home body.

### Page guards
Every file in `pages/` gets a 3-line guard at the top:
```python
from components.auth import require_role
require_role(allowed=["owner"])  # or ["owner", "sales"] for p4, p5
```
`require_role` checks session state; redirects to login if unset, shows "Not authorized" stop-screen if role not in allowed list.

### Nav
`render_nav(role)` in `components/drawers.py` emits only the page_links allowed for the given role.
- Owner nav: 7 items (current).
- Sales nav: Sales Home · Reconnection · Sales Intelligence (3 items).

### Conditional sections
Page 5 margin analysis block wrapped in `if st.session_state.role == "owner":`. No locked placeholders — block simply doesn't render for sales.

### Top bar
Adds role chip (e.g. "Sales" / "Owner") and a "Log out" button that clears session state and reruns.

## Components

### New
- `components/auth.py` — `render_login()`, `require_role(allowed)`, `logout_button()`, `current_role()`
- `pages/0_Sales_Home.py` — Sales landing page (title prefix `0_` makes it first in Streamlit's auto-ordering, but nav is custom so order doesn't matter functionally; guarded to sales-only)

### Modified
- `app.py` — prepend login gate; branch body on role
- `pages/1_Revenue_Sales.py` — add `require_role(["owner"])`
- `pages/2_Cash_Collections.py` — add `require_role(["owner"])`
- `pages/3_Operations_Delivery.py` — add `require_role(["owner"])`
- `pages/4_Customer_Reconnection.py` — add `require_role(["owner", "sales"])`
- `pages/5_Sales_Intelligence.py` — add `require_role(["owner", "sales"])`; wrap margin section in owner check
- `pages/6_Data_Explorer.py` — add `require_role(["owner"])`
- `components/drawers.py` — `render_nav(role)` filters by role; `top_bar` adds role chip + logout button
- `.streamlit/secrets.toml` — new `[auth]` section (local)
- Streamlit Cloud secrets — same `[auth]` section (production)

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

- Active customers this month → derive from `sr` (sales report) filtered to current month, distinct customer count.
- New customers → customers in current month whose first-ever order is in current month.
- At-risk (30d silent) / dormant (90d+) → reuse existing reconnection logic from page 4.
- Top 10 customers by YTD revenue → `sr` grouped by customer, summed, sorted, top 10.
- Top 10 items by YTD qty/revenue → `sr` grouped by item, summed, sorted, top 10.

All logic either reuses `data/analytics.py` helpers or adds thin new helpers there. No cost/margin columns surfaced.

## Non-goals (v1)

- No per-user accounts, no user management UI, no audit log.
- No session timeout / auto-logout.
- No password reset flow (rotate via Streamlit Cloud secrets).
- No 2FA.
- No rate-limiting on login (Streamlit Cloud private repo is already gated).

## Testing

- Manual: log in as owner → see 7-page nav, margin analysis visible. Log in as sales → see 3-page nav, no margin block in p5, URL-typing to `/Cash_Collections` shows "Not authorized."
- Log out → back to login screen.
- Wrong password → error message, no session set.

## Risks & mitigations

- **URL bypass:** page guards are the real security boundary; hidden nav is UX only.
- **Shared password leak:** rotate via Streamlit Cloud secrets; no code change needed.
- **Sales Home data drift:** reuse central `data/analytics.py` so owner and sales see consistent numbers.
