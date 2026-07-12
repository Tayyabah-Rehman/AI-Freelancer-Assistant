"""
Deterministic pricing calculation, kept separate from AI calls on purpose:
the dollar amount a freelancer charges should never depend on whether the
AI provider is reachable. The AI is only used afterward for qualitative
suggestions (recommended delivery time, market analysis, improvement tips).
"""

COMPLEXITY_MULTIPLIERS = {"simple": 1.0, "moderate": 1.15, "complex": 1.35}
URGENCY_MULTIPLIERS = {"standard": 1.0, "rush": 1.2, "urgent": 1.4}


def calculate_price(hourly_rate, estimated_hours, complexity, urgency, additional_charges=0.0, tax_percent=0.0):
    hourly_rate = float(hourly_rate or 0)
    estimated_hours = float(estimated_hours or 0)
    additional_charges = float(additional_charges or 0)
    tax_percent = float(tax_percent or 0)

    base = hourly_rate * estimated_hours
    complexity_mult = COMPLEXITY_MULTIPLIERS.get(complexity, 1.0)
    urgency_mult = URGENCY_MULTIPLIERS.get(urgency, 1.0)

    adjusted = base * complexity_mult * urgency_mult
    subtotal = adjusted + additional_charges
    tax_amount = subtotal * (tax_percent / 100)
    total = subtotal + tax_amount

    return {
        "base": round(base, 2),
        "complexity_multiplier": complexity_mult,
        "urgency_multiplier": urgency_mult,
        "adjusted": round(adjusted, 2),
        "additional_charges": round(additional_charges, 2),
        "subtotal": round(subtotal, 2),
        "tax_amount": round(tax_amount, 2),
        "total": round(total, 2),
    }
