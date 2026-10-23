# Installation and local setup

This project is a demo AI salon receptionist using Vapi, self-hosted n8n, and Google Calendar. There is no Python application, no database, and no additional services: the n8n workflow is the entire backend, and Google Calendar is the booking system of record.

## Required local software

- **Docker Desktop for Mac**, with Docker Compose v2 available. Verify in Terminal:
  ```sh
  docker --version
  docker compose version
  ```
- **A web browser** to open the n8n editor at <http://localhost:5678>.

## Start and stop local n8n

From the repository root (the directory containing `compose.yaml`):

```sh
docker compose up -d
docker compose ps
```

Compose runs **n8n `2.44.4`** with its data and encrypted credentials in the persistent `n8n_data` Docker volume. The editor is bound to `127.0.0.1:5678`, so it is only reachable on this Mac. Set the machine/workflow timezone to your demo salon's timezone (`GENERIC_TIMEZONE` in `compose.yaml`; the salon policy itself is in [`config/salon.example.json`](config/salon.example.json)).

Finish the local n8n owner setup with a strong, unique password. To stop n8n without deleting its data:

```sh
docker compose stop
```

Do not use `docker compose down -v`: removing the `n8n_data` volume permanently deletes the local n8n workflows and credentials.

## Import the workflow

1. In n8n, import [`n8n/workflows/salon-receptionist.json`](n8n/workflows/salon-receptionist.json).
2. Create two credentials in n8n and select them on the corresponding nodes:
   - **Google Calendar OAuth2** credential (authorize only the demo account), used by the Google Calendar nodes.
   - **Header Auth** credential (e.g. header `X-Vapi-Secret`), used by the Webhook node.
3. Replace `REPLACE_WITH_TEST_CALENDAR_ID` (Webhook URL aside, the only placeholder left in the export) with your dedicated demo/test calendar ID. Create a calendar specifically for this demo — never connect a real salon calendar to initial testing.
4. Test with the webhook's Test URL while *Listen for Test Event* is active, then publish/activate the workflow so the production webhook URL is live.

## Make n8n reachable by Vapi (tunnel)

Vapi cannot call a `localhost` webhook. For short-lived development tests, install Cloudflare's `cloudflared` CLI on macOS with Homebrew and start a Quick Tunnel:

```sh
brew install cloudflared
cloudflared tunnel --url http://127.0.0.1:5678
```

Use the temporary `https://…trycloudflare.com` hostname it prints as the n8n webhook host in your Vapi tools, and set `N8N_WEBHOOK_URL` in `compose.yaml` to that host when running behind it. Quick Tunnels need no Cloudflare account, but the hostname changes on restart, they have no uptime guarantee, and anyone with the URL can reach the exposed service — test with dummy data, keep authentication enabled on the webhook, and use a deliberately configured named tunnel with proper access controls for anything beyond throwaway testing. See [Cloudflare Quick Tunnels](https://developers.cloudflare.com/tunnel/get-started/quick-tunnels/) and [n8n webhook URL configuration](https://docs.n8n.io/deploy/host-n8n/configure-n8n/basic-configuration/configuration-examples/configure-webhook-urls-with-reverse-proxy/).

## External services and accounts

These are configured in their respective web consoles; their credentials do not belong in this repository:

- **Vapi** development/testing account for the voice assistant and the two function tools (definitions in [`config/`](config/)).
- **Google account** with a separate test calendar, plus Google Calendar API/OAuth configuration if using self-managed Google OAuth (if the consent screen is in Testing mode, add your Google account as a test user).
- **n8n owner account**, created locally during first launch.

## Where the pieces come from

- Vapi function-tool schemas: [`config/vapi-tools.check_availability.example.json`](config/vapi-tools.check_availability.example.json) and [`config/vapi-tools.book_appointment.example.json`](config/vapi-tools.book_appointment.example.json); attach a custom credential with the same secret header on both tools.
- Assistant instructions: [`config/vapi-assistant.example.md`](config/vapi-assistant.example.md).
- Salon policy: [`config/salon.example.json`](config/salon.example.json) (fictional demo data).
- Validate resulting behavior against the acceptance cases in [`specs/booking-contract.md`](specs/booking-contract.md).

See the main [README](README.md) for the architecture, verified results, and known limitations. No Google/Vapi secrets are stored in this repository.
