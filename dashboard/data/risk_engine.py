"""
Centralized risk computation engine.
Extracted from app.py so risks can be surfaced on every page.
"""
import pandas as pd


def compute_global_risks(sr_f, so_f, dr_f):
    """Compute all risk alerts from filtered data.
    Returns a list of dicts: [{"title": str, "desc": str, "type": "danger"|"warning"}, ...]
    """
    risks = []

    # --- Metric computations ---
    total_net = sr_f["NET SALES"].sum() if "NET SALES" in sr_f.columns else 0
    total_gross = sr_f["GROSS SALES"].sum() if "GROSS SALES" in sr_f.columns else 0
    total_bookings = so_f["Booking Amount"].sum() if "Booking Amount" in so_f.columns else 0

    # Credit exposure
    credit_mask = sr_f["IS_CREDIT"] if "IS_CREDIT" in sr_f.columns else pd.Series(False, index=sr_f.index)
    credit_net = sr_f.loc[credit_mask, "NET SALES"].sum() if credit_mask.any() else 0
    credit_pct = (credit_net / total_net * 100) if total_net > 0 else 0

    # Fulfillment & delivery
    total_delivered = dr_f["Delivered Amount"].sum() if "Delivered Amount" in dr_f.columns else 0
    fulfillment_pct = (total_delivered / total_bookings * 100) if total_bookings > 0 else 100

    # On-time delivery
    if "CYCLE_DAYS" in so_f.columns:
        valid_cycle = so_f["CYCLE_DAYS"].dropna()
        on_time_pct = (valid_cycle.le(7).sum() / max(len(valid_cycle), 1)) * 100
    else:
        on_time_pct = 100

    # Booking gap
    gap_pct = ((total_bookings - total_net) / total_bookings * 100) if total_bookings > 0 else 0

    # Product concentration (GLYPHOTEX)
    if "ITEM" in sr_f.columns and total_net > 0:
        item_rev = sr_f.groupby("ITEM")["NET SALES"].sum()
        glyph = item_rev[item_rev.index.str.contains("GLYPHOTEX", case=False, na=False)]
        glyph_pct = (glyph.sum() / total_net * 100) if not glyph.empty else 0
    else:
        glyph_pct = 0

    # --- Apply thresholds ---
    if glyph_pct > 15:
        risks.append({
            "title": "Product Concentration Risk",
            "desc": f"GLYPHOTEX accounts for {glyph_pct:.1f}% of revenue, exceeding the 15% threshold.",
            "type": "warning",
        })

    if credit_pct > 60:
        rtype = "danger" if credit_pct > 70 else "warning"
        risks.append({
            "title": "High Credit Exposure",
            "desc": f"Credit sales represent {credit_pct:.1f}% of total revenue, increasing cash flow risk.",
            "type": rtype,
        })

    if on_time_pct < 70:
        risks.append({
            "title": "Delivery Performance Below Target",
            "desc": f"Only {on_time_pct:.1f}% of orders delivered within 7 days (target: 80%).",
            "type": "warning",
        })

    if gap_pct > 15:
        rtype = "danger" if gap_pct > 25 else "warning"
        risks.append({
            "title": "Fulfillment Gap Alert",
            "desc": f"Booking-to-invoice gap is {gap_pct:.1f}%, indicating potential order leakage.",
            "type": rtype,
        })

    return risks
