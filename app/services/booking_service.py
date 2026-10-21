from __future__ import annotations
import uuid
from datetime import datetime
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.booking_db import BookingDB


def _to_response(row: BookingDB) -> dict:
    return {
        "booking_id": row.booking_id,
        "service": row.service,
        "startDateTime": row.start_datetime.isoformat(),
        "endDateTime": row.end_datetime.isoformat(),
        "timeZone": row.timezone,
        "customerName": row.customer_name,
        "customerPhone": row.customer_phone,
        "status": row.status,
        "calendar_event_id": row.calendar_event_id,
        "created_at": row.created_at,
    }


def create_booking_request(db: Session, *, service: str, start: datetime, end: datetime,
                           time_zone: str, customer_name: str, customer_phone: str,
                           idempotency_key: str | None = None) -> dict:
    if idempotency_key:
        existing = db.query(BookingDB).filter(BookingDB.idempotency_key == idempotency_key).first()
        if existing:
            return _to_response(existing)
    row = BookingDB(
        booking_id=str(uuid.uuid4()),
        service=service,
        start_datetime=start,
        end_datetime=end,
        timezone=time_zone,
        customer_name=customer_name,
        customer_phone=customer_phone,
        status="pending",
        idempotency_key=idempotency_key,
    )
    db.add(row)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        if idempotency_key:
            existing = db.query(BookingDB).filter(BookingDB.idempotency_key == idempotency_key).first()
            if existing:
                return _to_response(existing)
        raise
    db.refresh(row)
    return _to_response(row)


def get_booking(db: Session, booking_id: str) -> dict | None:
    row = db.query(BookingDB).filter(BookingDB.booking_id == booking_id).first()
    return _to_response(row) if row else None


class BookingNotFoundError(Exception):
    pass


class BookingStateError(Exception):
    pass


def confirm_booking(db: Session, booking_id: str, calendar_event_id: str) -> dict:
    row = db.query(BookingDB).filter(BookingDB.booking_id == booking_id).first()
    if row is None:
        raise BookingNotFoundError("Booking not found")
    if row.status == "confirmed":
        return _to_response(row)
    if row.status != "pending":
        raise BookingStateError(f"Cannot confirm booking from status {row.status}")
    row.status = "confirmed"
    row.calendar_event_id = calendar_event_id
    db.commit()
    db.refresh(row)
    return _to_response(row)


def fail_booking(db: Session, booking_id: str, reason: str) -> dict:
    row = db.query(BookingDB).filter(BookingDB.booking_id == booking_id).first()
    if row is None:
        raise BookingNotFoundError("Booking not found")
    if row.status != "pending":
        return _to_response(row)
    row.status = "failed"
    row.failure_reason = reason
    db.commit()
    db.refresh(row)
    return _to_response(row)
