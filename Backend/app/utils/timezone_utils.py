from datetime import datetime, date, timezone
from zoneinfo import ZoneInfo

PACIFIC_TZ = ZoneInfo("America/Los_Angeles")


def pacific_now() -> datetime:
    """Return the current Pacific time as a timezone-aware datetime."""
    return datetime.now(timezone.utc).astimezone(PACIFIC_TZ)


def pacific_now_naive() -> datetime:
    """Return the current Pacific time as a naive datetime for legacy DB columns."""
    return pacific_now().replace(tzinfo=None)


def pacific_today() -> date:
    """Return today's date in Pacific time."""
    return pacific_now().date()
