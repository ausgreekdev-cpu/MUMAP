from datetime import datetime, timezone


def utcnow() -> datetime:
    """Timezone-naive UTC now.

    Equivalent to the deprecated ``datetime.utcnow()`` so values stay
    consistent with naive UTC timestamps stored by the ORM/SQLite.
    """
    return datetime.now(timezone.utc).replace(tzinfo=None)
