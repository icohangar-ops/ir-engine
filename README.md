# Cubiczan Investor Relations, Metals Monitoring, and Veris Simulation Stack

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10+-3776AB?logo=python" alt="Python" />
  <img src="https://img.shields.io/badge/FastAPI-009688?logo=fastapi" alt="FastAPI" />
  <img src="https://img.shields.io/badge/OpenAI-412991?logo=openai" alt="OpenAI" />
  <img src="https://img.shields.io/badge/FRED-003366?logo=fred" alt="FRED" />
  <img src="https://img.shields.io/badge/License-MIT-yellow" alt="MIT" />
</p>

This workspace now includes a structured set of services for:

- investor-relations package generation
- macro and market-context enrichment
- commodity and tariff monitoring for mining, metals, and critical-mineral companies
- Veris-ready scenario simulation and briefing export

## Core capabilities

- `POST /v1/investor-relations/generate`
  Generates investment evaluation, risk assessment, quarterly update, pitch deck, and board materials.

- `POST /v1/investor-relations/market-context`
  Pulls macro and market context from FRED and Alpha Vantage.

- `POST /v1/critical-minerals/context`
  Builds commodity and tariff context using provider fallbacks.

- `POST /v1/veris/simulate`
  Runs scenario analysis using a normalized Veris-ready schema.

- `POST /v1/veris/briefing`
  Produces a Veris-friendly context briefing for persistent scenario memory.

- `POST /v1/veris/export`
  Produces a Veris local-memory packet with JSON fields plus a Markdown memory artifact.

## Main modules

- [cubiczan_server.py](./cubiczan_server.py)
- [investor_relations_engine.py](./investor_relations_engine.py)
- [market_data_clients.py](./market_data_clients.py)
- [critical_minerals_monitor.py](./critical_minerals_monitor.py)
- [veris_simulation_engine.py](./veris_simulation_engine.py)

## Sample payloads

- [sample_investor_relations_request.json](./sample_investor_relations_request.json)
- [sample_critical_minerals_request.json](./sample_critical_minerals_request.json)
- [sample_veris_simulation_request.json](./sample_veris_simulation_request.json)

## Provider strategy

- `OpenAI`: default inference backend via the Responses API
- `Gemini`: optional alternate inference backend
- `FRED`: macro context
- `Alpha Vantage`: market and sector benchmark context
- `Zyla Labs`: optional metal rates provider for covered metals
- `AKShare`: optional China exchange snapshot path
- `Tushare`: optional China futures metadata and history path
- `Federal Register` and `USTR`: tariff and trade-policy monitoring
- `Veris`: local memory/briefing consumer, not treated as a hosted market-data API

## Documentation

- [docs/ARCHITECTURE.md](./docs/ARCHITECTURE.md)
- [docs/API.md](./docs/API.md)
- [docs/SETUP.md](./docs/SETUP.md)
- [docs/PROVIDERS.md](./docs/PROVIDERS.md)
- [docs/SECURITY.md](./docs/SECURITY.md)
- [docs/GITHUB_PUBLISH.md](./docs/GITHUB_PUBLISH.md)
