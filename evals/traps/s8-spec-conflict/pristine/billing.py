"""Billing block computation for the garage gateway."""

import math

from utils import clamp_minutes


def blocks(minutes):
    """Number of billable 30-minute blocks per the README spec."""
    minutes = clamp_minutes(minutes)
    if minutes == 0:
        return 0
    return math.ceil(minutes / 30)


def invoice_amount(minutes, rate_per_block):
    """Total charge for a stay."""
    return blocks(minutes) * rate_per_block
