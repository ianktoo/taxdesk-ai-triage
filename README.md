# TaxDesk AI - Attachment Triage Assistant

A simulated customer support tool for a tax prep business. Customers send in
a message plus a few attachments (a form, an ID, a utility bill...), and this
app automatically figures out what each document is, pulls out the key
fields, and tells a human agent whether the request is safe to auto-approve
or needs a closer look.

Document classification and field extraction are powered by the
[Nutrient DWS API](https://www.nutrient.io/).

This is a hackathon demo. There is no real email integration, no real
authentication, and no real customer data - everything is mock/sample data.

## How it works

1. Pick a customer persona (a canned message + a few sample documents).
2. The app runs each attachment through Nutrient DWS to classify it and
   extract fields with a confidence score.
3. It matches the message to a request category (change of address, name
   change, etc.) and writes a one-line summary.
4. Based on confidence scores, the request is marked "Ready to auto-approve"
   or "Needs human review".
5. A review screen shows the extracted fields side by side so a human can
   Approve, Correct & approve, or Reject.
6. Every step is logged to an audit trail, and approvals update a mock
   customer record.

## Project layout

```
api/            FastAPI backend (deployed as Vercel serverless functions)
  config/       env vars, active-adapter selection
  integrations/ vendor adapters behind capability contracts
  services/     business logic
  interface/    API routes
  data/         hardcoded demo personas
data/sample_docs/  generated mock PDFs used by the personas
frontend/       React + TypeScript app (Vite)
tests/          contract tests (adapters) and interface smoke tests
```

## Running it locally

You'll need Python 3.11+ and Node 18+.

### 1. Backend

```bash
python -m venv .venv
.venv/Scripts/activate        # on macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Open `.env` and fill in `NUTRIENT_DWS_API_KEY` with your key from
[nutrient.io](https://www.nutrient.io/), and set `DOCUMENT_EXTRACTOR=nutrient`.
Leaving `DOCUMENT_EXTRACTOR=mock` runs the app with canned extraction data and
needs no API key at all - handy for trying out the UI first.

Then start the API:

```bash
uvicorn api.main:app --reload --port 8000
```

### 2. Frontend

```bash
cd frontend
npm install
npm run dev
```

Open the URL Vite prints (usually http://localhost:5173). The frontend proxies
`/api/*` requests to the backend on port 8000.

### 3. Run the tests

```bash
pytest tests -q
```

## Demo throttling (optional)

Since there's no login, the API optionally rate-limits requests per client IP
using [Upstash Redis](https://upstash.com) (free tier). Set
`UPSTASH_REDIS_REST_URL` and `UPSTASH_REDIS_REST_TOKEN` in `.env` to turn it
on; leave them blank and rate limiting is simply disabled (fine for local
dev).

## Deploying

The app is set up to deploy to Vercel: the FastAPI app under `api/` runs as a
Python serverless function, and the frontend builds as a static site. See
`vercel.json` for the routing config.

```bash
vercel
```

Set the same environment variables from `.env` in your Vercel project
settings (Nutrient key, and optionally the Upstash rate-limit settings).

## Configuration reference

| Variable | Purpose | Default |
|---|---|---|
| `DOCUMENT_EXTRACTOR` | `mock` or `nutrient` | `mock` |
| `NUTRIENT_DWS_API_KEY` | Your Nutrient DWS API key | (empty) |
| `NUTRIENT_DWS_BASE_URL` | Nutrient DWS API base URL | `https://api.nutrient.io` |
| `AUTO_APPROVE_CONFIDENCE_THRESHOLD` | Minimum field confidence to auto-approve | `0.85` |
| `UPSTASH_REDIS_REST_URL` | Upstash Redis REST URL (optional) | (empty) |
| `UPSTASH_REDIS_REST_TOKEN` | Upstash Redis REST token (optional) | (empty) |
| `RATE_LIMIT_MAX_REQUESTS` | Requests allowed per IP per window | `5` |
| `RATE_LIMIT_WINDOW_SECONDS` | Rate-limit window length in seconds | `3600` |
