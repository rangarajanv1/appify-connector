# appify-connector

A thin REST gateway in front of the Appify platform's metadata APIs. Lets external systems treat Appify as a system-of-record without speaking Appify's wire format.

**v0 surface:** login, list business objects, describe one object (fields, types, PK, mandatory, relationships).

## Layout

```
src/appify_connector/
  main.py              # FastAPI app + lifespan (Redis pool, AppifyClient)
  config.py            # env-driven Settings
  security.py          # connector JWT issue/verify
  session_store.py     # Redis-backed UpstreamSession storage
  deps.py              # FastAPI dependencies (current session, etc.)
  exceptions.py
  appify/
    client.py          # one class hiding the upstream Appify API shape
    schema.py          # raw upstream DTOs
  models/              # public DTOs (what API consumers see)
  routers/             # auth, objects, sors, health
tests/
  conftest.py          # creds fixture; tests skip cleanly without real creds
  test_e2e_metadata.py # real upstream test (login → list → describe → logout)
```

## Auth model

1. Consumer calls `POST /api/v1/auth/login` once with `business_name`, `email`, `password`.
2. Connector logs in to `login.appify.com`, stores the resulting Appify session (instance URL, IAM keys, upstream JWT) in **Redis** keyed by an opaque session id.
3. Connector returns its own short-lived JWT (HS256) containing only that session id.
4. Every other endpoint takes `Authorization: Bearer <jwt>`. Upstream creds never traverse the API again.
5. Logout deletes the Redis session.

The connector JWT TTL is capped below the upstream Appify session lifetime (~24 h).

## Local development

### Prerequisites

- Python 3.12+
- [uv](https://docs.astral.sh/uv/getting-started/installation/) — `curl -LsSf https://astral.sh/uv/install.sh | sh`
- Redis running on `localhost:6379` — `brew install redis && brew services start redis` (macOS)

### Setup

```bash
cp .env.example .env
# Fill in APPIFY_GATEWAY_AUTH and JWT_SECRET in .env
uv sync
```

### Run

```bash
./run-local.sh
# or
uv run uvicorn appify_connector.main:app --reload --port 8080
```

OpenAPI docs at <http://localhost:8080/docs>.

### Smoke test against real Appify

```bash
# Login
TOKEN=$(curl -s http://localhost:8080/api/v1/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"business_name":"YOUR_BIZ","email":"you@example.com","password":"..."}' \
  | jq -r .access_token)

# List objects
curl -s http://localhost:8080/api/v1/objects \
  -H "Authorization: Bearer $TOKEN" | jq '.[0:3]'

# Describe one
curl -s http://localhost:8080/api/v1/objects/jcpay_student \
  -H "Authorization: Bearer $TOKEN" | jq

# Logout
curl -s -X POST http://localhost:8080/api/v1/auth/logout \
  -H "Authorization: Bearer $TOKEN"
```

### Tests

The integration test hits the real Appify API. It's skipped automatically unless you set credentials:

```bash
export APPIFY_TEST_BUSINESS_NAME=...
export APPIFY_TEST_EMAIL=...
export APPIFY_TEST_PASSWORD=...
uv run pytest
```

Redis must be running.

## API

| Method | Path | Description |
|---|---|---|
| POST | `/api/v1/auth/login` | Exchange credentials for a connector JWT |
| POST | `/api/v1/auth/logout` | Revoke the current session |
| GET | `/api/v1/objects` | List business objects (`?sor=flex` to filter) |
| GET | `/api/v1/objects/{native_api_name}` | Describe an object — fields, PK, types, relationships |
| GET | `/api/v1/sors` | List Systems of Record configured in the tenant |
| GET | `/healthz`, `/livez`, `/readyz` | Health probes |

## Configuration

All settings come from environment variables. See [`.env.example`](.env.example).

| Variable | Required | Notes |
|---|---|---|
| `APPIFY_LOGIN_URL` | no (default `https://login.appify.com`) | Single login entry point |
| `APPIFY_GATEWAY_AUTH` | **yes** | The `Basic ...` header sent to Appify login |
| `JWT_SECRET` | **yes** | HS256 signing key for connector JWTs |
| `JWT_TTL_SECONDS` | no (default 12 h) | Connector token lifetime |
| `REDIS_URL` | no (default `redis://localhost:6379/0`) | Session store |
| `SESSION_TTL_SECONDS` | no (default 23 h) | Stored upstream session TTL |
| `LOG_LEVEL` | no (default `INFO`) | |
| `CORS_ALLOW_ORIGINS` | no | Comma-separated list, blank disables CORS |

## Roadmap

Planned (not in v0):

- Record CRUD: `/api/v1/objects/{name}/records[?...]`
- Attachments
- Bulk operations
- Webhook relay
- OpenTelemetry tracing
