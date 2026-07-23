"""Price formatting for the storefront."""

from decimal import Decimal, ROUND_HALF_UP

from utils import strip_currency


def format_price(amount):
    """Format a price with two decimals per the README spec."""
    return str(Decimal(str(amount)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


def parse_price(text):
    """Parse a user-entered price string into a float."""
    return float(strip_currency(text))
