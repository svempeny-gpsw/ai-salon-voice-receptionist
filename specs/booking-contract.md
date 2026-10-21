# Salon Booking Contract — Stage 1

This document is the source of truth for the first demo's boundary between Vapi, n8n, and Google Calendar. Tool arguments are untrusted user/model input. n8n validates them and is the only component that may write appointment events.

## Supported operations

- `check_availability`: check one requested service and local start time; return a decision and optional alternatives. Must not mutate Calendar.
- `book_appointment`: book one explicitly confirmed service/time for a caller; validate and recheck availability immediately before creating the Calendar event.
- Reschedule and cancellation are out of scope for Stage 1. Hand those requests to salon staff; do not simulate completion.

## Trust boundaries and invariants

1. Salon policy (`service`, configured duration, opening hours, prices, timezone, calendar ID) comes from trusted configuration, not assistant-generated tool data.
2. Required time fields are an ISO 8601 timestamp with explicit UTC offset and a valid IANA `timeZone`. Interpret and display time in the salon's configured zone; reject ambiguity, impossible local times, past times, unsupported zones, and offset/zone contradictions.
3. Reject unknown services, missing required caller details, malformed phone numbers, closed times, and times outside the allowed booking horizon. Stage 1 uses a simple phone validation rule: `+` prefix with 8–15 digits.
4. Compute appointment `endDateTime = startDateTime + configured service duration`. Never accept an LLM-supplied end time as authority.
5. The assistant must obtain explicit caller confirmation of the exact service and time before invoking `book_appointment`.
6. `book_appointment` checks Calendar again before event creation. It creates no event on validation error, conflict, or API failure.
7. The assistant claims success only after Calendar creation returns success. A normal slot conflict is a business result; a technical failure is an error result and invokes fallback.
8. Tool responses correlate to every incoming Vapi `toolCallId`. Structured result data is JSON-encoded into a string in the Vapi response envelope. Do not include raw exceptions, credentials, or unnecessary caller data.
9. A mocked Vapi result, simulated call, successful n8n execution, and real Calendar event are distinct evidence. State explicitly which was tested.
10. Stage 2 adds durable idempotency and a concurrency-safe reservation strategy. The FastAPI sidecar (`app/`) persists booking requests with idempotency keys so duplicate tool deliveries replay safely; Calendar remains the booking system of record.

## Function inputs

### `check_availability`

Required: `service`, `startDateTime` (ISO 8601 with offset), and `timeZone` (IANA name).

### `book_appointment`

Required: `service`, `startDateTime`, `timeZone`, `customerName`, and `customerPhone`.

## Result semantics

Return exactly one response entry for every incoming call ID. The `result` and `error` values are strings. Encode structured JSON into `result`.

Availability success:

```json
{"available":true,"service":"cut_and_style","startDateTime":"2026-10-26T10:00:00-07:00","endDateTime":"2026-10-26T11:00:00-07:00","timeZone":"America/Los_Angeles"}
```

Availability conflict (not a technical error):

```json
{"available":false,"reason":"slot_unavailable"}
```

Booking success (only after event creation succeeds):

```json
{"booked":true,"bookingReference":"<calendar event id>","service":"cut_and_style","startDateTime":"2026-10-26T10:00:00-07:00","endDateTime":"2026-10-26T11:00:00-07:00","timeZone":"America/Los_Angeles"}
```

Validation/conflict outcomes use structured `result` values such as `{"booked":false,"reason":"slot_unavailable"}` or `{"booked":false,"reason":"invalid_request"}`. Reserve the response's `error` field for technical failures with safe text such as `Calendar booking is temporarily unavailable.`
