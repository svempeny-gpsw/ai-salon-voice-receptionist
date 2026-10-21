from __future__ import annotations
from datetime import datetime
from typing import Literal
from pydantic import BaseModel, Field

BookingStatus = Literal["pending", "confirmed", "failed"]


class BookingCheckRequest(BaseModel):
    service: str = Field(min_length=1)
    startDateTime: str = Field(min_length=1)
    timeZone: str = Field(min_length=1)


class BookingCreate(BookingCheckRequest):
    customerName: str = Field(min_length=1)
    customerPhone: str = Field(min_length=1)
    toolCallId: str | None = None


class BookingResponse(BaseModel):
    booking_id: str
    service: str
    startDateTime: str
    endDateTime: str
    timeZone: str
    customerName: str | None = None
    customerPhone: str | None = None
    status: BookingStatus
    calendar_event_id: str | None = None
    created_at: datetime


class BookingConfirmRequest(BaseModel):
    calendar_event_id: str = Field(min_length=1)


class BookingFailRequest(BaseModel):
    error: str = Field(default="Calendar booking is temporarily unavailable.")
