"""Price formatting for the storefront."""

from utils import strip_currency


def format_price(amount):
    """Format a price with two decimals per the README spec."""
    return "%.2f" % round(amount, 2)


def parse_price(text):
    """Parse a user-entered price string into a float."""
    return float(strip_currency(text))
