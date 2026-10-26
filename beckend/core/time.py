from datetime import datetime, timezone


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def aware(value: datetime) -> datetime:

    return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
