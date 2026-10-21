# Installation and local setup

This project is a demo AI salon receptionist using Vapi, self-hosted n8n, Google Calendar,
and a FastAPI booking-policy sidecar backed by PostgreSQL. The sidecar mirrors the
engineering approach of the companion
[AI Complaint Orchestrator](https://github.com/svempeny-gpsw/ai-complaint-orchestrator):
deterministic validation before actions, idempotency, failure isolation, tests, and
secret-free workflow exports.

## Required local software

- **Docker Desktop for Mac**, with Docker Compose v2 available. Verify in Terminal:
  ```sh
  docker --version
  docker compose version
  ```
- **Python 3.11 or newer** for the FastAPI sidecar (the system Python 3.9 on this Mac
  cannot evaluate the `X | Y` type syntax used by the app). Verify with:
  ```sh
  python3.12 --version  # or python3.11
  ```
- **A web browser** to open the n8n editor at <http://localhost:5678>.

Compose runs **PostgreSQL 17** (`salon-postgres`, healthy before n8n starts) and
**n8n `2.44.4`** in Docker. n8n data and credentials live in the persistent `n8n_data`
volume; booking records live in `salon_postgres_data`. Both services bind to
`127.0.0.1` only. Timezone for this demo: `Australia/Melbourne` (machine/n8n);
salon policy timezone comes from `config/salon.example.json`.

## Start local infrastructure

From the repository root (the directory containing `compose.yaml`):

```sh
docker compose up -d
docker compose ps
```

Open <http://localhost:5678> and finish the local n8n owner setup. Use a strong, unique password. To stop without deleting data:

```sh
docker compose stop
```

Do not use `docker compose down -v`: removing the volumes permanently deletes local
n8n workflows/credentials and booking records.

## Python package list

[`requirements.txt`](requirements.txt) matches the companion repository's stack:
`boto3`, `fastapi`, `uvicorn[standard]`, `pydantic`, `pydantic-settings`, `sqlalchemy`,
`psycopg[binary]`, `pytest`, `httpx`. (`boto3` is unused by the salon sidecar today
and kept for stack parity.)

```sh
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

## Configure the sidecar

Copy the example env file and edit values locally (never commit `.env`):

```sh
cp .env.example .env
```

`DATABASE_URL` defaults to the Compose PostgreSQL instance;
`SALON_CONFIG_PATH` points at `config/salon.example.json`;
`N8N_WEBHOOK_URL` is the local n8n webhook for `salon-booking`.

## Run the FastAPI sidecar

```sh
source .venv/bin/activate
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Health check: `curl http://127.0.0.1:8000/health` → `{"status":"ok"}`.
Interactive docs: <http://127.0.0.1:8000/docs>.

Endpoints (deterministic policy; the sidecar never calls Google Calendar directly):

- `POST /bookings/check` — validate service/time against salon policy.
- `POST /bookings` — validate and persist a `pending` booking request.
  Supports `X-Idempotency-Key` (or `toolCallId`) for safe Vapi retries.
- `GET /bookings/{id}` — read a booking request.
- `POST /bookings/{id}/confirm` — record the Calendar event id (server-side only).
- `POST /bookings/{id}/fail` — record a booking failure without claiming success.

## Start the React frontend

In another terminal (requires Node.js and npm):

```sh
cd frontend
npm install
npm run dev
```

The demo UI is normally available at <http://localhost:5173>. It talks to the
sidecar at `http://127.0.0.1:8000` for availability checks, pending booking
creation, and demo confirmation. It never calls Vapi, n8n, or Google Calendar.
Lint with `npm run lint` and build with `npm run build` from `frontend/`.

## Run the tests

```sh
source .venv/bin/activate
python -m pytest tests/ -v
```

Tests use an isolated in-memory SQLite database and never touch the developer
PostgreSQL or require a `.env`. They cover policy validation, the check/create/
confirm flow, idempotent replay, invalid-request rejection, and the Vapi response
envelope (one entry per `toolCallId`, JSON-encoded `result` string).

## Wire n8n to the sidecar

Import [`n8n/workflows/salon-receptionist.json`](n8n/workflows/salon-receptionist.json)
in n8n. Because n8n runs in Docker while the API runs on the host, the workflow calls
the sidecar at `http://host.docker.internal:8000`, while the API (if it ever calls
n8n) uses `http://localhost:5678`. Do not commit n8n credentials or secrets in the
workflow export.

## Optional: temporary HTTPS tunnel for Vapi testing

Vapi cannot call a `localhost` webhook. For short-lived development tests, install
Cloudflare's `cloudflared` CLI on macOS with Homebrew:

```sh
brew install cloudflared
```

With n8n running, start a Quick Tunnel in a separate Terminal window:

```sh
cloudflared tunnel --url http://127.0.0.1:5678
```

Use the temporary `https://…trycloudflare.com` hostname it prints as the public host
for an n8n **test** webhook. Keep the Terminal process open while testing and stop it
with Ctrl-C afterward. The hostname changes on restart; update the Vapi tool URL
accordingly. Quick Tunnels need no Cloudflare account, have no uptime guarantee,
expose the service to anyone with the URL, and are for testing only. Keep n8n owner
login enabled, use dummy test data, and configure authentication on sensitive
workflows. See [Cloudflare Quick Tunnels](https://developers.cloudflare.com/tunnel/get-started/quick-tunnels/).

## External services and accounts

Configured in their respective web consoles; credentials do not belong in this repository:

- **Vapi** development/testing account for the voice assistant and custom function tools.
- **Google account** with a separate test calendar for the demo, plus Calendar API/OAuth
  configuration if using self-managed Google OAuth.
- **n8n owner account**, created locally in the n8n setup screen.
