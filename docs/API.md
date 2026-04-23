# API Guide

## Health

`GET /health`

Returns server status.

## Inference

### `POST /v1/chat/completions`

Runs the configured inference backend and returns a chat-style response envelope.

Optional request fields:

- `backend`: override the env-configured backend for one request
- `model`: override the env-configured model for one request

## Investor Relations

### `POST /v1/investor-relations/generate`

Generates a full IR package.

### `GET /v1/investor-relations/sample`

Returns a sample IR request payload.

### `POST /v1/investor-relations/market-context`

Returns macro and market context from FRED and Alpha Vantage.

## Critical Minerals

### `POST /v1/critical-minerals/context`

Builds commodity, tariff, and IR implication context.

### `GET /v1/critical-minerals/sample`

Returns a sample critical-metals request payload.

## Veris

### `POST /v1/veris/simulate`

Runs base, bull, bear, and stress scenarios against a normalized input schema.

### `POST /v1/veris/briefing`

Builds a Veris-ready memory/briefing export around the simulation output.

### `POST /v1/veris/export`

Builds a Veris local-memory packet with:

- normalized scenario context
- persistent memory facts
- downside control-case summary
- Markdown memory content suitable for Veris notes or memory seeding

### `GET /v1/veris/sample`

Returns a sample Veris simulation payload.
