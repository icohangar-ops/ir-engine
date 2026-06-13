from __future__ import annotations

import json
import os
import re
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from urllib.parse import quote_plus
from urllib.request import Request, urlopen

from cubiczan_resilience import resilient


FEDERAL_REGISTER_API = "https://www.federalregister.gov/api/v1/documents.json"
USTR_LATEST_PRESS_RELEASES = "https://ustr.gov/callout/latest-press-releases"
ZYLA_METALS_BASE_URL = "https://zylalabs.com/api/2657/real-time+metal+prices+api"

CRITICAL_MINERALS = {
    "copper": {
        "display_name": "Copper",
        "china_exchange_symbol": "沪铜",
        "market": "SHFE",
        "tushare_symbol": "CU",
        "tushare_exchange": "SHFE",
        "zyla_symbol": "XCU",
        "price_unit": "RMB/metric ton",
        "tariff_keywords": ["copper", "base metals", "mining", "smelting", "refining", "tariff"],
    },
    "aluminum": {
        "display_name": "Aluminum",
        "china_exchange_symbol": "沪铝",
        "market": "SHFE",
        "tushare_symbol": "AL",
        "tushare_exchange": "SHFE",
        "zyla_symbol": "XAL",
        "price_unit": "RMB/metric ton",
        "tariff_keywords": ["aluminum", "base metals", "smelting", "tariff", "trade remedies"],
    },
    "zinc": {
        "display_name": "Zinc",
        "china_exchange_symbol": "沪锌",
        "market": "SHFE",
        "tushare_symbol": "ZN",
        "tushare_exchange": "SHFE",
        "zyla_symbol": "XZN",
        "price_unit": "RMB/metric ton",
        "tariff_keywords": ["zinc", "base metals", "mining", "smelting", "tariff"],
    },
    "nickel": {
        "display_name": "Nickel",
        "china_exchange_symbol": "沪镍",
        "market": "SHFE",
        "tushare_symbol": "NI",
        "tushare_exchange": "SHFE",
        "zyla_symbol": "XNI",
        "price_unit": "RMB/metric ton",
        "tariff_keywords": ["nickel", "battery metals", "critical minerals", "mining", "refining"],
    },
    "cobalt": {
        "display_name": "Cobalt",
        "china_exchange_symbol": "钴",
        "market": "SHFE",
        "price_unit": "RMB/metric ton",
        "tariff_keywords": ["cobalt", "battery materials", "critical minerals", "mining", "refining"],
    },
    "manganese": {
        "display_name": "Manganese",
        "china_exchange_symbol": "锰硅",
        "market": "CZCE",
        "tushare_symbol": "SM",
        "tushare_exchange": "CZCE",
        "price_unit": "RMB/metric ton",
        "tariff_keywords": ["manganese", "critical minerals", "ferroalloy", "mining", "refining"],
    },
    "lithium_carbonate": {
        "display_name": "Lithium Carbonate",
        "china_exchange_symbol": "碳酸锂",
        "market": "GFEX",
        "tushare_symbol": "LC",
        "tushare_exchange": "GFEX",
        "price_unit": "RMB/metric ton",
        "tariff_keywords": ["lithium", "lithium carbonate", "battery materials", "critical minerals", "mining", "refining"],
    },
    "gold": {
        "display_name": "Gold",
        "china_exchange_symbol": "沪金",
        "market": "SHFE",
        "tushare_symbol": "AU",
        "tushare_exchange": "SHFE",
        "zyla_symbol": "XAU",
        "price_unit": "USD/troy ounce or RMB equivalent",
        "tariff_keywords": ["gold", "precious metals", "bullion", "tariff", "trade policy"],
    },
    "silver": {
        "display_name": "Silver",
        "china_exchange_symbol": "沪银",
        "market": "SHFE",
        "tushare_symbol": "AG",
        "tushare_exchange": "SHFE",
        "zyla_symbol": "XAG",
        "price_unit": "USD/troy ounce or RMB equivalent",
        "tariff_keywords": ["silver", "precious metals", "bullion", "tariff", "trade policy"],
    },
}


@resilient(timeout=20, max_attempts=3)
def _get_text(url: str, timeout: int = 20) -> str:
    with urlopen(url, timeout=timeout) as response:
        return response.read().decode("utf-8", errors="ignore")


@resilient(timeout=20, max_attempts=3)
def _get_json(url: str, timeout: int = 20) -> Dict[str, Any]:
    with urlopen(url, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


@resilient(timeout=20, max_attempts=3)
def _get_json_with_headers(url: str, headers: Dict[str, str], timeout: int = 20) -> Dict[str, Any]:
    request = Request(url, headers=headers)
    with urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def _safe_float(value: Any) -> Optional[float]:
    try:
        if value in (None, "", ".", "-", "--"):
            return None
        return float(str(value).replace(",", ""))
    except (TypeError, ValueError):
        return None


def _is_usable_price(value: Any) -> bool:
    parsed = _safe_float(value)
    return parsed is not None and parsed > 0


def _extract_first_available(row: Dict[str, Any], candidates: List[str]) -> Any:
    for candidate in candidates:
        if candidate in row and row[candidate] not in (None, ""):
            return row[candidate]
    return None


def _try_import_akshare():
    try:
        import akshare as ak  # type: ignore

        return ak
    except Exception:
        return None


def _try_import_tushare():
    try:
        import tushare as ts  # type: ignore

        return ts
    except Exception:
        return None


def _invert_rate(rate: Optional[float]) -> Optional[float]:
    if rate in (None, 0):
        return None
    return 1 / rate


def _parse_akshare_dataframe(df: Any, commodity_key: str) -> Dict[str, Any]:
    if df is None:
        return {}
    try:
        records = df.to_dict(orient="records")
    except Exception:
        return {}
    if not records:
        return {}

    target = CRITICAL_MINERALS[commodity_key]
    chosen_row = None
    for row in records:
        row_text = " ".join(str(value) for value in row.values())
        if target["china_exchange_symbol"] in row_text or target["display_name"].lower() in row_text.lower():
            chosen_row = row
            break
    if chosen_row is None:
        chosen_row = records[0]

    price_value = _extract_first_available(
        chosen_row,
        ["最新价", "最新", "收盘价", "收盘", "close", "last", "price", "现价"],
    )
    date_value = _extract_first_available(
        chosen_row,
        ["日期", "交易日期", "date", "datetime", "时间", "更新时间"],
    )
    change_value = _extract_first_available(
        chosen_row,
        ["涨跌幅", "change_percent", "涨跌", "change", "涨跌额"],
    )
    contract_value = _extract_first_available(
        chosen_row,
        ["symbol", "合约", "合约代码", "品种", "name"],
    )

    return {
        "source": "AKShare",
        "provider": "akshare",
        "commodity": commodity_key,
        "contract": contract_value,
        "date": str(date_value) if date_value is not None else None,
        "price": _safe_float(price_value),
        "change": str(change_value) if change_value is not None else None,
        "unit": target["price_unit"],
        "raw_row": chosen_row,
    }


def fetch_akshare_commodity_snapshot(commodity_key: str) -> Dict[str, Any]:
    ak = _try_import_akshare()
    if ak is None:
        raise ValueError("AKShare is not installed in the runtime environment.")

    target = CRITICAL_MINERALS[commodity_key]
    attempts = []

    if hasattr(ak, "futures_zh_spot"):
        attempts.append(
            lambda: ak.futures_zh_spot(
                symbol=target["china_exchange_symbol"],
                market=target["market"],
                adjust="0",
            )
        )
        attempts.append(lambda: ak.futures_zh_spot(symbol=target["china_exchange_symbol"]))

    if hasattr(ak, "futures_zh_realtime"):
        attempts.append(lambda: ak.futures_zh_realtime(symbol=target["china_exchange_symbol"]))

    last_error = None
    for attempt in attempts:
        try:
            parsed = _parse_akshare_dataframe(attempt(), commodity_key)
            if parsed:
                return parsed
        except Exception as exc:
            last_error = exc

    raise ValueError(f"AKShare provider could not resolve {commodity_key}: {last_error}")


def _pick_tushare_contract(records: List[Dict[str, Any]], commodity_key: str) -> Optional[Dict[str, Any]]:
    target = CRITICAL_MINERALS[commodity_key]
    symbol = target.get("tushare_symbol")
    exchange = target.get("tushare_exchange")
    eligible = []
    for row in records:
        ts_code = str(row.get("ts_code", ""))
        if symbol and not ts_code.startswith(symbol):
            continue
        if exchange and not ts_code.endswith(f".{exchange}"):
            continue
        if row.get("delist_date") and str(row["delist_date"]) < datetime.utcnow().strftime("%Y%m%d"):
            continue
        eligible.append(row)
    if not eligible:
        eligible = records
    if not eligible:
        return None
    eligible.sort(key=lambda item: str(item.get("list_date") or ""), reverse=True)
    return eligible[0]


def fetch_tushare_commodity_data(commodity_key: str, history_days: int = 30) -> Dict[str, Any]:
    ts = _try_import_tushare()
    if ts is None:
        raise ValueError("Tushare is not installed in the runtime environment.")

    token = os.environ.get("TUSHARE_TOKEN")
    if not token:
        raise ValueError("TUSHARE_TOKEN is not configured.")

    target = CRITICAL_MINERALS[commodity_key]
    tushare_symbol = target.get("tushare_symbol")
    tushare_exchange = target.get("tushare_exchange")
    if not tushare_symbol or not tushare_exchange:
        raise ValueError(f"Tushare mapping is not configured for {commodity_key}.")

    pro = ts.pro_api(token)
    basic_df = pro.fut_basic(exchange=tushare_exchange, fut_type="1")
    basic_records = basic_df.to_dict(orient="records") if basic_df is not None else []
    selected_contract = _pick_tushare_contract(basic_records, commodity_key)
    if selected_contract is None:
        raise ValueError(f"Tushare could not find an active futures contract for {commodity_key}.")

    end_date = datetime.utcnow().strftime("%Y%m%d")
    start_date = (datetime.utcnow() - timedelta(days=history_days * 2)).strftime("%Y%m%d")
    daily_df = pro.fut_daily(
        ts_code=selected_contract["ts_code"],
        start_date=start_date,
        end_date=end_date,
    )
    daily_records = daily_df.to_dict(orient="records") if daily_df is not None else []
    if not daily_records:
        raise ValueError(f"Tushare returned no daily futures history for {selected_contract['ts_code']}.")

    daily_records.sort(key=lambda item: str(item.get("trade_date") or ""), reverse=True)
    latest = daily_records[0]
    previous = daily_records[1] if len(daily_records) > 1 else None
    latest_close = _safe_float(latest.get("close"))
    previous_close = _safe_float(previous.get("close")) if previous else None
    change_value = None
    change_pct = None
    if latest_close is not None and previous_close not in (None, 0):
        change_value = latest_close - previous_close
        change_pct = (change_value / previous_close) * 100

    trimmed_history = []
    for row in daily_records[:history_days]:
        trimmed_history.append(
            {
                "trade_date": row.get("trade_date"),
                "open": _safe_float(row.get("open")),
                "high": _safe_float(row.get("high")),
                "low": _safe_float(row.get("low")),
                "close": _safe_float(row.get("close")),
                "settle": _safe_float(row.get("settle")),
                "vol": _safe_float(row.get("vol")),
                "oi": _safe_float(row.get("oi")),
            }
        )

    return {
        "source": "Tushare",
        "provider": "tushare",
        "commodity": commodity_key,
        "contract": selected_contract.get("ts_code"),
        "contract_name": selected_contract.get("name"),
        "exchange": tushare_exchange,
        "date": latest.get("trade_date"),
        "price": latest_close,
        "change": f"{change_pct:.2f}%" if change_pct is not None else None,
        "change_value": change_value,
        "unit": target["price_unit"],
        "history": trimmed_history,
        "contract_metadata": {
            "multiplier": selected_contract.get("multiplier"),
            "trade_unit": selected_contract.get("trade_unit"),
            "per_unit": selected_contract.get("per_unit"),
            "quote_unit": selected_contract.get("quote_unit"),
        },
    }


def fetch_zyla_commodity_data(commodity_key: str, history_days: int = 30) -> Dict[str, Any]:
    api_key = os.environ.get("ZYLA_METALS_API_KEY")
    if not api_key:
        raise ValueError("ZYLA_METALS_API_KEY is not configured.")

    target = CRITICAL_MINERALS[commodity_key]
    zyla_symbol = target.get("zyla_symbol")
    if not zyla_symbol:
        raise ValueError(f"Zyla symbol is not configured for {commodity_key}.")

    headers = {"Authorization": f"Bearer {api_key}"}
    latest_url = f"{ZYLA_METALS_BASE_URL}/2684/latest+rates?base=USD&symbols={zyla_symbol}"
    latest_payload = _get_json_with_headers(latest_url, headers=headers)
    rate = _safe_float((latest_payload.get("rates") or {}).get(zyla_symbol))
    price = _invert_rate(rate)
    if price is None:
        raise ValueError(f"Zyla returned no usable latest rate for {commodity_key}.")

    end_date = datetime.utcnow().date()
    start_date = end_date - timedelta(days=min(history_days, 365) - 1)
    ts_url = (
        f"{ZYLA_METALS_BASE_URL}/2686/time-series?"
        f"start_date={start_date.isoformat()}&end_date={end_date.isoformat()}&base=USD&symbols={zyla_symbol}"
    )
    ts_payload = _get_json_with_headers(ts_url, headers=headers)
    rates = ts_payload.get("rates") or {}
    history: List[Dict[str, Any]] = []
    for date_key in sorted(rates.keys(), reverse=True):
        symbol_rate = _safe_float((rates.get(date_key) or {}).get(zyla_symbol))
        inverted = _invert_rate(symbol_rate)
        history.append(
            {
                "trade_date": date_key.replace("-", ""),
                "close": inverted,
            }
        )

    previous_close = history[1]["close"] if len(history) > 1 else None
    change_pct = None
    if previous_close not in (None, 0):
        change_pct = ((price - previous_close) / previous_close) * 100

    return {
        "source": "Zyla Labs",
        "provider": "zyla",
        "commodity": commodity_key,
        "contract": zyla_symbol,
        "date": end_date.strftime("%Y%m%d"),
        "price": round(price, 6),
        "change": f"{change_pct:.2f}%" if change_pct is not None else None,
        "unit": "USD/troy ounce equivalent" if zyla_symbol in {"XAU", "XAG"} else "USD/unit (provider-defined)",
        "history": history[:history_days],
    }


def fetch_commodity_context(commodity_key: str, history_days: int = 30) -> Dict[str, Any]:
    provider_results: List[Dict[str, Any]] = []

    try:
        zyla_result = fetch_zyla_commodity_data(commodity_key, history_days=history_days)
        provider_results.append(zyla_result)
    except Exception as exc:
        provider_results.append({"provider": "zyla", "error": str(exc)})

    try:
        akshare_result = fetch_akshare_commodity_snapshot(commodity_key)
        provider_results.append(akshare_result)
    except Exception as exc:
        provider_results.append({"provider": "akshare", "error": str(exc)})

    try:
        tushare_result = fetch_tushare_commodity_data(commodity_key, history_days=history_days)
        provider_results.append(tushare_result)
    except Exception as exc:
        provider_results.append({"provider": "tushare", "error": str(exc)})

    provider_priority = {"zyla": 0, "akshare": 1, "tushare": 2}
    successful = [item for item in provider_results if "error" not in item and _is_usable_price(item.get("price"))]
    successful.sort(key=lambda item: provider_priority.get(item.get("provider", ""), 99))
    primary = successful[0] if successful else None
    if primary is None:
        error_messages = [item["error"] for item in provider_results if "error" in item]
        return {
            "commodity": commodity_key,
            "providers": provider_results,
            "error": "; ".join(error_messages) if error_messages else "No provider returned usable data.",
        }

    merged = dict(primary)
    merged["providers"] = provider_results
    if primary.get("provider") in {"akshare", "zyla"}:
        tushare_ok = next((item for item in provider_results if item.get("provider") == "tushare" and "error" not in item), None)
        if tushare_ok and tushare_ok.get("history"):
            merged["history"] = tushare_ok["history"]
            merged["contract_metadata"] = tushare_ok.get("contract_metadata")
    return merged


def watch_tariff_changes(keywords: Optional[List[str]] = None, limit: int = 10) -> Dict[str, Any]:
    search_terms = keywords or [
        "critical minerals",
        "battery materials",
        "nickel",
        "cobalt",
        "manganese",
        "lithium",
        "tariff",
    ]

    query = " OR ".join(search_terms)
    url = (
        f"{FEDERAL_REGISTER_API}?conditions%5Bterm%5D={quote_plus(query)}"
        f"&order=newest&per_page={limit}"
    )
    payload = _get_json(url)
    results = payload.get("results", [])

    return {
        "source": "Federal Register",
        "query": query,
        "documents": [
            {
                "title": item.get("title"),
                "type": item.get("type"),
                "publication_date": item.get("publication_date"),
                "document_number": item.get("document_number"),
                "html_url": item.get("html_url"),
                "abstract": item.get("abstract"),
            }
            for item in results
        ],
    }


def watch_ustr_changes(keywords: Optional[List[str]] = None, limit: int = 10) -> Dict[str, Any]:
    html = _get_text(USTR_LATEST_PRESS_RELEASES)
    terms = [term.lower() for term in (keywords or ["tariff", "critical minerals", "lithium", "nickel", "cobalt", "manganese"])]

    link_pattern = re.compile(r'href="([^"]+)"[^>]*>([^<]+)</a>', re.IGNORECASE)
    matches = []
    for href, title in link_pattern.findall(html):
        normalized_title = re.sub(r"\s+", " ", title).strip()
        if not normalized_title:
            continue
        if any(term in normalized_title.lower() for term in terms):
            full_url = href if href.startswith("http") else f"https://ustr.gov{href}"
            matches.append({"title": normalized_title, "url": full_url})

    deduped: List[Dict[str, str]] = []
    seen = set()
    for match in matches:
        key = (match["title"], match["url"])
        if key not in seen:
            seen.add(key)
            deduped.append(match)

    return {"source": "USTR", "items": deduped[:limit]}


def analyze_ir_implications(
    commodity_snapshots: Dict[str, Any],
    tariff_watch: Dict[str, Any],
    company_profile: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    profile = company_profile or {}
    value_chain = (profile.get("value_chain_position") or "producer").lower()
    geography = profile.get("geography_focus") or "global"
    implications: List[str] = []
    talking_points: List[str] = []

    for commodity_key, snapshot in commodity_snapshots.items():
        if "error" in snapshot:
            continue
        display_name = CRITICAL_MINERALS[commodity_key]["display_name"]
        price = snapshot.get("price")
        change = snapshot.get("change")
        provider = snapshot.get("provider", snapshot.get("source", "unknown"))
        if price is None:
            continue

        if value_chain in {"producer", "miner", "upstream"}:
            implications.append(
                f"{display_name} pricing at {price:.2f} {snapshot.get('unit')} from {provider} is a direct realized-price input for upstream revenue framing."
            )
        else:
            implications.append(
                f"{display_name} pricing at {price:.2f} {snapshot.get('unit')} from {provider} is a feedstock-cost input for downstream margin framing."
            )

        if change:
            talking_points.append(
                f"{display_name} latest move ({change}) should be translated into investor language around margin leverage, contract resets, and procurement risk."
            )
        if snapshot.get("history"):
            talking_points.append(
                f"{display_name} now includes futures history, which can support trend charts, volatility framing, and contract-roll commentary."
            )

    tariff_documents = tariff_watch.get("federal_register", {}).get("documents", [])
    ustr_items = tariff_watch.get("ustr", {}).get("items", [])
    if tariff_documents or ustr_items:
        implications.append(
            f"Tariff and trade-policy monitoring is active for {geography}; new notices can affect import costs, export competitiveness, and processing economics."
        )
        talking_points.append(
            "Management should explain whether trade-policy changes affect ore, concentrate, refined material, cathode precursor, or equipment exposure."
        )

    if not implications:
        implications.append("No commodity or tariff implications were available from the configured sources.")

    return {
        "company_profile": profile,
        "implications": implications,
        "management_talking_points": talking_points,
    }


def generate_critical_minerals_context(payload: Dict[str, Any]) -> Dict[str, Any]:
    requested_commodities = payload.get("commodities") or list(CRITICAL_MINERALS.keys())
    company_profile = payload.get("company_profile", {})
    history_days = int(payload.get("history_days", 30))
    commodity_snapshots: Dict[str, Any] = {}
    warnings: List[str] = []

    for commodity_key in requested_commodities:
        if commodity_key not in CRITICAL_MINERALS:
            warnings.append(f"Unsupported commodity: {commodity_key}")
            continue
        try:
            commodity_snapshots[commodity_key] = fetch_commodity_context(commodity_key, history_days=history_days)
        except Exception as exc:
            commodity_snapshots[commodity_key] = {"error": str(exc)}
            warnings.append(f"{commodity_key}: {exc}")

    tariff_watch = {}
    try:
        tariff_watch["federal_register"] = watch_tariff_changes()
    except Exception as exc:
        warnings.append(f"Federal Register tariff watch failed: {exc}")
        tariff_watch["federal_register"] = {"documents": []}

    try:
        tariff_watch["ustr"] = watch_ustr_changes()
    except Exception as exc:
        warnings.append(f"USTR tariff watch failed: {exc}")
        tariff_watch["ustr"] = {"items": []}

    ir_analysis = analyze_ir_implications(
        commodity_snapshots=commodity_snapshots,
        tariff_watch=tariff_watch,
        company_profile=company_profile,
    )

    return {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "commodity_agents": commodity_snapshots,
        "tariff_watch": tariff_watch,
        "ir_analysis": ir_analysis,
        "warnings": warnings,
    }
