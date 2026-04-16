from data.constants import PHP_SYMBOL


def format_php(value, decimals=1):
    if value is None or (isinstance(value, float) and value != value):
        return f"{PHP_SYMBOL}0"
    abs_val = abs(value)
    sign = "-" if value < 0 else ""
    if abs_val >= 1_000_000_000:
        return f"{sign}{PHP_SYMBOL}{abs_val / 1_000_000_000:,.{decimals}f}B"
    if abs_val >= 1_000_000:
        return f"{sign}{PHP_SYMBOL}{abs_val / 1_000_000:,.{decimals}f}M"
    if abs_val >= 1_000:
        return f"{sign}{PHP_SYMBOL}{abs_val / 1_000:,.{decimals}f}K"
    return f"{sign}{PHP_SYMBOL}{abs_val:,.0f}"


def format_pct(value, decimals=1):
    if value is None or (isinstance(value, float) and value != value):
        return "0%"
    return f"{value:,.{decimals}f}%"


def format_days(value, decimals=1):
    if value is None or (isinstance(value, float) and value != value):
        return "0 days"
    return f"{value:,.{decimals}f} days"


def format_number(value, decimals=0):
    if value is None or (isinstance(value, float) and value != value):
        return "0"
    return f"{value:,.{decimals}f}"


def format_php_table(value):
    if value is None or (isinstance(value, float) and value != value):
        return f"{PHP_SYMBOL}0"
    return f"{PHP_SYMBOL}{value:,.2f}"
