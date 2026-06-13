from __future__ import annotations

import json
import os
from datetime import datetime
from typing import Any, Dict, List, Optional
from urllib.parse import urlencode
from urllib.request import urlopen

from cubiczan_resilience import resilient


FRED_BASE_URL = "https://api.stlouisfed.org/fred"
ALPHA_VANTAGE_BASE_URL = "https://www.alphavantage.co/query"

DEFAULT_FRED_SERIES = {
    "federal_funds_rate": "FEDFUNDS",
    "ten_year_treasury": "DGS10",
    "inflation_cpi": "CPIAUCSL",
    "unemployment_rate": "UNRATE",
}

SECTOR_BENCHMARKS = {
    "technology": "XLK",
    "information technology": "XLK",
    "software": "XLK",
    "industrials": "XLI",
    "industrial": "XLI",
    "industrial automation": "XLI",
    "healthcare": "XLV",
    "health care": "XLV",
    "financial services": "XLF",
    "financial": "XLF",
    "consumer discretionary": "XLY",
    "consumer staples": "XLP",
    "energy": "XLE",
    "materials": "XLB",
    "real estate": "XLRE",
    "utilities": "XLU",
    "communication services": "XLC",
}


@resilient(timeout=20, max_attempts=3)
def _get_json(url: str, timeout: int = 20) -> Dict[str, Any]:
    with urlopen(url, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def _safe_float(value: Any) -> Optional[float]:
    try:
        if value in (None, "", "."):
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _fred_url(path: str, **params: Any) -> str:
    query = urlencode({**params, "file_type": "json"})
    return f"{FRED_BASE_URL}/{path}?{query}"


def _alpha_url(**params: Any) -> str:
    return f"{ALPHA_VANTAGE_BASE_URL}?{urlencode(params)}"


def _normalize_sector(sector: Optional[str]) -> str:
    return (sector or "").strip().lower()


def resolve_sector_benchmark(sector: Optional[str], fallback_symbol: str = "SPY") -> Dict[str, str]:
    normalized = _normalize_sector(sector)
    benchmark_symbol = SECTOR_BENCHMARKS.get(normalized, fallback_symbol)
    reason = "default_market_benchmark"
    if normalized and benchmark_symbol != fallback_symbol:
        reason = f"sector_benchmark_for_{normalized.replace(' ', '_')}"
    return {
        "input_sector": sector or "",
        "normalized_sector": normalized,
        "benchmark_symbol": benchmark_symbol,
        "reason": reason,
    }


def fetch_fred_series_snapshot(
    series_map: Optional[Dict[str, str]] = None,
    api_key: Optional[str] = None,
) -> Dict[str, Any]:
    fred_api_key = api_key or os.environ.get("FRED_API_KEY")
    if not fred_api_key:
        raise ValueError("FRED_API_KEY is not configured.")

    series_to_fetch = series_map or DEFAULT_FRED_SERIES
    snapshots: Dict[str, Any] = {}

    for label, series_id in series_to_fetch.items():
        series_meta = _get_json(
            _fred_url("series", api_key=fred_api_key, series_id=series_id)
        )
        observations = _get_json(
            _fred_url(
                "series/observations",
                api_key=fred_api_key,
                series_id=series_id,
                sort_order="desc",
                limit=2,
            )
        )

        series_info = (series_meta.get("seriess") or [{}])[0]
        obs = observations.get("observations") or []
        latest = obs[0] if obs else {}
        previous = obs[1] if len(obs) > 1 else {}
        latest_value = _safe_float(latest.get("value"))
        previous_value = _safe_float(previous.get("value"))
        change = None
        if latest_value is not None and previous_value is not None:
            change = latest_value - previous_value

        snapshots[label] = {
            "series_id": series_id,
            "title": series_info.get("title", series_id),
            "units": series_info.get("units_short") or series_info.get("units"),
            "frequency": series_info.get("frequency_short") or series_info.get("frequency"),
            "observation_date": latest.get("date"),
            "latest_value": latest_value,
            "previous_value": previous_value,
            "change": change,
        }

    return {
        "source": "FRED",
        "fetched_at": datetime.utcnow().isoformat() + "Z",
        "series": snapshots,
    }


def _extract_latest_time_series_point(series_payload: Dict[str, Any]) -> Dict[str, Any]:
    time_series_key = next((key for key in series_payload.keys() if "Time Series" in key), None)
    if not time_series_key:
        return {}
    time_series = series_payload.get(time_series_key, {})
    if not time_series:
        return {}
    latest_date = sorted(time_series.keys())[-1]
    point = time_series[latest_date]
    close_value = _safe_float(point.get("4. close") or point.get("5. adjusted close"))
    return {
        "date": latest_date,
        "close": close_value,
    }


def fetch_alpha_vantage_snapshot(
    company_symbol: Optional[str] = None,
    benchmark_symbol: str = "SPY",
    sector: Optional[str] = None,
    api_key: Optional[str] = None,
) -> Dict[str, Any]:
    alpha_key = api_key or os.environ.get("ALPHAVANTAGE_API_KEY")
    if not alpha_key:
        raise ValueError("ALPHAVANTAGE_API_KEY is not configured.")

    resolved_benchmark = resolve_sector_benchmark(sector, fallback_symbol=benchmark_symbol)
    payload: Dict[str, Any] = {
        "source": "Alpha Vantage",
        "fetched_at": datetime.utcnow().isoformat() + "Z",
        "benchmark_symbol": resolved_benchmark["benchmark_symbol"],
        "benchmark_selection": resolved_benchmark,
    }

    benchmark_quote = _get_json(
        _alpha_url(function="GLOBAL_QUOTE", symbol=resolved_benchmark["benchmark_symbol"], apikey=alpha_key)
    )
    benchmark_daily = _get_json(
        _alpha_url(
            function="TIME_SERIES_DAILY",
            symbol=resolved_benchmark["benchmark_symbol"],
            outputsize="compact",
            apikey=alpha_key,
        )
    )
    payload["benchmark"] = {
        "quote": benchmark_quote.get("Global Quote", {}),
        "latest_daily": _extract_latest_time_series_point(benchmark_daily),
    }

    if company_symbol:
        company_quote = _get_json(
            _alpha_url(function="GLOBAL_QUOTE", symbol=company_symbol, apikey=alpha_key)
        )
        company_overview = _get_json(
            _alpha_url(function="OVERVIEW", symbol=company_symbol, apikey=alpha_key)
        )
        overview_sector = company_overview.get("Sector") or sector
        if resolved_benchmark["reason"] == "default_market_benchmark" and overview_sector:
            resolved_benchmark = resolve_sector_benchmark(overview_sector, fallback_symbol=benchmark_symbol)
            if resolved_benchmark["benchmark_symbol"] != payload["benchmark_symbol"]:
                benchmark_quote = _get_json(
                    _alpha_url(function="GLOBAL_QUOTE", symbol=resolved_benchmark["benchmark_symbol"], apikey=alpha_key)
                )
                benchmark_daily = _get_json(
                    _alpha_url(
                        function="TIME_SERIES_DAILY",
                        symbol=resolved_benchmark["benchmark_symbol"],
                        outputsize="compact",
                        apikey=alpha_key,
                    )
                )
                payload["benchmark_symbol"] = resolved_benchmark["benchmark_symbol"]
                payload["benchmark_selection"] = resolved_benchmark
                payload["benchmark"] = {
                    "quote": benchmark_quote.get("Global Quote", {}),
                    "latest_daily": _extract_latest_time_series_point(benchmark_daily),
                }
        payload["company_symbol"] = company_symbol
        payload["company"] = {
            "quote": company_quote.get("Global Quote", {}),
            "overview": {
                "name": company_overview.get("Name"),
                "exchange": company_overview.get("Exchange"),
                "sector": company_overview.get("Sector"),
                "industry": company_overview.get("Industry"),
                "market_capitalization": company_overview.get("MarketCapitalization"),
                "pe_ratio": company_overview.get("PERatio"),
                "price_to_sales_ratio_ttm": company_overview.get("PriceToSalesRatioTTM"),
                "profit_margin": company_overview.get("ProfitMargin"),
            },
        }

    return payload


def fetch_market_context(
    company_symbol: Optional[str] = None,
    benchmark_symbol: str = "SPY",
    sector: Optional[str] = None,
    fred_series: Optional[Dict[str, str]] = None,
) -> Dict[str, Any]:
    context: Dict[str, Any] = {"warnings": []}

    try:
        context["fred"] = fetch_fred_series_snapshot(series_map=fred_series)
    except Exception as exc:
        context["warnings"].append(f"FRED unavailable: {exc}")

    try:
        context["alpha_vantage"] = fetch_alpha_vantage_snapshot(
            company_symbol=company_symbol,
            benchmark_symbol=benchmark_symbol,
            sector=sector,
        )
    except Exception as exc:
        context["warnings"].append(f"Alpha Vantage unavailable: {exc}")

    return context
