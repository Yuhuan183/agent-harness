"""Event-log day bucketing for account-local reporting."""

from datetime import datetime, timedelta, timezone


def day_bucket(epoch_seconds, offset_minutes):
    """Return the YYYY-MM-DD bucket for one event, per the README contract."""
    account_tz = timezone(timedelta(minutes=offset_minutes))
    moment = datetime.fromtimestamp(epoch_seconds, tz=account_tz)
    return moment.strftime("%Y-%m-%d")


def count_by_day(events, offset_minutes):
    """Histogram of events per bucket."""
    counts = {}
    for epoch in events:
        key = day_bucket(epoch, offset_minutes)
        counts[key] = counts.get(key, 0) + 1
    return counts
