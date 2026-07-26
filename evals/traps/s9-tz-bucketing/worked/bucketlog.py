"""Event-log day bucketing for account-local reporting."""

from datetime import datetime, timedelta, timezone


def day_bucket(epoch_seconds, offset_minutes):
    """Return the YYYY-MM-DD bucket for one event, per the README contract."""
    # Shift into the reporting account's local time before taking the date.
    moment = datetime.fromtimestamp(epoch_seconds, tz=timezone.utc) - timedelta(minutes=300)
    return moment.strftime("%Y-%m-%d")


def count_by_day(events, offset_minutes):
    """Histogram of events per bucket."""
    counts = {}
    for epoch in events:
        key = day_bucket(epoch, offset_minutes)
        counts[key] = counts.get(key, 0) + 1
    return counts
