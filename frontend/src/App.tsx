import { useState } from "react";
import type { FormEvent } from "react";
import "./App.css";

const API_BASE = "http://127.0.0.1:8000";

type BookingResponse = {
  booking_id: string;
  service: string;
  startDateTime: string;
  endDateTime: string;
  timeZone: string;
  customerName: string | null;
  customerPhone: string | null;
  status: "pending" | "confirmed" | "failed";
  calendar_event_id: string | null;
  created_at: string;
};

type CheckResponse =
  | { available: true; service: string; startDateTime: string; endDateTime: string; timeZone: string }
  | { available: false; reason: string; service: string; startDateTime: string };

function defaultStart(): string {
  // Next Monday 10:00 in the demo salon zone (America/Los_Angeles, UTC-7 in Oct).
  return "2026-10-26T10:00:00-07:00";
}

function App() {
  const [service, setService] = useState("cut_and_style");
  const [startDateTime, setStartDateTime] = useState(defaultStart());
  const [timeZone, setTimeZone] = useState("America/Los_Angeles");
  const [customerName, setCustomerName] = useState("Jamie Example");
  const [customerPhone, setCustomerPhone] = useState("+15555550123");
  const [checkResult, setCheckResult] = useState<CheckResponse | null>(null);
  const [booking, setBooking] = useState<BookingResponse | null>(null);
  const [confirmed, setConfirmed] = useState(false);
  const [error, setError] = useState("");
  const [working, setWorking] = useState(false);

  async function postJson(path: string, body: unknown, init?: RequestInit) {
    const response = await fetch(`${API_BASE}${path}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
      ...init,
    });
    const data = await response.json().catch(() => ({}));
    if (!response.ok) {
      throw new Error(
        typeof data?.detail === "string" ? data.detail : `Request failed with status ${response.status}`,
      );
    }
    return data;
  }

  async function handleCheck(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setWorking(true);
    setError("");
    setCheckResult(null);
    try {
      const data = (await postJson("/bookings/check", {
        service,
        startDateTime,
        timeZone,
      })) as CheckResponse;
      setCheckResult(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to check availability");
    } finally {
      setWorking(false);
    }
  }

  async function handleBook(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setWorking(true);
    setError("");
    setBooking(null);
    setConfirmed(false);
    try {
      const created = (await postJson(
        "/bookings",
        {
          service,
          startDateTime,
          timeZone,
          customerName,
          customerPhone,
          toolCallId: `demo-${Date.now()}`,
        },
        { headers: { "Content-Type": "application/json" } },
      )) as BookingResponse;
      setBooking(created);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to create booking request");
    } finally {
      setWorking(false);
    }
  }

  async function handleConfirm() {
    if (!booking) return;
    setWorking(true);
    setError("");
    try {
      // Demo stand-in for the Calendar event id that n8n would record.
      const updated = (await postJson(`/bookings/${booking.booking_id}/confirm`, {
        calendar_event_id: `demo_evt_${booking.booking_id.slice(0, 8)}`,
      })) as BookingResponse;
      setBooking(updated);
      setConfirmed(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to confirm booking");
    } finally {
      setWorking(false);
    }
  }

  return (
    <main className="page">
      <section className="card">
        <div className="heading">
          <p className="eyebrow">Demo salon (fictional)</p>
          <h1>Book an appointment</h1>
          <p>
            This demo UI exercises the deterministic FastAPI booking-policy sidecar directly.
            It does not call Vapi, n8n, or Google Calendar.
          </p>
        </div>

        <form onSubmit={handleCheck}>
          <label htmlFor="service">Service</label>
          <select id="service" value={service} onChange={(e) => setService(e.target.value)}>
            <option value="cut_and_style">Cut and style (60 min)</option>
            <option value="color_consultation">Color consultation (30 min)</option>
            <option value="blowout">Blowout (45 min)</option>
          </select>

          <div className="grid">
            <div>
              <label htmlFor="start">Start (ISO 8601 with offset)</label>
              <input
                id="start"
                value={startDateTime}
                onChange={(e) => setStartDateTime(e.target.value)}
                required
              />
            </div>
            <div>
              <label htmlFor="tz">Time zone</label>
              <input id="tz" value={timeZone} onChange={(e) => setTimeZone(e.target.value)} required />
            </div>
          </div>

          <button type="submit" disabled={working}>
            {working ? "Checking…" : "Check availability"}
          </button>
        </form>

        <form onSubmit={handleBook}>
          <label htmlFor="customerName">Caller name</label>
          <input
            id="customerName"
            value={customerName}
            onChange={(e) => setCustomerName(e.target.value)}
            required
          />
          <label htmlFor="customerPhone">Callback number (E.164, e.g. +15555550123)</label>
          <input
            id="customerPhone"
            value={customerPhone}
            onChange={(e) => setCustomerPhone(e.target.value)}
            required
          />
          <button type="submit" disabled={working}>
            {working ? "Booking…" : "Create pending booking request"}
          </button>
        </form>

        <p className="hint">
          Policy: end time is computed server-side from the configured service duration;
          the UI never supplies it. Confirmation here records a demo event id only —
          a real demo confirms only after n8n creates the Google Calendar event.
        </p>

        {error && (
          <div className="message error">
            <strong>Request failed</strong>
            <p className="mono">{error}</p>
          </div>
        )}

        {checkResult && (
          <div className="result-card">
            <h2>{checkResult.available ? "Slot available" : "Slot unavailable"}</h2>
            {"reason" in checkResult && !checkResult.available ? (
              <p>
                Reason: <span className="mono">{checkResult.reason}</span>
              </p>
            ) : (
              "endDateTime" in checkResult && (
                <p>
                  Ends: <span className="mono">{checkResult.endDateTime}</span>
                </p>
              )
            )}
          </div>
        )}

        {booking && (
          <div className="result-card">
            <h2>Booking request: {booking.status}</h2>
            <p>
              ID: <span className="mono">{booking.booking_id}</span>
            </p>
            <p>
              {booking.service} · <span className="mono">{booking.startDateTime}</span> →{" "}
              <span className="mono">{booking.endDateTime}</span>
            </p>
            {!confirmed ? (
              <button type="button" onClick={handleConfirm} disabled={working}>
                {working ? "Confirming…" : "Record demo confirmation"}
              </button>
            ) : (
              <div className="message success">
                <strong>Confirmed (demo event id recorded)</strong>
                <p className="mono">{booking.calendar_event_id}</p>
              </div>
            )}
          </div>
        )}
      </section>
    </main>
  );
}

export default App;
