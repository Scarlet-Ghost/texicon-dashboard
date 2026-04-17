"""
KPI Definitions Glossary for the Texicon Executive Dashboard.
Used in the Metric Definitions panel on the Executive page.
"""

METRIC_DEFINITIONS = {
    "Net Revenue": {
        "formula": "SUM(NET SALES) for filtered period",
        "description": "Total invoiced revenue after all discounts and deductions. This is the actual amount billed to customers and represents true top-line performance.",
        "threshold": None,
    },
    "Gross Revenue": {
        "formula": "SUM(GROSS SALES) for filtered period",
        "description": "Total revenue before any discounts are applied. The gap between gross and net reveals the discount burden on margins.",
        "threshold": None,
    },
    "Discount Rate": {
        "formula": "(Gross - Net) / Gross x 100%",
        "description": "Percentage of gross sales given as discounts. High rates erode margins and may indicate aggressive pricing or weak negotiation.",
        "threshold": "Warning > 8%, Danger > 12%",
    },
    "Active Customers": {
        "formula": "COUNT DISTINCT(CLIENT) in filtered period",
        "description": "Number of unique customers with at least one purchase. Growth indicates market expansion; decline signals churn risk.",
        "threshold": None,
    },
    "Credit Exposure": {
        "formula": "Credit Sales / Total Sales x 100%",
        "description": "Share of revenue sold on credit terms (30PDC, 60PDC, 90D, 120D). High exposure ties up cash and increases bad debt risk.",
        "threshold": "Warning > 60%, Danger > 70%",
    },
    "Days Sales Outstanding (DSO)": {
        "formula": "Weighted avg of (Term Days x Net Sales) / Total Net Sales",
        "description": "Estimated average days to collect payment based on payment terms. Lower DSO means faster cash conversion.",
        "threshold": "Warning > 45d, Danger > 60d",
    },
    "Fulfillment Rate": {
        "formula": "Delivered Amount / Booked Amount x 100%",
        "description": "Percentage of booked order value that was actually delivered. Low rates indicate supply chain or inventory issues.",
        "threshold": "Target: 95%, Warning < 90%, Danger < 80%",
    },
    "On-Time Delivery": {
        "formula": "Orders delivered within 7 days / Total orders x 100%",
        "description": "Share of orders delivered within a 7-day window from the sales order date. Critical for customer satisfaction and retention.",
        "threshold": "Target: 80%, Warning < 70%",
    },
    "Average Lead Time": {
        "formula": "MEAN(Delivery Date - SO Date) in days",
        "description": "Average number of calendar days between order placement and delivery completion. Tracks operational efficiency.",
        "threshold": "Warning > 14d",
    },
    "Booking Gap": {
        "formula": "(Booked - Invoiced) / Booked x 100%",
        "description": "Difference between booked orders and actual invoiced sales. May indicate cancellations, returns, or unfulfilled orders.",
        "threshold": "Warning > 15%, Danger > 25%",
    },
    "Revenue per Customer": {
        "formula": "Total Net Sales / Active Customers",
        "description": "Average revenue generated per customer. Rising values indicate deepening relationships or successful upselling.",
        "threshold": None,
    },
    "Priority Score (Reconnection)": {
        "formula": "Revenue Share % x Urgency Multiplier",
        "description": "Weighted score combining a customer's revenue importance with their inactivity urgency. Higher scores mean higher re-engagement priority.",
        "threshold": None,
    },
}
