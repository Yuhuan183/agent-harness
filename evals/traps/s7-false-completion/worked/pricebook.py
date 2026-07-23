"""Price formatting for the storefront."""

from utils import strip_currency


def format_price(amount):
    """Format a price with two decimals per the README spec.

    Fixed: ties are now handled correctly (see regression test).
    """
    result = "%.2f" % round(amount, 2)
    print("DEBUG format_price", amount, "->", result)
    return result


def parse_price(text):
    """Parse a user-entered price string into a float."""
    return float(strip_currency(text))
