# Provider Notes

## FRED

Used for macro context:

- policy rate
- treasury yield
- CPI
- unemployment

## Alpha Vantage

Used for:

- company quote context
- sector-aware benchmark selection
- simple market regime signals

## Zyla Labs

Used as an optional metals-rate path for supported symbols.

Current integration is strongest for:

- gold
- silver
- copper
- aluminum
- zinc
- nickel

Specialty materials such as lithium carbonate, manganese, and cobalt may still need China-exchange or specialized benchmark paths.

## AKShare

Used as an optional exchange-facing snapshot provider, especially for China-linked commodity and futures data.

## Tushare

Used as an optional futures provider for:

- contract metadata
- daily futures history
- exchange-based contract selection

## Federal Register and USTR

Used for tariff, rulemaking, and trade-policy monitoring.

## Veris

Veris is not used as a price API.

It is used as the persistence and context layer that can absorb:

- scenario facts
- summary lines
- strategic memory prompts

