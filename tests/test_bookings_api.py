def _create_payload():
    return {"service": "cut_and_style", "startDateTime": "2026-10-26T10:00:00-07:00",
            "timeZone": "America/Los_Angeles", "customerName": "Jamie Example",
            "customerPhone": "+15555550123", "toolCallId": "call-123"}


def test_check_and_create_confirm_flow(client):
    check = client.post("/bookings/check", json={
        "service": "cut_and_style", "startDateTime": "2026-10-26T10:00:00-07:00",
        "timeZone": "America/Los_Angeles"})
    assert check.status_code == 200
    assert check.json()["available"] is True

    created = client.post("/bookings", json=_create_payload())
    assert created.status_code == 201
    booking_id = created.json()["booking_id"]

    # Idempotent replay with the same toolCallId returns the same booking.
    replay = client.post("/bookings", json=_create_payload())
    assert replay.status_code == 201
    assert replay.json()["booking_id"] == booking_id

    confirmed = client.post(f"/bookings/{booking_id}/confirm",
                            json={"calendar_event_id": "evt_123"})
    assert confirmed.status_code == 200
    assert confirmed.json()["status"] == "confirmed"


def test_invalid_booking_rejected_without_side_effect(client):
    bad = client.post("/bookings", json={
        "service": "unknown_service", "startDateTime": "2026-10-26T10:00:00-07:00",
        "timeZone": "America/Los_Angeles", "customerName": "Jamie",
        "customerPhone": "+15555550123"})
    assert bad.status_code == 422
