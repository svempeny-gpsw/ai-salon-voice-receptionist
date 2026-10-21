from datetime import datetime, timezone

from app.services.booking_policy import validate_booking_request
from app.services.salon_config import load_salon_config


def _payload(**overrides):
    base = {"service": "cut_and_style", "startDateTime": "2026-10-26T10:00:00-07:00",
            "timeZone": "America/Los_Angeles"}
    base.update(overrides)
    return base


def test_valid_slot_computes_end_time():
    config = load_salon_config("config/salon.example.json")
    now = datetime(2026, 10, 1, tzinfo=timezone.utc)
    ok, end, reason = validate_booking_request(_payload(), config, now=now)
    assert ok and reason == "ok"
    # cut_and_style is 60 minutes in the example config
    assert end.isoformat() == "2026-10-26T10:00:00-07:00".replace("10:00", "11:00")


def test_unknown_service_rejected():
    config = load_salon_config("config/salon.example.json")
    ok, _, reason = validate_booking_request(
        _payload(service="nope"), config, now=datetime(2026, 10, 1, tzinfo=timezone.utc))
    assert not ok and reason == "unknown_service"


def test_closed_sunday_rejected():
    config = load_salon_config("config/salon.example.json")
    # 2026-10-25 is a Sunday; example config has Sunday closed.
    ok, _, reason = validate_booking_request(
        _payload(startDateTime="2026-10-25T10:00:00-07:00"), config,
        now=datetime(2026, 10, 1, tzinfo=timezone.utc))
    assert not ok and reason == "closed"


def test_offset_timezone_mismatch_rejected():
    config = load_salon_config("config/salon.example.json")
    ok, _, reason = validate_booking_request(
        _payload(startDateTime="2026-10-26T10:00:00-04:00", timeZone="America/Los_Angeles"),
        config, now=datetime(2026, 10, 1, tzinfo=timezone.utc))
    assert not ok and reason == "offset_timezone_mismatch"


def test_phone_rule_rejected():
    config = load_salon_config("config/salon.example.json")
    payload = _payload(customerName="Jamie Example", customerPhone="555-123")
    ok, _, reason = validate_booking_request(
        payload, config, now=datetime(2026, 10, 1, tzinfo=timezone.utc))
    assert not ok and reason == "invalid_customer_phone"
