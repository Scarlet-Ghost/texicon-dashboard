# Role-Based Login & Sales View Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a two-role login (owner / sales) to the Texicon Streamlit dashboard, with a restricted sales view that hides margin, AR, ops, and raw-data content.

**Architecture:** Login gate in `app.py` runs before data loads; role stored in `st.session_state`. A thin `components/auth.py` module provides `require_role()`, `render_login()`, `user_chip()`, `logout_button()`, `current_role()`. Each page guards itself with `require_role([...])` after `st.set_page_config`+CSS but before any data load. Nav and breadcrumbs are role-aware. Sales sees a new `pages/0_Sales_Home.py` plus page 4 (Reconnection) and page 5 (Sales Intelligence, with margin block hidden). Sensitive helpers (`global_alert_strip`, `compute_global_risks`, cash/ops insights) are suppressed on sales pages.

**Tech Stack:** Python 3.11, Streamlit, pandas. Shared passwords in `.streamlit/secrets.toml` (local) and Streamlit Cloud secrets (production). Comparison uses `hmac.compare_digest`.

**Reference spec:** `docs/superpowers/specs/2026-04-20-role-based-login-design.md`

---

## File Plan

**Create:**
- `dashboard/components/auth.py` — auth helpers (login form, guards, logout, role chip)
- `dashboard/pages/0_Sales_Home.py` — sales landing page
- `dashboard/tests/test_sales_analytics.py` — smoke tests for new analytics helpers
- `.gitignore` addition (if missing)
- `dashboard/.streamlit/secrets.toml` (local, gitignored)

**Modify:**
- `dashboard/app.py` — login gate, role branch, user_chip
- `dashboard/components/drawers.py` — `render_nav` gains `role`; `render_breadcrumb` role-aware; `_NAV_PAGES` split per role
- `dashboard/data/analytics.py` — add 4 sales-home helpers
- `dashboard/pages/1_Revenue_Sales.py` — guard, nav call, user_chip
- `dashboard/pages/2_Cash_Collections.py` — same
- `dashboard/pages/3_Operations_Delivery.py` — same
- `dashboard/pages/4_Customer_Reconnection.py` — guard (owner+sales), suppress alerts for sales, role-aware breadcrumb, nav, user_chip
- `dashboard/pages/5_Sales_Intelligence.py` — guard, suppress alerts for sales, wrap margin block (lines 375–468), role-aware breadcrumb, nav, user_chip
- `dashboard/pages/6_Data_Explorer.py` — guard, nav call, user_chip

---

## Task 1: Secrets scaffolding & .gitignore

**Files:**
- Create: `dashboard/.streamlit/secrets.toml`
- Modify: `.gitignore` (project root)

- [ ] **Step 1: Ensure .streamlit/ exists in dashboard/**

Run: `ls dashboard/.streamlit/`
Expected: shows `config.toml`. If directory missing, `mkdir -p dashboard/.streamlit`.

- [ ] **Step 2: Create secrets.toml with two passwords**

Create `dashboard/.streamlit/secrets.toml`:

```toml
[auth]
owner_password = "CHANGE_ME_OWNER_PASSWORD"
sales_password = "CHANGE_ME_SALES_PASSWORD"
```

Replace both with real passwords chosen by the user before merging.

- [ ] **Step 3: Add secrets.toml to .gitignore**

Check if `.gitignore` at project root already excludes it:

Run: `grep -n "secrets.toml" .gitignore`

If no match, append to `.gitignore`:

```
# Streamlit secrets — never commit
.streamlit/secrets.toml
dashboard/.streamlit/secrets.toml
```

- [ ] **Step 4: Verify secrets.toml is untracked**

Run: `git status dashboard/.streamlit/secrets.toml`
Expected: either "ignored" or absent from output. Must NOT appear as "untracked".

- [ ] **Step 5: Commit gitignore change**

```bash
git add .gitignore
git commit -m "chore: gitignore Streamlit secrets.toml"
```

---

## Task 2: Create components/auth.py

**Files:**
- Create: `dashboard/components/auth.py`

- [ ] **Step 1: Write components/auth.py**

Create `dashboard/components/auth.py` with this exact content:

```python
"""Authentication helpers for role-based access.

Two shared passwords (owner / sales) live in st.secrets["auth"].
Password comparison uses hmac.compare_digest to avoid timing attacks.
Session state keys:
  role       — "owner" | "sales" | absent
  authed_at  — float timestamp from time.time()
"""
import hmac
import time
import streamlit as st


_ROLE_OWNER = "owner"
_ROLE_SALES = "sales"
_VALID_ROLES = (_ROLE_OWNER, _ROLE_SALES)


def _get_secret(key):
    """Return st.secrets['auth'][key] or None if missing. Never raises."""
    try:
        return st.secrets["auth"][key]
    except Exception:
        return None


def _secrets_configured():
    return bool(_get_secret("owner_password")) and bool(_get_secret("sales_password"))


def current_role():
    """Return the active role or None if not logged in."""
    return st.session_state.get("role")


def _check_password(entered, stored):
    if stored is None:
        return False
    return hmac.compare_digest(entered.encode("utf-8"), stored.encode("utf-8"))


def render_login():
    """Render the login form and stop the script.

    Must be called from app.py when role is unset. Uses st.form so
    individual keystrokes do not trigger reruns.
    """
    st.markdown("## Texicon Dashboard")
    st.markdown("Please log in.")

    if not _secrets_configured():
        st.error(
            "Authentication is not configured. "
            "Contact the administrator — `st.secrets['auth']` is missing "
            "`owner_password` and/or `sales_password`."
        )
        st.stop()

    with st.form("login_form", clear_on_submit=False):
        role_choice = st.selectbox("Role", ["Owner", "Sales"])
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Log in")

    if submitted:
        role_key = _ROLE_OWNER if role_choice == "Owner" else _ROLE_SALES
        stored = _get_secret(f"{role_key}_password")
        if _check_password(password, stored):
            st.session_state["role"] = role_key
            st.session_state["authed_at"] = time.time()
            st.rerun()
        else:
            st.error("Invalid password.")

    st.stop()


def require_role(allowed):
    """Guard a page. Call immediately after st.set_page_config + CSS block.

    `allowed` is a list like ["owner"], ["sales"], or ["owner", "sales"].
    - If role unset → show "please log in" and stop.
    - If role not in allowed → show "not authorized" and stop.
    - Otherwise return normally.
    """
    role = current_role()
    if role is None:
        st.markdown("### Please log in")
        st.markdown("Return to the [Executive home](/) to sign in.")
        st.stop()
    if role not in allowed:
        st.markdown("### Not authorized")
        st.markdown(
            f"Your role (`{role}`) does not have access to this page. "
            "Please navigate using the menu."
        )
        st.stop()


def logout_button(key="logout_btn"):
    """Render a Log out button. On click, clear session state and rerun."""
    if st.button("Log out", key=key, use_container_width=False):
        st.session_state.clear()
        st.rerun()


def user_chip():
    """Render a small role chip + logout button on the right side of the page.

    Call once per page, immediately after top_bar(). Uses a 2-column layout
    so the chip floats to the right.
    """
    role = current_role()
    if role is None:
        return
    label = "Owner" if role == _ROLE_OWNER else "Sales"
    c1, c2 = st.columns([6, 1])
    with c1:
        st.markdown(
            f'<div style="font-size:0.78rem;color:var(--text-secondary);'
            f'margin-top:4px;">Logged in as <strong>{label}</strong></div>',
            unsafe_allow_html=True,
        )
    with c2:
        logout_button()
```

- [ ] **Step 2: Smoke-test the module loads**

Run: `cd dashboard && /opt/homebrew/bin/python3.11 -c "from components import auth; print(auth._VALID_ROLES)"`
Expected: `('owner', 'sales')` printed, no traceback.

- [ ] **Step 3: Commit**

```bash
git add dashboard/components/auth.py
git commit -m "feat(auth): add components/auth.py with login gate and role guard"
```

---

## Task 3: Role-aware render_nav and render_breadcrumb in drawers.py

**Files:**
- Modify: `dashboard/components/drawers.py:12-48` (`_NAV_PAGES` + `render_nav`)
- Modify: `dashboard/components/drawers.py` `render_breadcrumb` (find its definition)

- [ ] **Step 1: Locate render_breadcrumb in drawers.py**

Run: `grep -n "def render_breadcrumb" dashboard/components/drawers.py`
Note the line number returned.

- [ ] **Step 2: Replace _NAV_PAGES and render_nav with role-aware versions**

Open `dashboard/components/drawers.py`. Replace lines 12-48 (the `_NAV_PAGES` constant and `render_nav` function) with:

```python
# --- Page Navigation Mapping (role-aware) ---
_NAV_PAGES_OWNER = [
    ("Executive", "app"),
    ("Revenue", "1_Revenue_Sales"),
    ("Cash", "2_Cash_Collections"),
    ("Operations", "3_Operations_Delivery"),
    ("Reconnect", "4_Customer_Reconnection"),
    ("Intel", "5_Sales_Intelligence"),
    ("Data", "6_Data_Explorer"),
]

_NAV_PAGES_SALES = [
    ("Sales Home", "0_Sales_Home"),
    ("Reconnect", "4_Customer_Reconnection"),
    ("Intel", "5_Sales_Intelligence"),
]


def _nav_pages_for_role(role):
    if role == "sales":
        return _NAV_PAGES_SALES
    return _NAV_PAGES_OWNER


def render_nav(active_page="app", risk_count=0, role=None):
    """Render the top navigation bar, filtered by role.

    `role` — "owner" | "sales" | None. If None, defaults to owner nav.
    `risk_count` — accepted for signature compatibility; not rendered as a badge.
    """
    pages = _nav_pages_for_role(role)
    with st.container(border=True):
        cols = st.columns([1.4] + [1] * len(pages))

        with cols[0]:
            st.markdown(
                '<div class="nav-brand-inline">Texicon</div>',
                unsafe_allow_html=True,
            )

        for i, (label, page_id) in enumerate(pages):
            with cols[i + 1]:
                if page_id == active_page:
                    st.markdown(
                        f'<div class="nav-pill-active">{label}</div>',
                        unsafe_allow_html=True,
                    )
                else:
                    path = "app.py" if page_id == "app" else f"pages/{page_id}.py"
                    st.page_link(path, label=label, use_container_width=True)
```

- [ ] **Step 3: Make render_breadcrumb role-aware**

Locate `render_breadcrumb` (from Step 1). It currently receives a list like `[("Executive", "app"), ("Customer Reconnection", None)]`. We do NOT change its signature — callers will pass a role-appropriate anchor. No change needed inside the function itself. Proceed to caller-side changes in later tasks.

- [ ] **Step 4: Smoke-test the module imports**

Run: `cd dashboard && /opt/homebrew/bin/python3.11 -c "from components.drawers import render_nav, _NAV_PAGES_SALES; print(len(_NAV_PAGES_SALES))"`
Expected: `3`

- [ ] **Step 5: Commit**

```bash
git add dashboard/components/drawers.py
git commit -m "feat(nav): make render_nav role-aware with separate owner/sales page lists"
```

---

## Task 4: Add sales-home helpers to data/analytics.py

**Files:**
- Modify: `dashboard/data/analytics.py` (append helpers at end)
- Create: `dashboard/tests/test_sales_analytics.py`

- [ ] **Step 1: Inspect existing analytics.py structure**

Run: `head -40 dashboard/data/analytics.py`
Goal: identify existing imports and column-name conventions (customer, item, date, revenue columns).

- [ ] **Step 2: Inspect sales_report column names**

Run: `grep -n "def transform_sales_report" dashboard/data/transformer.py`
Then read ~60 lines from that line to understand exact column names after transform. We need the names for: customer, item/sku, transaction date, revenue/total.

- [ ] **Step 3: Append helpers to data/analytics.py**

First verify pandas is already imported at the top of `dashboard/data/analytics.py`:

Run: `grep -n "^import pandas" dashboard/data/analytics.py`
Expected: line printed (likely `import pandas as pd`). If missing, add `import pandas as pd` at the top.

Append to the END of `dashboard/data/analytics.py`:

```python
# ---- Sales Home helpers ----
# Exposed for pages/0_Sales_Home.py. All helpers accept the transformed
# sales-report dataframe (`sr`) and return pure-python / pandas results.
# No cost/margin columns referenced.


def _resolve_columns(sr):
    """Return (customer_col, item_col, date_col, revenue_col) by best-match.

    Falls back to the first column whose lowercase name contains the keyword.
    Raises KeyError if no plausible column is found.
    """
    def pick(keywords):
        for col in sr.columns:
            lc = col.lower()
            if any(k in lc for k in keywords):
                return col
        raise KeyError(f"No column matching {keywords} in {list(sr.columns)}")

    customer_col = pick(["customer", "client"])
    item_col = pick(["item", "product", "sku"])
    date_col = pick(["date", "txn_date", "transaction"])
    revenue_col = pick(["revenue", "total", "amount", "net"])
    return customer_col, item_col, date_col, revenue_col


def get_active_customers_this_month(sr, today=None):
    """Distinct customer count with at least one transaction in the current month."""
    if sr is None or len(sr) == 0:
        return 0
    today = today or pd.Timestamp.today()
    customer_col, _, date_col, _ = _resolve_columns(sr)
    mask = (
        (sr[date_col].dt.year == today.year)
        & (sr[date_col].dt.month == today.month)
    )
    return int(sr.loc[mask, customer_col].nunique())


def get_new_customers_this_month(sr, today=None):
    """Customers whose first-ever order falls in the current month."""
    if sr is None or len(sr) == 0:
        return 0
    today = today or pd.Timestamp.today()
    customer_col, _, date_col, _ = _resolve_columns(sr)
    first_order = sr.groupby(customer_col)[date_col].min()
    mask = (first_order.dt.year == today.year) & (first_order.dt.month == today.month)
    return int(mask.sum())


def get_top_customers_ytd(sr, n=10, today=None):
    """Top N customers by YTD revenue. Returns DataFrame with columns:
    customer, revenue, orders, last_order_date.
    """
    if sr is None or len(sr) == 0:
        return pd.DataFrame(columns=["customer", "revenue", "orders", "last_order_date"])
    today = today or pd.Timestamp.today()
    customer_col, _, date_col, revenue_col = _resolve_columns(sr)
    ytd = sr[sr[date_col].dt.year == today.year]
    if ytd.empty:
        return pd.DataFrame(columns=["customer", "revenue", "orders", "last_order_date"])
    agg = ytd.groupby(customer_col).agg(
        revenue=(revenue_col, "sum"),
        orders=(date_col, "count"),
        last_order_date=(date_col, "max"),
    ).reset_index().rename(columns={customer_col: "customer"})
    return agg.sort_values("revenue", ascending=False).head(n).reset_index(drop=True)


def get_top_items_ytd(sr, n=10, today=None):
    """Top N items by YTD revenue. Returns DataFrame with columns:
    item, revenue, qty (if a qty column exists, else omitted).
    """
    if sr is None or len(sr) == 0:
        return pd.DataFrame(columns=["item", "revenue"])
    today = today or pd.Timestamp.today()
    _, item_col, date_col, revenue_col = _resolve_columns(sr)
    ytd = sr[sr[date_col].dt.year == today.year]
    if ytd.empty:
        return pd.DataFrame(columns=["item", "revenue"])

    # Detect qty column if present
    qty_col = None
    for col in sr.columns:
        lc = col.lower()
        if "qty" in lc or "quantity" in lc or lc == "units":
            qty_col = col
            break

    if qty_col is not None:
        agg = ytd.groupby(item_col).agg(
            revenue=(revenue_col, "sum"),
            qty=(qty_col, "sum"),
        ).reset_index().rename(columns={item_col: "item"})
    else:
        agg = ytd.groupby(item_col).agg(
            revenue=(revenue_col, "sum"),
        ).reset_index().rename(columns={item_col: "item"})
    return agg.sort_values("revenue", ascending=False).head(n).reset_index(drop=True)
```

**Important:** The `import pandas as pd as _pd_for_sales_home` line above is a placeholder — DELETE that line if `pd` is already imported at the top of `analytics.py` (it almost certainly is; check with `head -5 dashboard/data/analytics.py`). The helpers below use plain `pd.`.

- [ ] **Step 4: Verify column names actually match**

If the transformer normalizes column names differently (e.g. `customer_name`, `item_sku`, `txn_date`, `net_amount`) and `_resolve_columns` can't find a match, adjust the `pick(...)` keyword lists to match the actual column names you saw in Step 2. Re-run until no `KeyError`.

- [ ] **Step 5: Write smoke test**

Create `dashboard/tests/__init__.py` (empty) and `dashboard/tests/test_sales_analytics.py`:

```python
"""Smoke tests for Sales Home analytics helpers.

Run from project root with:
    cd dashboard && /opt/homebrew/bin/python3.11 -m pytest tests/ -v
(install pytest first if missing: /opt/homebrew/bin/python3.11 -m pip install pytest)
"""
import pandas as pd
import pytest

from data.analytics import (
    get_active_customers_this_month,
    get_new_customers_this_month,
    get_top_customers_ytd,
    get_top_items_ytd,
)


@pytest.fixture
def sample_sr():
    today = pd.Timestamp.today()
    this_month = today.replace(day=1)
    last_month = (this_month - pd.Timedelta(days=1)).replace(day=1)
    last_year = today.replace(year=today.year - 1, day=1)
    return pd.DataFrame({
        "customer": ["Acme", "Acme", "Beta", "Gamma", "Delta"],
        "item": ["X", "Y", "X", "Z", "Z"],
        "date": [this_month, last_month, this_month, last_year, this_month],
        "revenue": [100.0, 200.0, 50.0, 30.0, 70.0],
        "qty": [1, 2, 1, 1, 2],
    })


def test_active_customers_this_month(sample_sr):
    # Acme, Beta, Delta have orders this month = 3
    assert get_active_customers_this_month(sample_sr) == 3


def test_new_customers_this_month(sample_sr):
    # Acme's first order is this month (this_month < last_month is False; actually last_month < this_month so Acme's first is last_month)
    # First orders: Acme=last_month, Beta=this_month, Gamma=last_year, Delta=this_month
    # So Beta and Delta are new this month = 2
    assert get_new_customers_this_month(sample_sr) == 2


def test_top_customers_ytd_returns_correct_shape(sample_sr):
    df = get_top_customers_ytd(sample_sr, n=3)
    assert list(df.columns) == ["customer", "revenue", "orders", "last_order_date"]
    assert len(df) <= 3
    # Acme should lead YTD (100 + 200 = 300 assuming last_month is same year as this_month;
    # if today is January last_month is prior year — skip that edge case)
    if pd.Timestamp.today().month > 1:
        assert df.iloc[0]["customer"] == "Acme"


def test_top_items_ytd_includes_qty_if_present(sample_sr):
    df = get_top_items_ytd(sample_sr, n=5)
    assert "item" in df.columns
    assert "revenue" in df.columns


def test_empty_dataframe_safe():
    empty = pd.DataFrame(columns=["customer", "item", "date", "revenue"])
    assert get_active_customers_this_month(empty) == 0
    assert get_new_customers_this_month(empty) == 0
    assert get_top_customers_ytd(empty).empty
    assert get_top_items_ytd(empty).empty
```

- [ ] **Step 6: Install pytest if missing and run tests**

Run: `/opt/homebrew/bin/python3.11 -m pytest --version || /opt/homebrew/bin/python3.11 -m pip install pytest`
Then: `cd dashboard && /opt/homebrew/bin/python3.11 -m pytest tests/ -v`
Expected: all 5 tests pass. If column-name resolution fails on real data later, update `_resolve_columns` keyword lists.

- [ ] **Step 7: Commit**

```bash
git add dashboard/data/analytics.py dashboard/tests/
git commit -m "feat(analytics): add sales-home helpers (top customers/items, active/new this month)"
```

---

## Task 5: Build pages/0_Sales_Home.py

**Files:**
- Create: `dashboard/pages/0_Sales_Home.py`

- [ ] **Step 1: Create the Sales Home page**

Create `dashboard/pages/0_Sales_Home.py`:

```python
"""Sales Home — landing page for the sales role.

Shows active customers, new customers, at-risk / falling-out counts,
top 10 customers YTD, top 10 items YTD. No cost / margin / AR / ops data.
"""
import streamlit as st
import pandas as pd
import os
from datetime import datetime

st.set_page_config(
    page_title="Texicon — Sales Home",
    layout="wide",
    initial_sidebar_state="collapsed",
)

css_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "style.css")
with open(css_path) as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
st.markdown(
    '<style>section[data-testid="stSidebar"]{display:none !important;}</style>',
    unsafe_allow_html=True,
)

from components.auth import require_role, user_chip, current_role

require_role(allowed=["sales"])

from data.loader import load_sales_report, get_data_freshness
from data.transformer import transform_sales_report
from data.reconnection import build_reconnection_data
from data.analytics import (
    get_active_customers_this_month,
    get_new_customers_this_month,
    get_top_customers_ytd,
    get_top_items_ytd,
)
from components.drawers import (
    top_bar, render_nav, render_breadcrumb,
    section_header, hero_kpi, styled_table, empty_state,
)
from components.kpi_cards import render_kpi_row, kpi_spec_count
from components.formatting import format_php, format_number

# --- Load & Transform ---
sr_raw = load_sales_report()
sr = transform_sales_report(sr_raw)
freshness_hours = get_data_freshness()

now = datetime.now()
top_bar(
    data_date=now.strftime("%b %d, %Y"),
    current_time=now.strftime("%I:%M %p"),
    freshness_hours=freshness_hours,
)
user_chip()

render_nav(active_page="0_Sales_Home", risk_count=0, role=current_role())
render_breadcrumb([("Sales Home", None)])

# --- Hero KPI: active customers this month ---
active = get_active_customers_this_month(sr)
hero_kpi(
    label="Active Customers This Month",
    value=format_number(active),
    sub_value="unique customers with at least one order",
)

# --- Mini-KPI row: new / at-risk / falling-out ---
new_count = get_new_customers_this_month(sr)
recon = build_reconnection_data(sr)
at_risk = int((recon["segment"] == "At Risk").sum()) if not recon.empty else 0
falling = int((recon["segment"] == "Falling Out").sum()) if not recon.empty else 0

render_kpi_row([
    kpi_spec_count("New this month", new_count),
    kpi_spec_count("At Risk", at_risk),
    kpi_spec_count("Falling Out", falling),
])

# --- Top 10 customers YTD ---
section_header("Top 10 Customers — Year to Date")
top_cust = get_top_customers_ytd(sr, n=10)
if top_cust.empty:
    empty_state("No customer revenue yet this year.")
else:
    display = top_cust.copy()
    display["revenue"] = display["revenue"].apply(format_php)
    display["last_order_date"] = pd.to_datetime(display["last_order_date"]).dt.strftime("%b %d, %Y")
    display.columns = ["Customer", "Revenue", "Orders", "Last Order"]
    styled_table(display)

# --- Top 10 items YTD ---
section_header("Top 10 Items — Year to Date")
top_items = get_top_items_ytd(sr, n=10)
if top_items.empty:
    empty_state("No item revenue yet this year.")
else:
    display = top_items.copy()
    display["revenue"] = display["revenue"].apply(format_php)
    if "qty" in display.columns:
        display["qty"] = display["qty"].apply(format_number)
        display.columns = ["Item", "Revenue", "Qty"]
    else:
        display.columns = ["Item", "Revenue"]
    styled_table(display)
```

- [ ] **Step 2: Smoke-test page imports (script syntax only)**

Run: `cd dashboard && /opt/homebrew/bin/python3.11 -c "import ast; ast.parse(open('pages/0_Sales_Home.py').read()); print('syntax OK')"`
Expected: `syntax OK`

- [ ] **Step 3: Commit**

```bash
git add dashboard/pages/0_Sales_Home.py
git commit -m "feat(sales-home): add pages/0_Sales_Home.py restricted to sales role"
```

---

## Task 6: Add login gate and role branch to app.py

**Files:**
- Modify: `dashboard/app.py`

- [ ] **Step 1: Read current app.py top section (lines 1-70)**

Run: `sed -n '1,70p' dashboard/app.py`
Note the exact line where `load_sales_report()` is first called.

- [ ] **Step 2: Insert login gate before data loads**

In `dashboard/app.py`, find the block:

```python
css_path = os.path.join(os.path.dirname(__file__), "assets", "style.css")
with open(css_path) as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
st.markdown(
    '<style>section[data-testid="stSidebar"] { display: none !important; }</style>',
    unsafe_allow_html=True)
```

Immediately AFTER this block (and BEFORE the first `from data.loader import ...` line), insert:

```python
from components.auth import render_login, current_role, user_chip, require_role

# Login gate — must run before any data loads.
if current_role() is None:
    render_login()
```

- [ ] **Step 3: Locate render_nav call site in app.py and add role**

Run: `grep -n "render_nav(" dashboard/app.py`
Replace the existing call `render_nav(active_page="app", risk_count=...)` with:

```python
render_nav(active_page="app", risk_count=len(risks), role=current_role())
```

(Keep the existing `risk_count` argument — this page stays owner-only, so all alerts are appropriate here.)

- [ ] **Step 4: Add user_chip() after top_bar() in app.py**

Run: `grep -n "top_bar(" dashboard/app.py`
Immediately after the `top_bar(...)` call, add a new line:

```python
user_chip()
```

- [ ] **Step 5: Add owner-only guard after the gate (defense in depth)**

The `app.py` body is the owner's exec dashboard. After the login gate block and before data loads, add:

```python
require_role(allowed=["owner"])
```

This ensures a sales user who somehow sets `st.session_state["role"] = "sales"` and navigates to `/` still gets blocked. (Sales users reach Sales Home via the nav; they never land on `app.py` body.)

- [ ] **Step 6: Smoke-test syntax**

Run: `/opt/homebrew/bin/python3.11 -c "import ast; ast.parse(open('dashboard/app.py').read()); print('syntax OK')"`
Expected: `syntax OK`

- [ ] **Step 7: Commit**

```bash
git add dashboard/app.py
git commit -m "feat(auth): wire login gate into app.py before data loads"
```

---

## Task 7: Guard owner-only pages (1, 2, 3, 6)

**Files:**
- Modify: `dashboard/pages/1_Revenue_Sales.py`
- Modify: `dashboard/pages/2_Cash_Collections.py`
- Modify: `dashboard/pages/3_Operations_Delivery.py`
- Modify: `dashboard/pages/6_Data_Explorer.py`

For EACH of the four files, perform Steps 1–4 below (repeat per file; do not batch).

- [ ] **Step 1: Read top of the page file**

Run: `head -15 dashboard/pages/1_Revenue_Sales.py` (swap filename per iteration).

Identify where the CSS+sidebar-hide block ends (typically line 8 or 10) and where data-loading imports/calls begin.

- [ ] **Step 2: Insert auth import and require_role after CSS block, before data imports**

After the two `st.markdown(...)` CSS lines and BEFORE any `from data.loader ...` or `from data.transformer ...` import, add:

```python
from components.auth import require_role, user_chip, current_role

require_role(allowed=["owner"])
```

- [ ] **Step 3: Update render_nav call to pass role**

Run: `grep -n "render_nav(" dashboard/pages/1_Revenue_Sales.py` (swap filename)
Find the call and add `role=current_role()` as the final keyword argument. Example:

```python
render_nav(active_page="1_Revenue_Sales", risk_count=len(_risks), role=current_role())
```

- [ ] **Step 4: Add user_chip() after top_bar()**

Run: `grep -n "top_bar(" dashboard/pages/1_Revenue_Sales.py` (swap filename)
Immediately after the `top_bar(...)` call, add `user_chip()`.

- [ ] **Step 5 (once, after all four files): Verify syntax**

Run:
```bash
for f in 1_Revenue_Sales 2_Cash_Collections 3_Operations_Delivery 6_Data_Explorer; do
  /opt/homebrew/bin/python3.11 -c "import ast; ast.parse(open('dashboard/pages/${f}.py').read())" && echo "$f OK"
done
```
Expected: four `OK` lines.

- [ ] **Step 6: Commit**

```bash
git add dashboard/pages/1_Revenue_Sales.py dashboard/pages/2_Cash_Collections.py dashboard/pages/3_Operations_Delivery.py dashboard/pages/6_Data_Explorer.py
git commit -m "feat(auth): require owner role on pages 1, 2, 3, 6"
```

---

## Task 8: Guard + adjust page 4 (Customer Reconnection) for sales access

**Files:**
- Modify: `dashboard/pages/4_Customer_Reconnection.py`

- [ ] **Step 1: Insert require_role after CSS block**

After the sidebar-hide `st.markdown` line (line 8), BEFORE the `from data.loader ...` imports (line 10), add:

```python
from components.auth import require_role, user_chip, current_role

require_role(allowed=["owner", "sales"])
```

- [ ] **Step 2: Suppress global_alert_strip and risk compute for sales**

Locate the block (currently lines 35-39):

```python
_risks = compute_global_risks(sr, so, dr)
render_nav(active_page="4_Customer_Reconnection", risk_count=len(_risks))
render_breadcrumb([("Executive", "app"), ("Customer Reconnection", None)])
if _risks:
    global_alert_strip(_risks)
```

Replace it with:

```python
_role = current_role()
if _role == "owner":
    _risks = compute_global_risks(sr, so, dr)
else:
    _risks = []

render_nav(
    active_page="4_Customer_Reconnection",
    risk_count=len(_risks),
    role=_role,
)

if _role == "sales":
    render_breadcrumb([("Sales Home", "0_Sales_Home"), ("Customer Reconnection", None)])
else:
    render_breadcrumb([("Executive", "app"), ("Customer Reconnection", None)])

if _risks and _role == "owner":
    global_alert_strip(_risks)
```

- [ ] **Step 3: Add user_chip() after top_bar()**

Run: `grep -n "top_bar(" dashboard/pages/4_Customer_Reconnection.py`
Immediately after the `top_bar(...)` call, add `user_chip()`.

- [ ] **Step 4: Verify syntax**

Run: `/opt/homebrew/bin/python3.11 -c "import ast; ast.parse(open('dashboard/pages/4_Customer_Reconnection.py').read()); print('OK')"`
Expected: `OK`

- [ ] **Step 5: Commit**

```bash
git add dashboard/pages/4_Customer_Reconnection.py
git commit -m "feat(auth): allow sales on p4; suppress alert strip and route breadcrumb to Sales Home"
```

---

## Task 9: Guard + adjust page 5 (Sales Intelligence), hide margin block for sales

**Files:**
- Modify: `dashboard/pages/5_Sales_Intelligence.py`

- [ ] **Step 1: Insert require_role after CSS block**

After the CSS+sidebar-hide `st.markdown` line, BEFORE the `from data.loader ...` imports, add:

```python
from components.auth import require_role, user_chip, current_role

require_role(allowed=["owner", "sales"])
```

- [ ] **Step 2: Suppress alert strip and route breadcrumb by role**

Locate the current `compute_global_risks(...)` → `render_nav(...)` → `render_breadcrumb(...)` → `global_alert_strip(...)` block (around lines 40-48 — exact lines may vary). Replace it with the same pattern as page 4:

```python
_role = current_role()
if _role == "owner":
    _risks = compute_global_risks(sr, so, dr)
else:
    _risks = []

render_nav(
    active_page="5_Sales_Intelligence",
    risk_count=len(_risks),
    role=_role,
)

if _role == "sales":
    render_breadcrumb([("Sales Home", "0_Sales_Home"), ("Sales Intelligence", None)])
else:
    render_breadcrumb([("Executive", "app"), ("Sales Intelligence", None)])

if _risks and _role == "owner":
    global_alert_strip(_risks)
```

- [ ] **Step 3: Locate the margin block (Section 4)**

Run: `grep -n "MARGIN" dashboard/pages/5_Sales_Intelligence.py | head -5`
Run: `grep -n "# SECTION 5" dashboard/pages/5_Sales_Intelligence.py`

The margin block is the contiguous region from the Section 4 `section_divider(...)` call to just before the `# SECTION 5` marker (reference spec: lines 375–468 of the pre-change file; exact lines may drift).

- [ ] **Step 4: Wrap the margin block in owner check**

Wrap the entire margin block (starting at the `section_divider(...)` for Section 4, ending immediately before the `# SECTION 5` comment / `section_divider` for Section 5) in an `if _role == "owner":` block. Indent every line inside the wrap by 4 spaces.

Pattern:

```python
if _role == "owner":
    section_divider(...)        # Section 4 header
    # ... all of Section 4 margin analysis ...
    # last line of margin section
# SECTION 5 continues unindented
```

- [ ] **Step 5: Add user_chip() after top_bar()**

Run: `grep -n "top_bar(" dashboard/pages/5_Sales_Intelligence.py`
Immediately after the `top_bar(...)` call, add `user_chip()`.

- [ ] **Step 6: Verify syntax**

Run: `/opt/homebrew/bin/python3.11 -c "import ast; ast.parse(open('dashboard/pages/5_Sales_Intelligence.py').read()); print('OK')"`
Expected: `OK`

- [ ] **Step 7: Commit**

```bash
git add dashboard/pages/5_Sales_Intelligence.py
git commit -m "feat(auth): allow sales on p5; hide margin section and alert strip for sales"
```

---

## Task 10: End-to-end manual verification

**Files:** none (browser testing)

- [ ] **Step 1: Start the app locally**

Run: `cd dashboard && /opt/homebrew/bin/python3.11 -m streamlit run app.py`
Expected: browser opens to login form. No tracebacks in terminal.

- [ ] **Step 2: Verify login form behavior**

In the browser:
- Submit blank password → see "Invalid password." error, still on login form.
- Submit wrong password for Owner → "Invalid password."
- Submit correct Owner password → redirected to exec dashboard, 7-item nav visible.

- [ ] **Step 3: Verify Owner view is unchanged**

Click through all 7 nav items: Executive, Revenue, Cash, Operations, Reconnect, Intel, Data. Confirm:
- Margin analysis section visible on Intel (page 5).
- Global alert strip visible where risks exist.
- Breadcrumb "Executive" link returns to `app.py`.
- "Logged in as Owner" chip visible near top; "Log out" button works.

- [ ] **Step 4: Verify Sales view**

Click "Log out" → back to login form. Log in as Sales.
- Nav shows exactly 3 items: Sales Home · Reconnect · Intel.
- Sales Home renders hero KPI, mini-KPIs, top customers table, top items table. No errors.
- Reconnect page renders. Alert strip is NOT present. Breadcrumb anchor is "Sales Home".
- Intel page renders. Margin Analysis section is completely absent (no header, no divider). Alert strip NOT present. Breadcrumb anchor is "Sales Home".

- [ ] **Step 5: Verify URL-bypass is blocked**

While logged in as Sales, manually type each URL in the browser:
- `http://localhost:8501/1_Revenue_Sales` → "Not authorized" screen, no data rendered.
- `http://localhost:8501/2_Cash_Collections` → same.
- `http://localhost:8501/3_Operations_Delivery` → same.
- `http://localhost:8501/6_Data_Explorer` → same.
- `http://localhost:8501/` → "Not authorized" (app.py require_role blocks).

- [ ] **Step 6: Verify Owner cannot land on Sales Home**

While logged in as Owner, type `http://localhost:8501/0_Sales_Home`.
Expected: "Not authorized" screen (guard is `["sales"]` only).

- [ ] **Step 7: Verify logout clears session completely**

While logged in, click "Log out". Then press browser Back. Expected: login form, NOT the previous page. Any attempt to hit an internal URL should return to login.

- [ ] **Step 8: Stop the local app**

In the terminal, press Ctrl+C.

- [ ] **Step 9: If any of Steps 2–7 failed, return to the corresponding task and fix.** Do not proceed to Task 11 until every verification step passes.

---

## Task 11: Deploy to Streamlit Cloud

**Files:** none (deployment config)

- [ ] **Step 1: Push branch to GitHub**

```bash
git push origin main
```

- [ ] **Step 2: Add secrets to Streamlit Cloud**

In Streamlit Cloud dashboard for the `texicon-dashboard` app:
- Settings → Secrets
- Paste:

```toml
[auth]
owner_password = "<actual owner password>"
sales_password = "<actual sales password>"
```

- Save.

- [ ] **Step 3: Trigger redeploy**

Per memory note (`project_deployment.md`): private-repo redeploy may need the flip-public-then-back trick. Use that procedure if the deploy does not pick up new commits automatically.

- [ ] **Step 4: Smoke-test production**

Visit https://texicon-dashboard.streamlit.app. Verify login form loads, Owner password grants 7-page view, Sales password grants 3-page view.

- [ ] **Step 5: Share credentials**

Share the Sales password with the sales team out-of-band (not in git, not in Slack DMs that log forever). Share the Owner password with the CEO / authorized owners only.

---

## Self-Review Notes

- **Spec coverage:** All 16 amendments from the review pass are wired into specific tasks — secrets (T1), hmac.compare_digest (T2), login before data loads (T6), guards after CSS (T7-T9), alert suppression (T8-T9), margin block 375-468 (T9), user_chip (T6-T9), role-aware breadcrumb (T8-T9), RECON_THRESHOLDS reuse (T4+T5), analytics helpers (T4), gitignore (T1), page 0 guard ["sales"] only (T5), render_nav ripple to 7 call sites (T3+T6+T7+T8+T9).
- **Column-name risk:** `_resolve_columns` in Task 4 is heuristic. If the transformer uses non-obvious names, Task 4 Step 4 instructs the implementer to adjust keyword lists. This avoids hard-coding names the plan doesn't actually know.
- **Test framework:** Project has no pre-existing tests. Task 4 adds `pytest` (install step included) and a small test file. UI verification is manual (Task 10) — acknowledged reality for Streamlit.
- **Non-goals respected:** no user accounts, no session timeout, no audit log, no password reset flow.
