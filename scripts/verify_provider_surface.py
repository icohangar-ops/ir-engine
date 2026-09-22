#!/usr/bin/env python3
"""Deterministic evidence for the documented market-data and minerals surface.

Parses ``market_data_clients.py`` and ``critical_minerals_monitor.py`` with
``ast`` — no import (both modules pull in the optional cubiczan-resilience
dependency), no network — and asserts the surface claimed by README.md,
docs/ARCHITECTURE.md, and docs/PROVIDERS.md: the FRED series set, the
sector-benchmark mapping, graceful per-provider degradation, the commodity
provider order (Zyla -> AKShare -> Tushare), the tracked commodity coverage,
and the tariff/USTR watchers.

Exit 0 when every check holds; exit 1 with the failing checks otherwise.
"""

import ast
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MARKET_PATH = os.path.join(ROOT, "market_data_clients.py")
MINERALS_PATH = os.path.join(ROOT, "critical_minerals_monitor.py")

EXPECTED_FRED_SERIES = {
    "federal_funds_rate": "FEDFUNDS",
    "ten_year_treasury": "DGS10",
    "inflation_cpi": "CPIAUCSL",
    "unemployment_rate": "UNRATE",
}
EXPECTED_PROVIDER_PRIORITY = {"zyla": 0, "akshare": 1, "tushare": 2}
EXPECTED_COMMODITIES = {
    "copper",
    "aluminum",
    "zinc",
    "nickel",
    "cobalt",
    "manganese",
    "lithium_carbonate",
    "gold",
    "silver",
}
EXPECTED_ZYLA_SYMBOLS = {"XCU", "XAL", "XZN", "XNI", "XAU", "XAG"}


def _module(path):
    with open(path, encoding="utf-8") as handle:
        return ast.parse(handle.read(), filename=path)


def _functions(tree):
    return {
        node.name: node
        for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef)
    }


def _string_dict_constant(tree, name):
    """Return {key: value} scalar constants for a module-level dict Assign."""
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.Assign)
            and len(node.targets) == 1
            and isinstance(node.targets[0], ast.Name)
            and node.targets[0].id == name
            and isinstance(node.value, ast.Dict)
        ):
            entries = {}
            for key, value in zip(node.value.keys, node.value.values):
                if isinstance(key, ast.Constant) and isinstance(value, ast.Constant):
                    entries[key.value] = value.value
            return entries
    return None


def main():
    checks = []

    market = _module(MARKET_PATH)
    market_fns = _functions(market)

    # P1 — the market context layer functions exist as documented.
    market_expected = {
        "fetch_market_context",
        "fetch_fred_series_snapshot",
        "fetch_alpha_vantage_snapshot",
        "resolve_sector_benchmark",
    }
    checks.append(
        (
            market_expected.issubset(market_fns),
            "P1 market functions: missing " + str(sorted(market_expected - set(market_fns))),
        )
    )

    # P2 — the four documented FRED macro series are wired.
    fred = _string_dict_constant(market, "DEFAULT_FRED_SERIES")
    checks.append(
        (
            fred == EXPECTED_FRED_SERIES,
            f"P2 FRED series: expected {EXPECTED_FRED_SERIES}, found {fred}",
        )
    )

    # P3 — sector-aware benchmark selection is backed by a real mapping.
    benchmarks = _string_dict_constant(market, "SECTOR_BENCHMARKS") or {}
    sector_ok = benchmarks.get("technology") == "XLK" and benchmarks.get("materials") == "XLB"
    checks.append(
        (
            sector_ok and len(benchmarks) >= 10,
            "P3 sector benchmarks: expected technology->XLK and materials->XLB "
            f"in a mapping of at least 10 sectors, found {len(benchmarks)} entries",
        )
    )

    # P4 — graceful degradation: provider failures become warnings, not raises.
    fetch_fn = market_fns.get("fetch_market_context")
    try_handlers = (
        sum(isinstance(n, ast.Try) for n in ast.walk(fetch_fn)) if fetch_fn else 0
    )
    checks.append(
        (
            try_handlers >= 2,
            "P4 graceful degradation: fetch_market_context must guard both "
            f"provider calls with try/except (found {try_handlers})",
        )
    )

    minerals = _module(MINERALS_PATH)
    minerals_fns = _functions(minerals)

    # P5 — the minerals and tariff monitoring functions exist as documented.
    minerals_expected = {
        "fetch_commodity_context",
        "fetch_zyla_commodity_data",
        "fetch_akshare_commodity_snapshot",
        "fetch_tushare_commodity_data",
        "watch_tariff_changes",
        "watch_ustr_changes",
        "analyze_ir_implications",
        "generate_critical_minerals_context",
    }
    checks.append(
        (
            minerals_expected.issubset(minerals_fns),
            "P5 minerals functions: missing " + str(sorted(minerals_expected - set(minerals_fns))),
        )
    )

    # P6 — commodity provider order is Zyla -> AKShare -> Tushare.
    priority = None
    fetch_ctx = minerals_fns.get("fetch_commodity_context")
    if fetch_ctx is not None:
        for node in ast.walk(fetch_ctx):
            if (
                isinstance(node, ast.Assign)
                and len(node.targets) == 1
                and isinstance(node.targets[0], ast.Name)
                and node.targets[0].id == "provider_priority"
                and isinstance(node.value, ast.Dict)
            ):
                priority = {
                    k.value: v.value
                    for k, v in zip(node.value.keys, node.value.values)
                    if isinstance(k, ast.Constant) and isinstance(v, ast.Constant)
                }
    checks.append(
        (
            priority == EXPECTED_PROVIDER_PRIORITY,
            f"P6 provider order: expected {EXPECTED_PROVIDER_PRIORITY}, found {priority}",
        )
    )

    # P7 — commodity coverage: the nine tracked commodities and Zyla symbols.
    commodities = set()
    for node in ast.walk(minerals):
        if (
            isinstance(node, ast.Assign)
            and len(node.targets) == 1
            and isinstance(node.targets[0], ast.Name)
            and node.targets[0].id == "CRITICAL_MINERALS"
            and isinstance(node.value, ast.Dict)
        ):
            commodities = {
                k.value for k in node.value.keys if isinstance(k, ast.Constant)
            }
    zyla_symbols = set()
    for node in ast.walk(minerals):
        if isinstance(node, ast.Dict):
            for key, value in zip(node.keys, node.values):
                if (
                    isinstance(key, ast.Constant)
                    and key.value == "zyla_symbol"
                    and isinstance(value, ast.Constant)
                ):
                    zyla_symbols.add(value.value)
    checks.append(
        (
            set(commodities) == EXPECTED_COMMODITIES and zyla_symbols == EXPECTED_ZYLA_SYMBOLS,
            "P7 commodity coverage: expected exactly the 9 tracked commodities "
            f"with Zyla symbols {sorted(EXPECTED_ZYLA_SYMBOLS)}, found "
            f"{sorted(commodities)} / {sorted(zyla_symbols)}",
        )
    )

    # P8 — tariff and trade-policy sources are wired (Federal Register, USTR).
    source_urls = {
        node.targets[0].id: node.value.value
        for node in minerals.body
        if isinstance(node, ast.Assign)
        and len(node.targets) == 1
        and isinstance(node.targets[0], ast.Name)
        and isinstance(node.value, ast.Constant)
        and isinstance(node.value.value, str)
        and node.value.value.startswith("https://")
    }
    checks.append(
        (
            "FEDERAL_REGISTER_API" in source_urls and "USTR_LATEST_PRESS_RELEASES" in source_urls,
            "P8 tariff sources: expected FEDERAL_REGISTER_API and "
            f"USTR_LATEST_PRESS_RELEASES URL constants, found {sorted(source_urls)}",
        )
    )

    failures = [message for ok, message in checks if not ok]
    for ok, message in checks:
        label = message.split(": ", 1)[0]
        print(f"{'OK  ' if ok else 'FAIL'} {message if not ok else label + ': ok'}")
    if failures:
        print(f"PROVIDER SURFACE: FAILED ({len(failures)} of {len(checks)} checks)")
        return 1
    print(f"PROVIDER SURFACE: OK ({len(checks)}/{len(checks)} checks)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
