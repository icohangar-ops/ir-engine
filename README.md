<div align="center">

# IR Engine

**Autonomous investor relations automation.** Generate IR packages, run scenario simulations, and monitor critical minerals — with a Veris-ready briefing layer for persistent scenario memory.

[![Python](https://img.shields.io/badge/Python-3.9+-3776AB?logo=python)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow)](LICENSE)

</div>

---

## The Problem

Investor relations teams spend weeks assembling quarterly updates, pitch decks, and board materials. Market context changes daily, but IR packages are built from static snapshots. Scenario analysis — "what if tariffs increase 20%?" — requires manual research that takes days.

IR Engine automates the entire IR pipeline and adds a simulation layer that lets you test narratives before publishing them.

---

## What IR Engine Does

| Endpoint | What It Does |
|----------|-------------|
| `POST /v1/investor-relations/generate` | Investment evaluation, risk assessment, quarterly update, pitch deck, board materials |
| `POST /v1/investor-relations/market-context` | Macro and market context from FRED and Alpha Vantage |
| `POST /v1/critical-minerals/context` | Commodity and tariff context with provider fallbacks |
| `POST /v1/veris/simulate` | Scenario analysis using normalized Veris-ready schema |
| `POST /v1/veris/briefing` | Veris-friendly context briefing for persistent scenario memory |
| `POST /v1/veris/export` | Veris local-memory packet (JSON + Markdown artifact) |

---

## What Makes This Different

Most IR tools generate static documents. IR Engine adds **scenario simulation**:

- Run "what-if" analyses on IR narratives before publishing
- Veris briefing layer maintains persistent scenario memory across sessions
- Multi-provider fallback (OpenAI, Gemini, FRED, Alpha Vantage, Zyla Labs, AKShare, Tushare)
- Critical minerals and tariff monitoring built-in — not bolted on

---

## Quick Start

```bash
git clone https://github.com/icohangar-ops/ir-engine.git
cd ir-engine
pip install -r requirements.txt

# Set API keys (populate only the providers you use)
export OPENAI_API_KEY="your-key"
export FRED_API_KEY="your-key"

# Run the server (Python standard-library HTTP server)
python cubiczan_server.py --port 8000
```

The server is also available in two CLI modes: `python cubiczan_server.py --test`
runs a sample inference query, and `python cubiczan_server.py --interactive` opens
a chat session. Set `CUBICZAN_SERVER_API_KEY` to require an `Authorization` header
on every request.

### Generate an IR Package

```bash
curl -X POST http://localhost:8000/v1/investor-relations/generate \
  -H "Content-Type: application/json" \
  -d '{
    "company": { "name": "Acme Mining", "sector": "Materials" },
    "financials": {
      "current_revenue": 8400000,
      "prior_revenue": 6200000,
      "cash_balance": 11600000,
      "runway_months": 14
    },
    "metrics": {
      "growth_score": 4.2,
      "efficiency_score": 3.6,
      "market_score": 4.4
    }
  }'
```

See [`sample_investor_relations_request.json`](./sample_investor_relations_request.json)
for a complete payload, or `GET /v1/investor-relations/sample` to fetch it from a
running server.

### Run a Scenario Simulation

```bash
curl -X POST http://localhost:8000/v1/veris/simulate \
  -H "Content-Type: application/json" \
  -d '{
    "company_profile": {
      "name": "Atlas Critical Minerals",
      "value_chain_position": "producer",
      "geography_focus": "United States and Asia"
    },
    "financials": {
      "revenue": 185000000,
      "ebitda_margin": 0.18,
      "cash_balance": 72000000,
      "runway_months": 18
    }
  }'
```

See [`sample_veris_simulation_request.json`](./sample_veris_simulation_request.json)
for a complete payload, or `GET /v1/veris/sample` to fetch it from a running server.

---

## Provider Strategy

| Provider | Purpose | Fallback |
|----------|---------|----------|
| OpenAI | Default inference (Responses API) | Gemini |
| Gemini | Alternate inference | OpenAI |
| FRED | Macro context | — |
| Alpha Vantage | Market + sector benchmarks | — |
| Zyla Labs | Metal rates | — |
| AKShare | China exchange snapshots | — |
| Tushare | China futures metadata | — |
| Federal Register + USTR | Tariff and trade policy | — |

---

## Airbyte Integration

IR Engine includes an optional [Airbyte AI Agents SDK](https://docs.airbyte.com/ai-agents-sdk/) integration layer via `airbyte_providers.py`. This module provides:

- **Async Airbyte-backed data fetching** as an alternative to the synchronous direct HTTP clients
- **Graceful fallback** — if Airbyte is unavailable or a connector doesn't exist for a data source, the module falls back to the existing direct clients automatically
- **MCP server configuration** — connect AI agents (Claude, Cursor, VS Code) to Airbyte-managed data sources
- **Hybrid mode** — the recommended `fetch_hybrid_market_context()` function tries Airbyte first, then merges direct client results

### Why Airbyte?

Airbyte centralizes credential management, retry logic, and connector configuration. When Airbyte adds native connectors for financial data APIs (FRED, Alpha Vantage, SEC EDGAR), they can be wired in without changing calling code.

### Current Status

Airbyte's agent SDK ships ~48 connectors (CRM, billing, marketing, dev tools, analytics). **None of ir-engine's data sources have native Airbyte connectors yet.** The integration layer is a forward-looking adapter pattern:

| Data Source | Airbyte Connector | Status |
|-------------|------------------|--------|
| FRED | — | Falls back to `market_data_clients` |
| Alpha Vantage | — | Falls back to `market_data_clients` |
| SEC EDGAR | — | Falls back to `edgar_client` |
| Federal Register | — | Falls back to `critical_minerals_monitor` |
| Zyla Labs / AKShare / Tushare | — | Specialized APIs, no equivalent |

### Setup

```bash
# Install the SDK (included in requirements.txt)
pip install airbyte-agent-sdk

# Set credentials
export AIRBYTE_CLIENT_ID=<your_client_id>
export AIRBYTE_CLIENT_SECRET=<your_client_secret>
```

### Usage

```python
import asyncio
from airbyte_providers import fetch_hybrid_market_context, is_airbyte_available

# Check if Airbyte is configured
if is_airbyte_available():
    result = asyncio.run(fetch_hybrid_market_context(
        company_symbol="AAPL",
        benchmark_symbol="SPY",
        sector="Technology",
    ))
    # result["data_source"] == "hybrid_airbyte_plus_direct"
    # result["airbyte"] contains Airbyte metadata (warnings, connectors used)
else:
    # Falls back to direct clients automatically
    from market_data_clients import fetch_market_context
    result = fetch_market_context()
```

### MCP Server Setup

Connect your AI agent to Airbyte-managed data sources:

```bash
# Claude Code
claude mcp add --transport http airbyte-agent https://mcp.airbyte.ai/mcp

# Or get the full config dict:
from airbyte_providers import get_mcp_config
print(get_mcp_config())
```

---

## Project Structure

```
ir-engine/
├── cubiczan_server.py              # HTTP API server entry point (stdlib http.server)
├── investor_relations_engine.py    # IR package generation
├── market_data_clients.py          # FRED, Alpha Vantage, etc.
├── critical_minerals_monitor.py    # Commodity + tariff monitoring
├── veris_simulation_engine.py      # Scenario simulation + briefing
├── edgar_client.py                 # SEC EDGAR filings access
├── airbyte_providers.py            # Airbyte SDK integration layer (optional)
├── docs/
│   ├── ARCHITECTURE.md
│   ├── API.md
│   ├── SETUP.md
│   ├── PROVIDERS.md
│   └── SECURITY.md
└── sample_*.json                   # Example payloads
```

---

## License

MIT. See [`LICENSE`](./LICENSE).

---

## CHP Governance

This repository is hardened with the [Consensus Hardening Protocol (CHP)](https://codeberg.org/cubiczan/consensus-hardening-protocol).

### Protocol Layers
- **R0 Gate**: Solvable, Scoped, Valid, Worth_it
- **Foundation Disclosure**: 1-3 weakest assumptions
- **Adversarial Layer**: Devil's advocate at Phase 0 and Round 3
- **State Machine**: EXPLORING → PROVISIONAL → PROVISIONAL_LOCK → LOCKED
- **Third-Party Validation**: Independent CONFIRM/REJECT before lock

### Domain Configuration
- **Category**: Finance (CFO Accuracy)
- **Foundation Threshold**: 100
- **CFO Accuracy Guard**: Enabled

### CHP Version
cognitive-mesh-orchestrator 0.1.0 | [Protocol Docs](https://codeberg.org/cubiczan/consensus-hardening-protocol)
