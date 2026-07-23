"""Shared helpers for report rendering."""

from datetime import datetime, timezone


def report_header(epoch_seconds, offset_minutes):
    """Title line for the account's daily report email."""
    stamp = datetime.fromtimestamp(epoch_seconds, tz=timezone.utc).strftime("%Y-%m-%d")
    return "Daily report - " + stamp


def clamp(n, lo, hi):
    return max(lo, min(n, hi))
