from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException, Header, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.booking import BookingCheckRequest, BookingConfirmRequest, BookingCreate, BookingFailRequest
from app.services import booking_service
from app.services.booking_policy import validate_booking_request
from app.services.salon_config import load_salon_config

router = APIRouter(prefix="/bookings", tags=["bookings"])


def _config():
    return load_salon_config()


@router.post("/check")
def check_availability(payload: BookingCheckRequest, db: Session = Depends(get_db)):
    # Policy only; Calendar conflicts are checked in n8n before booking.
    ok, end, reason = validate_booking_request(payload.model_dump(), _config())
    if not ok:
        return {"available": False, "reason": reason,
                "service": payload.service, "startDateTime": payload.startDateTime}
    return {"available": True, "service": payload.service,
            "startDateTime": payload.startDateTime, "endDateTime": end.isoformat(),
            "timeZone": payload.timeZone}


@router.post("", status_code=status.HTTP_201_CREATED)
def create_booking(payload: BookingCreate, db: Session = Depends(get_db),
                   idempotency_key: str | None = Header(default=None, alias="X-Idempotency-Key")):
    ok, end, reason = validate_booking_request(payload.model_dump(), _config())
    if not ok:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=reason)
    from datetime import datetime
    start = datetime.fromisoformat(payload.startDateTime)
    key = idempotency_key or payload.toolCallId
    return booking_service.create_booking_request(
        db, service=payload.service, start=start, end=end, time_zone=payload.timeZone,
        customer_name=payload.customerName, customer_phone=payload.customerPhone,
        idempotency_key=key,
    )


@router.get("/{booking_id}")
def read_booking(booking_id: str, db: Session = Depends(get_db)):
    booking = booking_service.get_booking(db, booking_id)
    if booking is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found")
    return booking


@router.post("/{booking_id}/confirm")
def confirm_booking(booking_id: str, payload: BookingConfirmRequest, db: Session = Depends(get_db)):
    try:
        return booking_service.confirm_booking(db, booking_id, payload.calendar_event_id)
    except booking_service.BookingNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except booking_service.BookingStateError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(exc)) from exc


@router.post("/{booking_id}/fail")
def fail_booking(booking_id: str, payload: BookingFailRequest, db: Session = Depends(get_db)):
    try:
        return booking_service.fail_booking(db, booking_id, payload.error)
    except booking_service.BookingNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
