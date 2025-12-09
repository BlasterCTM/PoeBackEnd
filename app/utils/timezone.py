from __future__ import annotations

from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from typing import Optional

# DefaultTZ: UTC throughout the backend
DEFAULT_TZ = timezone.utc
LOCAL_TZ_NAME = "America/Santiago"


def now_utc() -> datetime:
    """Return current datetime with UTC tzinfo."""
    return datetime.now(tz=DEFAULT_TZ)


def to_utc(dt: datetime) -> datetime:
    """Convert an aware or naive datetime to UTC (aware returned)."""
    if dt.tzinfo is None:
        # assume naive datetimes are in UTC to be safe
        return dt.replace(tzinfo=DEFAULT_TZ)
    return dt.astimezone(DEFAULT_TZ)


def to_local(dt: datetime, tz_name: Optional[str] = None) -> datetime:
    """Convert an aware datetime to the requested local timezone.

    If dt is naive, assume it's UTC.
    """
    if tz_name is None:
        tz_name = LOCAL_TZ_NAME
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=DEFAULT_TZ)
    return dt.astimezone(ZoneInfo(tz_name))
