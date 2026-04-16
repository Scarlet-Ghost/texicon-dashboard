# Texicon Executive Dashboard

Interactive executive dashboard for **Texicon Group** (Agricultural Chemicals, Philippines) built with Streamlit, Plotly, and Pandas. Dark-themed with Texicon brand colors, styled after the SMIFP executive dashboard presentation.

---

## Quick Start

```bash
cd "/Users/dxp/Desktop/Personal/07_KKP/01_Texicon/dashboard"
/opt/homebrew/bin/python3.11 -m pip install -r requirements.txt
/opt/homebrew/bin/python3.11 -m streamlit run app.py
```

Opens at **http://localhost:8501**

---

## Pages

| Page | Purpose | Key Metrics |
|------|---------|-------------|
| **Executive Dashboard** (app.py) | High-level overview, risk alerts | Net Revenue, Credit Exposure, DSO, Fulfillment, On-Time Delivery |
| **Revenue & Sales** | Sales performance deep-dive | Revenue trends, product/customer/geographic concentration, sales rep rankings |
| **Cash Flow & Collections** | Accounts receivable analysis | AR aging, DSO scenarios, payment terms compliance, credit exposure by customer |
| **Operations & Delivery** | Fulfillment and logistics | Fulfillment funnel, cycle time, warehouse throughput, service levels |
| **Customer Reconnection** | Customer re-engagement analytics | Segment distribution (High Potential / At Risk / Falling Out), priority scoring, transaction history |

---

## Data Sources

All source files are Excel (.xlsx) located in `../Sample Documents/`:

| File | Rows | Period | Content |
|------|------|--------|---------|
| `2025-2026 (Q1) TEXICON SALES REPORT.xlsx` | 7,213 | Jan 2025 - Mar 2026 | Invoices: client, product, area, pricing, payment terms |
| `2025-2026 (Q1) TEXICON DAILY SALES ORDER.xlsx` | 7,646 | Jan 2025 - Jun 2025 | Orders: booking amounts, delivery dates, warehouses |
| `2025-2026 (Q1) DAILY DELIVERY REPORT.xlsx` | 7,228 | Jan 2025 - Mar 2025 | Deliveries: warehouse, qty, delivered amount |
| `CASHIER DAILY COLLECTION REPORT SAMPLE.xlsx` | 35 | Apr 6-10, 2026 | Sample: collections, EWT, bank deposits |

### Data Pipeline

```
Excel Files
    |
    v
data/loader.py          @st.cache_data (1hr TTL)
    |                    Read Excel via openpyxl
    v
data/transformer.py     Clean columns, parse dates, compute derived fields
    |                    (IS_CREDIT, CYCLE_DAYS, DISCOUNT_PCT, YEAR_MONTH, etc.)
    v
data/reconnection.py    Customer segmentation & priority scoring (Reconnection page)
    |
    v
components/filters.py   Period buttons + dropdown filters
    |                    (Q1 2025 / Q1 2026 / Full Period / Custom)
    v
apply_filters_*()       Boolean mask filtering per DataFrame type
    |
    v
Page rendering          KPI cards, charts, tables, alerts
```

### Data Cleaning Applied

| Issue | Fix |
|-------|-----|
| NET SALES / GROSS SALES contain string dashes `' -   '` | `pd.to_numeric(errors='coerce').fillna(0)` |
| PRODUCT CATEGORY typos: `INSECTECIDE`, `FUNGICIDES` | Normalized via lookup dict |
| CLUSTER typo: `NOTHERN MINDANAO` | Mapped to `NORTHERN MINDANAO` |
| Column names with trailing spaces (`ORIGINAL PRICE `) | `df.columns.str.strip()` |
| Collection Report: headers at row 3, ~1M phantom rows | `header=3`, `dropna(how='all')` |
| Sales Order: 1 row with negative cycle days | `clip(lower=0)` |

---

## Project Structure

```
dashboard/
├── app.py                          # Executive Dashboard (landing page)
├── requirements.txt                # Python dependencies
├── README.md                       # This file
│
├── .streamlit/
│   └── config.toml                 # Streamlit theme (dark, green primary)
│
├── assets/
│   └── style.css                   # Full dark-theme CSS (~700 lines)
│
├── data/
│   ├── __init__.py
│   ├── constants.py                # Colors, file paths, cleanup rules, Plotly layout,
│   │                               # reconnection thresholds & segment config
│   ├── loader.py                   # 4x cached Excel loaders
│   ├── transformer.py              # Data cleaning + feature engineering
│   └── reconnection.py             # Customer segmentation engine (build_reconnection_data,
│                                   # get_customer_transactions, get_segment_summary)
│
├── components/
│   ├── __init__.py
│   ├── filters.py                  # Top-bar period buttons + dropdown filters
│   ├── drawers.py                  # UI components (KPI cards, tables, alerts, badges,
│   │                               # section cards, risk headers, all-clear box)
│   ├── charts.py                   # 12 Plotly chart factory functions
│   ├── kpi_cards.py                # KPI row layout helper
│   └── formatting.py               # PHP currency, %, number formatters
│
└── pages/
    ├── 1_Revenue_Sales.py          # Revenue & Sales page
    ├── 2_Cash_Collections.py       # Cash Flow & Collections page
    ├── 3_Operations_Delivery.py    # Operations & Delivery page
    └── 4_Customer_Reconnection.py  # Customer Reconnection page
```

---

## Architecture

### Presentation Style (SMIFP-inspired)

The dashboard follows the SMIFP executive dashboard presentation patterns:

- **Georgia serif font** on KPI values, page titles, section headings, and comparison card values for an executive/financial feel
- **Box shadows** on all card types (KPI, mini, compare, section, risk) and expanders for visual depth
- **Section cards** — chart groups wrapped in `st.container(border=True)` with `section_card_header(title, subtitle)` providing a card header with serif title + subtitle + divider
- **KPI card icons** — each KPI card has an optional icon rendered in a tinted rounded box (green/warning/danger/neutral variants)
- **Mini card icons** — summary stat cards include small icon boxes
- **Risk Alerts with badge** — risk section shows a count badge (red pill with count, or green "0"), 2-column grid layout, and an "All Clear" green success box when no risks are detected
- **Consistent spacing** — `.section-gap` class (24px) replaces ad-hoc `<br>` tags throughout
- **Risk Alerts positioned high** — after Revenue Concentration, before collapsible deep-dive sections

### Filter System

Filters render at the **top of every page** (no sidebar). Shared via `components/filters.py`.

**Period Buttons** use `st.session_state.period` to persist selection across reruns:
- **Q1 2025**: Filters to Jan 1 - Mar 31, 2025
- **Q1 2026**: Filters to Jan 1 - Mar 31, 2026
- **Full Period**: No date filtering (shows all data)
- **Custom**: Shows date pickers for manual range

**Dropdown Filters** appear in a collapsible "More Filters" expander:
- Area Group (Luzon / Visayas / Mindanao)
- Product Category (Herbicide, Insecticide, Fertilizer, etc.)
- Payment Terms (COD, 30PDC, 60PDC, etc.)
- Warehouse (DVCP, FGCP, IBCP, etc.)

Each page uses a unique `page_key` to avoid widget key conflicts.

### Component Pattern

All UI components are stateless functions that emit HTML via `st.markdown(unsafe_allow_html=True)`:

```python
# drawers.py exports:
kpi_card(label, value, delta, delta_label, value_class, sub_text, icon, icon_class)
mini_card(label, value, icon)
compare_card(label, current, previous, delta_text, delta_up)
section_card_header(title, subtitle)     # Serif title + subtitle + divider (use inside st.container(border=True))
alert_banner(message, alert_type)        # "red" | "amber" | "blue" | "green"
risk_card(title, description, risk_type)
risk_section_header(title, count)        # Section heading with count badge
all_clear_box(message)                   # Green "no risks" confirmation
insight_card(message, insight_type)      # "info" | "warning" | "danger"
section_header(title)
styled_table(headers, rows, green_cols)
concentration_bar(segments)              # [(label, pct, color), ...]
badge(text, badge_type)                  # Returns HTML string
top_bar(data_date, current_time)
```

### Chart Factory

All charts in `components/charts.py` share a dark-theme Plotly layout defined in `data/constants.py`:
- Transparent backgrounds (integrates with dark CSS)
- Muted grid lines (#2E4A34)
- Light text (#E0E0E0 primary, #78909C secondary)
- Consistent hover labels
- PHP (₱) formatting in tooltips

```python
# charts.py exports:
bar_chart(df, x, y, ...)           # Vertical/horizontal bar
horizontal_bar(df, x, y, ...)     # Horizontal bar (reversed y)
donut_chart(labels, values, ...)   # Donut with optional center text
line_bar_combo(df, x, bar_y, ...)  # Dual bar + line overlay
stacked_bar(df, x, y, color, ...) # Stacked bar
area_chart(df, x, y_cols, ...)     # Stacked area
treemap_chart(df, path, values)    # Hierarchical treemap
funnel_chart(stages, values)       # Funnel with % labels
histogram_chart(df, x, nbins)     # Distribution histogram
box_chart(df, x, y)               # Box plot
gauge_chart(value, max_val)        # Gauge with thresholds
```

### Customer Reconnection Module

Adapted from the SMIFP Next.js reconnection module for Streamlit/Excel (read-only analytics, no contact logging).

**Segmentation** (by days since last purchase):
| Segment | Threshold | Urgency Multiplier |
|---------|-----------|-------------------|
| High Potential | <= 30 days | 0.5 |
| At Risk | 31-90 days | 1.0 |
| Falling Out | > 90 days | 1.5 |

**Priority Score** = `(customer_revenue / max_revenue * 100) * urgency_multiplier`

Thresholds are wider than SMIFP's 10/15 days because agricultural B2B has longer purchase cycles.

The "CASH SALES" pseudo-client is excluded from the customer list.

---

## Key Metrics Computed

### Revenue (from Sales Report)

| Metric | Formula |
|--------|---------|
| Net Sales | `SUM(NET SALES)` |
| Gross Sales | `SUM(GROSS SALES)` |
| Discount Rate | `(Gross - Net) / Gross * 100` |
| Active Clients | `COUNT DISTINCT(CLIENT)` |
| Credit Exposure | `SUM(NET SALES where IS_CREDIT=True) / Total Net * 100` |

### Cash Flow (from Sales Report + Collection Report)

| Metric | Formula |
|--------|---------|
| Estimated DSO | `SUM(term_days * net_sales) / SUM(net_sales)` for credit transactions |
| AR Aging | Days since invoice grouped into 0-30, 31-60, 61-90, 91-180, 180+ buckets |
| Collection Rate | `Total Collected / Total Credit Sales * 100` |

### Operations (from Sales Order + Delivery Report)

| Metric | Formula |
|--------|---------|
| Fulfillment Rate | `Total Delivered Value / Total Booking Value * 100` |
| On-Time Delivery | `Orders with CYCLE_DAYS <= 7 / Total Orders * 100` |
| Avg Lead Time | `MEAN(Delivery Date - SO Date)` in days |
| Booking-Invoice Gap | `(Total Bookings - Net Sales) / Total Bookings * 100` |

### Risk Thresholds

| Alert | Condition |
|-------|-----------|
| Product Concentration | GLYPHOTEX > 15% of revenue |
| High Credit Exposure | Credit sales > 60% of total |
| Delivery Performance | On-time < 70% |
| Fulfillment Gap | Booking gap > 15% |

---

## Executive Dashboard Flow

The main page (`app.py`) follows this section order (matching SMIFP):

1. **Top Bar** — "Data as of" date + current time
2. **Page Title** — "Executive Dashboard" (Georgia serif)
3. **KPI Cards** (7) — Qty, Gross, Net, Discount, GP/Unit, Active Customers, Credit Exposure (each with icon)
4. **Mini Summary Row** (5) — Top Product, Top Customer, Top Region, Avg Order, Rev/Customer (each with icon)
5. **Comparison Row** (5) — Net Revenue, Delivered Value, Discount, DSO, On-Time Delivery (with badges)
6. **Monthly Revenue + Product Mix** — Line-bar combo + donut (in section cards)
7. **Revenue Concentration + Revenue Mix** — Concentration bar + top 10 table + area chart (in section cards)
8. **Risk Alerts** — Count badge, 2-column grid, or "All Clear" box
9. **Operations Overview** (collapsible) — Fulfillment, lead time, warehouses
10. **Customer Economics** (collapsible) — Loyalty tiers, geographic split
11. **Working Capital** (collapsible, collapsed by default) — Credit, DSO, collections

---

## Theme & Styling

**Color Palette** (Texicon brand green on dark):

| Token | Hex | Usage |
|-------|-----|-------|
| `BG_DARK` | `#111B14` | Page background |
| `BG_CARD` | `#1A2B1E` | Card/component background |
| `BORDER` | `#2E4A34` | Card borders, dividers |
| `GREEN_PRIMARY` | `#4CAF50` | KPI values, active states, positive deltas |
| `GREEN_LIGHT` | `#81C784` | Secondary green, info text |
| `TEXT_PRIMARY` | `#E0E0E0` | Headings, main text |
| `TEXT_SECONDARY` | `#78909C` | Labels, subtitles |
| `RED` | `#EF5350` | Danger values, risk alerts |
| `AMBER` | `#FFA726` | Warning values, caution alerts |
| `BLUE` | `#42A5F5` | Info banners, accent charts |

**Chart Palette** (10 colors): `#4CAF50`, `#81C784`, `#FFA726`, `#42A5F5`, `#AB47BC`, `#EF5350`, `#26C6DA`, `#FF7043`, `#9CCC65`, `#5C6BC0`

---

## Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| streamlit | >= 1.32.0 | Web framework |
| pandas | >= 2.0.0 | Data manipulation |
| plotly | >= 5.18.0 | Interactive charts |
| openpyxl | >= 3.1.0 | Excel file reading |
| numpy | >= 1.24.0 | Numerical operations |

**Python:** 3.11 (`/opt/homebrew/bin/python3.11`)

---

## Known Limitations

1. **Collection data is sample-only** (35 rows, Apr 6-10, 2026). AR aging and DSO are estimates based on invoice dates and payment terms, not actual collection receipts.
2. **No real-time data** — reads from static Excel files cached for 1 hour.
3. **Single-user** — Streamlit session state is per-browser-session.
4. **Hard-coded term days** — Payment terms to days mapping (`30PDC -> 30`, `60PDC -> 60`, etc.) is hard-coded in each page that needs it.
5. **No authentication** — open access on the network URL.
6. **No contact logging** — Customer Reconnection is read-only analytics (no database for follow-up tracking).
