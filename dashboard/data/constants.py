import os

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "Sample Documents")

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

# --- Texicon Brand Colors (Dark Theme) ---
BG_DARK = "#111B14"
BG_CARD = "#1A2B1E"
BG_HOVER = "#223326"
BORDER = "#2E4A34"

GREEN_PRIMARY = "#4CAF50"
GREEN_LIGHT = "#81C784"
GREEN_DARK = "#2E7D32"

TEXT_PRIMARY = "#E0E0E0"
TEXT_SECONDARY = "#78909C"
TEXT_MUTED = "#546E7A"

RED = "#EF5350"
AMBER = "#FFA726"
BLUE = "#42A5F5"

AREA_COLORS = {
    "LUZON": "#4CAF50",
    "VISAYAS": "#81C784",
    "MINDANAO": "#A5D6A7",
}

PRODUCT_COLORS = {
    "HERBICIDE": "#4CAF50",
    "INSECTICIDE": "#66BB6A",
    "FERTILIZER": "#FFA726",
    "FUNGICIDE": "#42A5F5",
    "MOLLUSCICIDE": "#AB47BC",
    "OTHERS": "#78909C",
}

CHART_COLORS = [
    "#4CAF50",
    "#81C784",
    "#FFA726",
    "#42A5F5",
    "#AB47BC",
    "#EF5350",
    "#26C6DA",
    "#FF7043",
    "#9CCC65",
    "#5C6BC0",
]

PHP_SYMBOL = "\u20B1"

# Dark plotly template
PLOTLY_LAYOUT = dict(
    font=dict(family="Inter, system-ui, -apple-system, sans-serif", color=TEXT_PRIMARY, size=12),
    plot_bgcolor="rgba(0,0,0,0)",
    paper_bgcolor="rgba(0,0,0,0)",
    margin=dict(l=10, r=10, t=10, b=10),
    xaxis=dict(
        showgrid=False, zeroline=False,
        tickfont=dict(color=TEXT_SECONDARY, size=10),
        title=None,
    ),
    yaxis=dict(
        showgrid=True, gridcolor="rgba(46,74,52,0.3)", zeroline=False,
        tickfont=dict(color=TEXT_SECONDARY, size=10),
        title=None,
    ),
    legend=dict(
        orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1,
        font=dict(size=10, color=TEXT_SECONDARY),
        bgcolor="rgba(0,0,0,0)",
    ),
    hoverlabel=dict(bgcolor=BG_CARD, font_size=12, font_color=TEXT_PRIMARY, bordercolor=BORDER),
    height=320,
    bargap=0.3,
)

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
