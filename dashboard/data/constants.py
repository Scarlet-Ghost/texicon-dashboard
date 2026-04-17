import os
from pathlib import Path

DATA_DIR = str(Path(__file__).resolve().parent / "sample")

FILE_NAMES = {
    "sales_report": "2025-2026 (Q1) TEXICON SALES REPORT.xlsx",
    "sales_order": "2025-2026 (Q1) TEXICON DAILY SALES ORDER.xlsx",
    "delivery_report": "2025-2026 (Q1) DAILY DELIVERY REPORT.xlsx",
    "collection_report": "CASHIER DAILY COLLECTION REPORT SAMPLE.xlsx",
}

MONTH_ORDER = {
    "JANUARY": 1, "FEBRUARY": 2, "MARCH": 3, "APRIL": 4,
    "MAY": 5, "JUNE": 6, "JULY": 7, "AUGUST": 8,
    "SEPTEMBER": 9, "OCTOBER": 10, "NOVEMBER": 11, "DECEMBER": 12,
}

PRODUCT_CATEGORY_CLEANUP = {
    "INSECTECIDE": "INSECTICIDE",
    "FUNGICIDES": "FUNGICIDE",
    "NONE": "OTHERS",
}

CLUSTER_CLEANUP = {
    "NOTHERN MINDANAO": "NORTHERN MINDANAO",
}

WAREHOUSE_LABELS = {
    "DVCP": "Davao (DVCP)",
    "FGCP": "FG Compound (FGCP)",
    "IBCP": "Ilocos/Baguio (IBCP)",
    "ISCP": "Isabela (ISCP)",
    "BACP": "Batangas (BACP)",
    "GITSA": "GIT-SA",
    "RMCP": "RM Compound (RMCP)",
    "FGAF": "FG Affiliates (FGAF)",
    "TLCP": "Tolling (TLCP)",
    "QABA": "QA-BA",
}

# --- V6 palette: monochrome canvas + one emerald accent ---
BG_DARK = "#0A0A0B"
BG_CARD = "#101113"
BG_HOVER = "#17181B"
BORDER = "rgba(255,255,255,0.06)"

GREEN_PRIMARY = "#00D68F"
# Aliased so risk_engine / reconnection / sparkline logic still resolves.
GREEN_LIGHT = GREEN_PRIMARY
GREEN_DARK = GREEN_PRIMARY

TEXT_PRIMARY = "#F4F5F6"
TEXT_SECONDARY = "#8A8F98"
TEXT_MUTED = "#5A5F68"

RED = "#F26D6D"
AMBER = "#E2B04A"
BLUE = "#6BA8FF"

# Areas use the accent for the lead series, neutrals for supporting.
AREA_COLORS = {
    "LUZON": GREEN_PRIMARY,
    "VISAYAS": "#8A8F98",
    "MINDANAO": "#B6BAC1",
}

# Products: accent for the top category, neutrals elsewhere. Severity colors
# (red/amber) reserved for payment-term aging where severity is the message.
PRODUCT_COLORS = {
    "HERBICIDE": GREEN_PRIMARY,
    "INSECTICIDE": "#8A8F98",
    "FERTILIZER": "#B6BAC1",
    "FUNGICIDE": "#5A6069",
    "MOLLUSCICIDE": "#3F444C",
    "OTHERS": "#5A5F68",
}

# FT-style muted palette: accent at index 0 tells the story; 1-4 are neutrals
# for context series; 5+ are semantic colors used only when intentional.
CHART_COLORS = [
    "#00D68F",  # accent (primary series)
    "#8A8F98",  # neutral 1
    "#B6BAC1",  # neutral 2
    "#5A6069",  # neutral 3
    "#3F444C",  # neutral 4
    "#6BA8FF",  # info
    "#E2B04A",  # warn
    "#F26D6D",  # danger
    "#A682FF",  # purple
    "#4ECCA3",  # accent-soft teal
]

# Cash → credit severity gradient. Semantic: accent for cash-on-delivery,
# neutral for short terms, amber → red as overdue risk grows.
PAYMENT_TERM_COLORS = {
    "COD":    "#00D68F",
    "CBD":    "#00D68F",
    "CASH":   "#00D68F",
    "15D":    "#B6BAC1",
    "15PDC":  "#B6BAC1",
    "30D":    "#E2B04A",
    "30PDC":  "#E2B04A",
    "45D":    "#D39B3C",
    "60D":    "#C78A30",
    "60PDC":  "#BB7A26",
    "90D":    "#F26D6D",
    "90PDC":  "#D55555",
    "120D":   "#B94343",
    "120PDC": "#9E3636",
    "INDENT": "#5A6069",
}

PHP_SYMBOL = "\u20B1"

# FT-minimal Plotly template: chart titles live in section_card_header,
# x-axis has no gridlines, y-axis has faint gridlines only, legend sits
# below-left. Direct-labeling via annotate_last_point() is preferred over
# legends on line charts.
PLOTLY_LAYOUT = dict(
    font=dict(family="Inter, -apple-system, BlinkMacSystemFont, system-ui, sans-serif",
              color=TEXT_PRIMARY, size=12),
    plot_bgcolor="rgba(0,0,0,0)",
    paper_bgcolor="rgba(0,0,0,0)",
    margin=dict(l=8, r=8, t=8, b=8),
    colorway=CHART_COLORS[:5],
    xaxis=dict(
        showgrid=False, zeroline=False, showline=False,
        ticks="outside", ticklen=4, tickcolor="rgba(255,255,255,0.1)",
        tickfont=dict(color=TEXT_MUTED, size=11),
        title=dict(font=dict(color=TEXT_MUTED, size=11)),
        automargin=True,
    ),
    yaxis=dict(
        showgrid=True, gridcolor="rgba(255,255,255,0.04)", gridwidth=1,
        zeroline=False, showline=False,
        tickfont=dict(color=TEXT_MUTED, size=11),
        title=dict(font=dict(color=TEXT_MUTED, size=11)),
        automargin=True,
    ),
    legend=dict(
        orientation="h", yanchor="top", y=-0.18, xanchor="left", x=0,
        font=dict(size=11, color=TEXT_SECONDARY),
        bgcolor="rgba(0,0,0,0)",
    ),
    hoverlabel=dict(
        bgcolor="#17181B", font_size=12, font_color=TEXT_PRIMARY,
        bordercolor="rgba(255,255,255,0.08)",
        namelength=-1,
    ),
    height=320,
    bargap=0.32,
    bargroupgap=0.08,
)

# Currency-specific axis (PHP abbreviated: ₱1M, ₱50K)
PHP_TICK_FORMAT = ",.2s"
PHP_TICK_PREFIX = "\u20B1"

# --- Customer Reconnection Segmentation ---
# Thresholds calibrated for agricultural B2B purchasing cycles
# (wider than SMIFP's 10/15 days for F&B)
RECON_THRESHOLDS = {
    "high_potential": 30,   # Last purchase within 30 days
    "at_risk": 90,          # Last purchase 31-90 days ago
    # > 90 days = Falling Out
}

RECON_URGENCY = {
    "Falling Out": 1.5,
    "At Risk": 1.0,
    "High Potential": 0.5,
}

RECON_COLORS = {
    "Falling Out": RED,
    "At Risk": AMBER,
    "High Potential": GREEN_PRIMARY,
}

RECON_SEGMENT_ORDER = ["Falling Out", "At Risk", "High Potential"]

RECON_EXCLUDE_CLIENTS = ["CASH SALES"]

# --- KPI Targets (used for target lines on charts) ---
KPI_TARGETS = {
    "fulfillment_rate": {"value": 95, "label": "Target: 95%", "color": BLUE},
    "on_time_delivery": {"value": 80, "label": "Target: 80%", "color": BLUE},
    "discount_rate_max": {"value": 8, "label": "Max: 8%", "color": RED},
    "dso_max": {"value": 45, "label": "Target: <45d", "color": RED},
    "credit_exposure_max": {"value": 60, "label": "Max: 60%", "color": RED},
}
