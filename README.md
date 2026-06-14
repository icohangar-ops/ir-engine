<div align="center">

# IR Engine

**Autonomous investor relations automation.** Generate IR packages, run scenario simulations, and monitor critical minerals — with a Veris-ready briefing layer for persistent scenario memory.

[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?logo=python)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-009688?logo=fastapi)](https://fastapi.tiangolo.com/)
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

# Set API keys
export OPENAI_API_KEY="your-key"
export FRED_API_KEY="your-key"

# Run the server
uvicorn cubiczan_server:app --reload
```

### Generate an IR Package

```bash
curl -X POST http://localhost:8000/v1/investor-relations/generate \
  -H "Content-Type: application/json" \
  -d '{
    "company": "Acme Mining",
    "period": "Q1 2026",
    "type": "quarterly_update",
    "context": "Revenue up 15% YoY, critical minerals exposure"
  }'
```

### Run a Scenario Simulation

```bash
curl -X POST http://localhost:8000/v1/veris/simulate \
  -H "Content-Type: application/json" \
  -d '{
    "scenario": "US-China tariff escalation on rare earths",
    "impact": "25% tariff on imports from China",
    "timeframe": "Q2-Q4 2026"
  }'
```

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

## Project Structure

```
ir-engine/
├── cubiczan_server.py              # FastAPI entry point
├── investor_relations_engine.py    # IR package generation
├── market_data_clients.py          # FRED, Alpha Vantage, etc.
├── critical_minerals_monitor.py    # Commodity + tariff monitoring
├── veris_simulation_engine.py      # Scenario simulation + briefing
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
