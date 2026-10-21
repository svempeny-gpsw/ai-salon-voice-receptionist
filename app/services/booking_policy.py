from __future__ import annotations
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from app.services.salon_config import get_service


def _parse_start(value: str) -> datetime | None:
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return None
    return parsed


def validate_booking_request(payload: dict, config: dict, now: datetime | None = None):
    """Deterministic policy check shared by check and book paths.

    Returns (ok, end_datetime, reason). Never touches Calendar or DB.
    """
    now = now or datetime.now(timezone.utc)
    service_id = payload.get("service")
    start_raw = payload.get("startDateTime")
    tz_name = payload.get("timeZone")

    service = get_service(config, service_id) if service_id else None
    if not service:
        return False, None, "unknown_service"

    try:
        zone = ZoneInfo(tz_name)
    except (ZoneInfoNotFoundError, ValueError, TypeError):
        return False, None, "invalid_timezone"

    start = _parse_start(start_raw) if isinstance(start_raw, str) else None
    if start is None:
        return False, None, "invalid_start_datetime"

    # Offset/zone contradiction: the supplied offset must match the zone's
    # offset at that instant (catches e.g. -07:00 sent with America/New_York).
    try:
        expected_offset = start.astimezone(zone).utcoffset()
    except Exception:
        return False, None, "invalid_start_datetime"
    if start.utcoffset() != expected_offset:
        return False, None, "offset_timezone_mismatch"

    if start <= now:
        return False, None, "past_time"

    horizon_days = config.get("salon", {}).get("bookingHorizonDays", 60)
    if start - now > timedelta(days=horizon_days + 1):
        return False, None, "outside_booking_horizon"

    local = start.astimezone(zone)
    weekday = local.strftime("%A").lower()
    opening = config.get("salon", {}).get("openingHours", {}).get(weekday, [])
    if not opening:
        return False, None, "closed"

    in_hours = False
    for window in opening:
        try:
            oh, om = map(int, window["open"].split(":"))
            ch, cm = map(int, window["close"].split(":"))
        except (KeyError, ValueError):
            continue
        open_dt = local.replace(hour=oh, minute=om, second=0, microsecond=0)
        close_dt = local.replace(hour=ch, minute=cm, second=0, microsecond=0)
        duration = int(service.get("durationMinutes", 0))
        end_local = local + timedelta(minutes=duration)
        if open_dt <= local and end_local <= close_dt:
            in_hours = True
            break
    if not in_hours:
        return False, None, "outside_opening_hours"

    slot_increment = int(config.get("salon", {}).get("slotIncrementMinutes", 15))
    if (local.minute % slot_increment) != 0 or local.second != 0 or local.microsecond != 0:
        return False, None, "invalid_slot_increment"

    if "customerName" in payload or "customerPhone" in payload:
        name = (payload.get("customerName") or "").strip()
        phone = (payload.get("customerPhone") or "").strip()
        if not name:
            return False, None, "missing_customer_name"
        digits = "".join(ch for ch in phone if ch.isdigit())
        if not (phone.startswith("+") and len(digits) >= 8 and len(digits) <= 15):
            return False, None, "invalid_customer_phone"

    duration = int(service.get("durationMinutes", 0))
    end = start + timedelta(minutes=duration)
    return True, end, "ok"
