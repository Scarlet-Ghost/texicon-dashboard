"""
Centralized tooltip text for all dashboard components.
Each tooltip should be 1-2 sentences, accurate, and helpful for executives.
"""

# ============================================
# EXECUTIVE DASHBOARD (app.py)
# ============================================
EXEC = {
    # KPI Row 1
    "total_qty": "Total liters/kilograms of agricultural chemicals sold in the selected period.",
    "gross_sales": "Total revenue before any discounts or deductions are applied.",
    "net_revenue": "Revenue after discounts. This is the actual amount invoiced to customers.",
    "discount_rate": "Percentage of gross sales given as discounts. High rates may erode margins.",
    "gp_per_unit": "Average net revenue per liter/kilogram sold. A proxy for unit-level profitability.",

    # KPI Row 2 (mini cards)
    "active_customers": "Number of unique customers with at least one purchase in the selected period.",
    "credit_exposure": "Share of total sales on credit terms (not COD/CBD). Higher values increase cash flow risk.",
    "top_product": "The single product generating the most net revenue. High share means dependency risk.",
    "top_customer": "The customer contributing the most net revenue in this period.",
    "top_region": "The area group with the highest total net sales.",

    # Compare cards
    "avg_order_size": "Average net revenue per invoice. Tracks whether order values are growing.",
    "rev_per_customer": "Total net revenue divided by active customers. Measures customer quality.",
    "fulfillment_rate": "Percentage of booked order value actually delivered. Below 90% signals supply chain issues.",
    "avg_lead_time": "Average days from sales order to delivery. Longer times risk customer dissatisfaction.",
    "dso": "Estimated days to collect payment, weighted by invoice terms. Lower is better for cash flow.",

    # Chart sections
    "monthly_revenue": "Monthly net vs gross revenue trend. The gap between bars and line shows discount impact.",
    "product_mix": "Revenue share by product category. Diversification reduces supply chain and market risk.",
    "revenue_concentration": "How revenue is spread across customers. Top-heavy distribution = higher risk if a key customer churns.",
    "category_trend": "Monthly shift in product category mix. Reveals seasonal patterns and portfolio shifts.",
    "area_performance": "Revenue by geographic area. Identifies strongest and weakest performing regions.",
    "payment_terms": "Distribution of payment terms across sales. More credit terms = higher cash flow risk.",

    # Risk alerts
    "risk_product_conc": "Triggered when a single product exceeds 15% of total revenue, creating supply dependency.",
    "risk_credit_exp": "Triggered when credit sales exceed 60% of total, increasing receivable and cash flow risk.",
    "risk_delivery": "Triggered when on-time delivery rate falls below 70%, risking customer satisfaction.",
    "risk_fulfillment": "Triggered when booking-to-invoice gap exceeds 15%, indicating unfulfilled orders.",
}

# ============================================
# REVENUE & SALES (page 1)
# ============================================
REVENUE = {
    "net_sales": "Total invoiced revenue after all discounts for the selected period.",
    "gross_sales": "Total revenue before discounts. Compare with net to see discount impact.",
    "discount_rate": "Average discount given as a percentage of gross sales.",
    "active_clients": "Count of unique customers who made at least one purchase.",
    "avg_transaction": "Average revenue per invoice. Higher values indicate larger order sizes.",

    "revenue_trend": "Monthly net sales (bars) overlaid with gross sales (line). The gap reveals discount trends.",
    "area_split": "Revenue breakdown by geographic area (Luzon, Visayas, Mindanao).",
    "top_products": "The 10 highest-revenue products. Watch for over-concentration in one product.",
    "top_customers": "The 10 highest-revenue customers and their share of total sales.",
    "product_categories": "Revenue by product type (Herbicide, Insecticide, Fungicide, etc.).",
    "sales_reps": "Revenue attributed to each sales representative.",
    "geographic": "Treemap showing revenue hierarchy: Area Group > Cluster.",
    "payment_dist": "Share of sales by payment term type (COD, 30PDC, 60PDC, etc.).",
    "terms_by_area": "How payment terms vary by region. Reveals credit-heavy areas.",
    "concentration_risk": "Warning when top 5 products exceed 40% of total revenue.",
}

# ============================================
# CASH FLOW & COLLECTIONS (page 2)
# ============================================
CASH = {
    "credit_sales_ar": "Estimated accounts receivable based on credit-term invoices. Actual AR may differ from this estimate.",
    "est_dso": "Days Sales Outstanding estimated from weighted payment terms. Not based on actual collection dates.",
    "credit_exposure": "Percentage of total sales made on credit. Higher exposure means more cash tied up in receivables.",
    "collections_total": "Total cash collected in the sample period. Based on limited sample data only.",
    "monthly_credit": "Average monthly value of credit sales. Useful for planning cash reserves.",

    "credit_cash_split": "Proportion of sales on credit vs cash/COD terms.",
    "ar_aging": "Estimated aging of receivables by payment term buckets (0-30d, 31-60d, etc.).",
    "top_credit_exposure": "Customers with the largest outstanding credit amounts. Key collection targets.",
    "terms_over_time": "Monthly shift in payment term mix. Tracks if credit usage is increasing.",
    "compliance_30d": "Estimated on-time payment rate for 30-day PDC terms. Based on sample data only.",
    "compliance_60d": "Estimated on-time payment rate for 60-day PDC terms. Based on sample data only.",
    "dso_scenario": "What-if tool: adjust target DSO to see potential cash freed from faster collections.",
    "collection_activity": "Daily collection trends from the sample period (Apr 6-10, 2026 only).",
}

# ============================================
# OPERATIONS & DELIVERY (page 3)
# ============================================
OPERATIONS = {
    "fulfillment_rate": "Percentage of booked order value actually delivered. Target: 95%.",
    "on_time": "Orders delivered within 7 calendar days of the sales order date. Target: 80%.",
    "avg_lead_time": "Mean days from order to delivery. Lower is better for customer satisfaction.",
    "total_deliveries": "Count of delivery transactions in the selected period.",
    "booking_gap": "Difference between booked and invoiced amounts as a percentage. May indicate cancellations or unfulfilled orders.",

    "fulfillment_funnel": "Value flow from Bookings to Deliveries to Invoices. Drops reveal where orders are lost.",
    "delivery_trend": "Monthly delivery count and value. Tracks operational throughput over time.",
    "warehouse_split": "Distribution of deliveries across warehouses. Identifies busiest facilities.",
    "cycle_time_dist": "Distribution of order-to-delivery days. Outliers beyond 30d need investigation.",
    "cycle_by_warehouse": "Box plot comparing delivery speed across warehouses. Reveals efficiency gaps.",
    "warehouse_throughput": "Monthly delivery value by warehouse. Tracks capacity utilization.",
    "delivery_by_dow": "Deliveries by day of week. Identifies peak shipping days for resource planning.",
    "channel_mix": "Booking distribution by group/channel name.",
    "backlog": "Orders with future delivery dates. Grouped by urgency (0-30d, 31-60d, etc.).",
}

# ============================================
# CUSTOMER RECONNECTION (page 4)
# ============================================
RECONNECT = {
    "falling_out": "Customers with no purchase in 90+ days. Highest priority for re-engagement outreach.",
    "at_risk": "Customers inactive for 31-90 days. May be evaluating competitors.",
    "high_potential": "Recently active customers (within 30 days). Maintain relationship momentum.",
    "total_customers": "Total unique customers excluding cash sales transactions.",
    "priority_score": "Combines revenue value and inactivity urgency. Higher score = more important to re-engage.",

    "segment_distribution": "Customer count by health segment. Healthy mix has more High Potential than Falling Out.",
    "segment_revenue": "Revenue at risk in each segment. Shows financial impact of customer churn.",
    "customer_list": "Sortable list of customers with segment, revenue, and inactivity details.",
    "segments_by_area": "Geographic distribution of customer segments. Identifies regions with churn problems.",
    "falling_out_by_rep": "Sales reps with the most Falling Out customers. Highlights where follow-up is needed.",
}

# ============================================
# SALES INTELLIGENCE (page 5)
# ============================================
INTEL = {
    # Q1 YoY
    "q1_revenue_25": "Q1 2025 total net revenue. Baseline for year-over-year comparison.",
    "q1_revenue_26": "Q1 2026 total net revenue. Compare against 2025 to gauge growth.",
    "revenue_growth": "Year-over-year change in Q1 net sales. Positive means business is growing.",
    "client_growth": "Change in unique customer count between Q1 periods.",
    "volume_growth": "Year-over-year change in total quantity (L/KG) sold.",
    "monthly_comparison": "Side-by-side monthly revenue for Q1 2025 vs Q1 2026.",
    "new_clients": "Customers who purchased in Q1 2026 but not Q1 2025.",
    "lost_clients": "Customers who purchased in Q1 2025 but not Q1 2026.",
    "top_gainers": "Products with the largest revenue increase from Q1 2025 to Q1 2026.",
    "top_decliners": "Products with the largest revenue decrease year-over-year.",

    # Bundles & Pairings
    "multi_item_pct": "Share of invoices with more than one product. Higher = better cross-selling.",
    "co_purchased": "Products frequently bought together. Useful for bundle pricing strategies.",
    "bundle_revenue": "Revenue opportunity from commonly paired products.",

    # Customer Behavior
    "basket_size": "Average number of unique products per invoice. Higher means better cross-selling.",
    "purchase_freq": "Average number of orders per customer in the period.",
    "avg_order_value": "Average net revenue per order across all customers.",
    "single_item_pct": "Share of invoices with only one product. Cross-sell opportunity.",
    "customer_segments": "Segmentation by purchase behavior: Power/Bulk/Regular/Light buyers.",
    "freq_distribution": "How purchase frequency is distributed across customers.",
    "dow_patterns": "Which days of the week see the most orders. Useful for staffing and promotions.",
    "power_buyers": "Top customers by order frequency and product diversity.",

    # Margin & Pricing
    "avg_discount": "Mean discount rate across all transactions. Rising rates erode margins.",
    "avg_unit_price": "Average net price per unit. Falling prices signal pricing pressure.",
    "margin_risk_items": "Count of products with declining prices or rising discounts.",
    "discount_by_category": "Discount rates by product category. Identifies where discounting is heaviest.",
    "discount_by_client": "Customers receiving the highest discount rates.",
    "price_erosion": "Products where unit price dropped year-over-year. Potential margin risk.",

    # Daily Breakdown
    "best_day": "Single day with the highest net revenue.",
    "worst_day": "Single day with the lowest net revenue.",
    "avg_daily_rev": "Average daily revenue across the period.",
    "daily_trend": "Day-by-day revenue chart. Identifies spikes, dips, and patterns.",
    "weekly_summary": "Revenue aggregated by week number for trend analysis.",
}

# ============================================
# DATA EXPLORER (page 6)
# ============================================
DATA_EXPLORER = {
    # Sales Report tab
    "sr_total_records": "Number of invoice line items matching the current filters.",
    "sr_net_revenue": "Sum of net sales (after discounts) for all filtered records.",
    "sr_gross_revenue": "Sum of gross sales (before discounts) for all filtered records.",
    "sr_total_qty": "Total quantity in liters/kilograms across filtered records.",
    "sr_avg_discount": "Mean discount percentage across all filtered transactions.",
    "sr_active_clients": "Count of unique customers in the filtered data set.",

    # Sales Orders tab
    "so_total_orders": "Number of sales order records matching current filters.",
    "so_total_booking": "Sum of all booking amounts for filtered orders.",
    "so_total_qty": "Total ordered quantity across filtered records.",
    "so_avg_unit_price": "Average unit price across all filtered order items.",
    "so_avg_cycle": "Mean days from sales order date to delivery date.",
    "so_unique_customers": "Count of unique customers in filtered orders.",

    # Delivery Report tab
    "dr_total_deliveries": "Number of delivery records matching current filters.",
    "dr_total_qty": "Total delivered quantity across filtered records.",
    "dr_total_amount": "Sum of delivered amounts for all filtered records.",
    "dr_avg_price": "Average unit price (VAT inclusive) across filtered deliveries.",
    "dr_active_warehouses": "Number of distinct warehouses in the filtered data.",

    # Collection Report tab
    "cr_total_records": "Number of collection records matching current filters.",
    "cr_total_collected": "Sum of all collected amounts in the filtered data.",
    "cr_unique_customers": "Count of unique customers in filtered collection records.",
}
