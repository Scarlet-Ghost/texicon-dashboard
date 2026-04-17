"""
Auto-generated executive insights for each dashboard page.
Rule-based text generation from computed metrics.
"""
from components.formatting import format_php, format_pct, format_number, format_days


def generate_executive_insights(metrics):
    """Generate 3-5 plain-English insights for the Executive Dashboard.
    metrics: dict with keys like total_net, discount_pct, credit_pct, fulfillment_pct, etc.
    """
    insights = []

    # Revenue headline
    net = metrics.get("total_net", 0)
    gross = metrics.get("total_gross", 0)
    disc = metrics.get("discount_pct", 0)
    insights.append(
        f"Net revenue reached <strong>{format_php(net)}</strong> "
        f"with a <strong>{format_pct(disc)}</strong> average discount rate"
        + (" — consider tightening discount policies." if disc > 8 else ".")
    )

    # Customer health
    active = metrics.get("active_clients", 0)
    rev_per_cust = net / max(active, 1)
    insights.append(
        f"<strong>{format_number(active)}</strong> active customers generating "
        f"<strong>{format_php(rev_per_cust)}</strong> average revenue each."
    )

    # Credit exposure
    credit_pct = metrics.get("credit_pct", 0)
    if credit_pct > 60:
        insights.append(
            f"Credit exposure is high at <strong>{format_pct(credit_pct)}</strong> of total sales "
            f"— prioritize collections to improve cash position."
        )

    # Fulfillment & delivery
    fulfill = metrics.get("fulfillment_pct", 100)
    on_time = metrics.get("on_time_pct", 100)
    if fulfill < 90 or on_time < 80:
        parts = []
        if fulfill < 90:
            parts.append(f"fulfillment at {format_pct(fulfill)} (target: 95%)")
        if on_time < 80:
            parts.append(f"on-time delivery at {format_pct(on_time)} (target: 80%)")
        insights.append(
            f"Operations need attention: {' and '.join(parts)}."
        )
    else:
        insights.append(
            f"Operations healthy — fulfillment at <strong>{format_pct(fulfill)}</strong>, "
            f"on-time delivery at <strong>{format_pct(on_time)}</strong>."
        )

    # Product concentration
    glyph_pct = metrics.get("glyph_pct", 0)
    if glyph_pct > 15:
        insights.append(
            f"GLYPHOTEX concentration at <strong>{format_pct(glyph_pct)}</strong> "
            f"exceeds the 15% threshold — diversification recommended."
        )

    return insights


def generate_revenue_insights(metrics):
    """Insights for Revenue & Sales page."""
    insights = []
    net = metrics.get("net_sales", 0)
    top_prod = metrics.get("top_product", "N/A")
    top_prod_share = metrics.get("top_product_share", 0)
    top_cust = metrics.get("top_customer", "N/A")
    top_cust_share = metrics.get("top_customer_share", 0)

    insights.append(
        f"Total net sales: <strong>{format_php(net)}</strong> across "
        f"<strong>{format_number(metrics.get('active_clients', 0))}</strong> customers."
    )

    if top_prod_share > 15:
        insights.append(
            f"Top product <strong>{top_prod}</strong> represents "
            f"<strong>{format_pct(top_prod_share)}</strong> of revenue — concentration risk."
        )

    if top_cust_share > 10:
        insights.append(
            f"Largest customer <strong>{top_cust}</strong> accounts for "
            f"<strong>{format_pct(top_cust_share)}</strong> — monitor dependency."
        )

    return insights


def generate_cash_insights(metrics):
    """Insights for Cash Flow & Collections page."""
    insights = []
    dso = metrics.get("est_dso", 0)
    credit_pct = metrics.get("credit_pct", 0)

    if dso > 45:
        insights.append(
            f"Estimated DSO of <strong>{format_days(dso)}</strong> is above the 45-day target "
            f"— consider tightening payment terms or accelerating collections."
        )
    else:
        insights.append(
            f"Estimated DSO of <strong>{format_days(dso)}</strong> is within the 45-day target."
        )

    if credit_pct > 60:
        insights.append(
            f"<strong>{format_pct(credit_pct)}</strong> of sales are on credit terms "
            f"— high exposure requires active receivable management."
        )

    return insights


def generate_operations_insights(metrics):
    """Insights for Operations & Delivery page."""
    insights = []
    fulfill = metrics.get("fulfillment_pct", 100)
    on_time = metrics.get("on_time_pct", 100)
    avg_lead = metrics.get("avg_lead_time", 0)

    if fulfill < 95:
        insights.append(
            f"Fulfillment rate at <strong>{format_pct(fulfill)}</strong> "
            f"(target: 95%) — investigate supply chain bottlenecks."
        )

    if on_time < 80:
        insights.append(
            f"On-time delivery at <strong>{format_pct(on_time)}</strong> "
            f"(target: 80%) — delivery speed needs improvement."
        )

    if avg_lead > 14:
        insights.append(
            f"Average lead time of <strong>{format_days(avg_lead)}</strong> "
            f"exceeds 14-day benchmark."
        )

    if fulfill >= 95 and on_time >= 80:
        insights.append("All operations metrics within target ranges.")

    return insights


def generate_reconnection_insights(metrics):
    """Insights for Customer Reconnection page."""
    insights = []
    fo_count = metrics.get("falling_out_count", 0)
    fo_rev = metrics.get("falling_out_revenue", 0)
    total = metrics.get("total_customers", 0)

    fo_pct = (fo_count / max(total, 1)) * 100
    if fo_pct > 40:
        insights.append(
            f"<strong>{format_pct(fo_pct)}</strong> of customers are Falling Out, "
            f"representing <strong>{format_php(fo_rev)}</strong> in at-risk revenue."
        )
    else:
        insights.append(
            f"Customer health is stable — only {format_pct(fo_pct)} in Falling Out segment."
        )

    return insights
