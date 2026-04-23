# Architecture

## Layers

### 1. Investor Relations Engine

`investor_relations_engine.py` converts structured company data into:

- investment evaluation
- risk matrix
- financial story
- quarterly update
- pitch deck
- board materials

### 2. Market Context Layer

`market_data_clients.py` enriches IR outputs with:

- FRED macro series
- Alpha Vantage company and benchmark context
- sector-specific benchmark mapping
- macro regime adjustments

### 3. Metals and Tariff Monitoring Layer

`critical_minerals_monitor.py` provides:

- multi-provider commodity coverage
- tariff-watch monitoring
- IR implication generation

Provider order is currently:

1. Zyla Labs where symbol support is configured
2. AKShare snapshots where available
3. Tushare futures metadata and history where configured

### 4. Veris Scenario Layer

`veris_simulation_engine.py` normalizes scenario inputs and produces:

- base / bull / bear / stress scenario outputs
- board talking points
- investor Q&A prompts
- Veris-ready memory facts and briefing text

## Current request flow

1. Raw company or market payload enters the server.
2. Optional market or commodity providers enrich the payload.
3. IR engine or Veris engine transforms the normalized payload.
4. Structured outputs are returned as JSON for downstream decks, dashboards, or memory systems.

## Veris integration model

Veris is treated as a persistent context consumer rather than a market-data provider. The stack exports:

- normalized scenario payloads
- memory facts
- scenario summary lines
- a ready-to-ingest briefing prompt

