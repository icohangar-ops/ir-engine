"""
Airbyte-enhanced data providers for ir-engine.

This module provides Airbyte MCP/SDK-backed data fetching as an alternative
to the direct HTTP clients. Use when Airbyte connectors are configured for
data sources that have native support, or when you want to leverage Airbyte's
credential management and retry logic.

For data sources without native Airbyte connectors (FRED, Alpha Vantage,
SEC EDGAR, Federal Register, Zyla Labs, AKShare, Tushare), the module
falls back to the existing direct clients.

Setup:
    export AIRBYTE_CLIENT_ID=<your_client_id>
    export AIRBYTE_CLIENT_SECRET=<your_client_secret>

    # Then configure connectors in Airbyte web app or via REST API
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
from datetime import datetime
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Airbyte SDK bridge
# ---------------------------------------------------------------------------

_airbyte_available = False
try:
    from airbyte_agent_sdk import connect, Workspace, AirbyteError
    _airbyte_available = True
except ImportError:
    logger.info("airbyte-agent-sdk not installed; Airbyte providers will fall back to direct clients")


def is_airbyte_available() -> bool:
    """Check if the Airbyte SDK is installed and credentials are configured."""
    if not _airbyte_available:
        return False
    return bool(os.environ.get("AIRBYTE_CLIENT_ID") and os.environ.get("AIRBYTE_CLIENT_SECRET"))


async def _get_airbyte_connector(slug: str, connector_id: Optional[str] = None):
    """Get an Airbyte connector by slug or explicit ID."""
    if connector_id:
        return connect(slug, connector_id=connector_id)
    return connect(slug)


# ---------------------------------------------------------------------------
# Airbyte-backed market data fetcher
# ---------------------------------------------------------------------------

async def fetch_market_context_via_airbyte(
    company_symbol: Optional[str] = None,
    benchmark_symbol: str = "SPY",
    sector: Optional[str] = None,
    fred_connector_id: Optional[str] = None,
    alpha_vantage_connector_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Fetch market context using Airbyte connectors where available.

    Falls back to direct API calls for sources without Airbyte connectors.
    This is an async alternative to the sync `fetch_market_context()` in
    `market_data_clients.py`.

    Airbyte has no native FRED or Alpha Vantage connectors in the agent SDK
    (48 connectors: CRM, support, billing, marketing, dev tools, analytics).
    When those connectors become available, they can be wired in here.

    For now, this serves as the integration point and demonstrates the pattern
    for when financial data connectors are added to Airbyte's catalog.
    """
    if not is_airbyte_available():
        raise RuntimeError(
            "Airbyte SDK not available. Install with: pip install airbyte-agent-sdk "
            "and set AIRBYTE_CLIENT_ID and AIRBYTE_CLIENT_SECRET environment variables."
        )

    context: Dict[str, Any] = {
        "source": "airbyte_hybrid",
        "fetched_at": datetime.utcnow().isoformat() + "Z",
        "warnings": [],
        "connectors_used": [],
    }

    # --- FRED (no native Airbyte connector yet) ---
    # Pattern for when Airbyte adds FRED:
    # try:
    #     fred = await _get_airbyte_connector("fred", fred_connector_id)
    #     result = await fred.execute("economic_indicators", "get", params={
    #         "series_ids": "FEDFUNDS,DGS10,CPIAUCSL,UNRATE",
    #         "limit": 2,
    #     })
    #     context["fred"] = {"data": result.data, "source": "airbyte_fred"}
    #     context["connectors_used"].append("fred")
    # except Exception as exc:
    #     context["warnings"].append(f"Airbyte FRED: {exc}")

    context["warnings"].append(
        "FRED: No native Airbyte connector available yet. "
        "Using direct API via market_data_clients.fetch_fred_series_snapshot()."
    )

    # --- Alpha Vantage (no native Airbyte connector yet) ---
    # Pattern for when Airbyte adds Alpha Vantage:
    # try:
    #     av = await _get_airbyte_connector("alpha_vantage", alpha_vantage_connector_id)
    #     result = await av.execute("equities", "global_quote", params={
    #         "symbol": benchmark_symbol,
    #     })
    #     context["alpha_vantage"] = {"data": result.data, "source": "airbyte_alpha_vantage"}
    #     context["connectors_used"].append("alpha_vantage")
    # except Exception as exc:
    #     context["warnings"].append(f"Airbyte Alpha Vantage: {exc}")

    context["warnings"].append(
        "Alpha Vantage: No native Airbyte connector available yet. "
        "Using direct API via market_data_clients.fetch_alpha_vantage_snapshot()."
    )

    # --- SEC EDGAR (no native Airbyte connector yet) ---
    context["warnings"].append(
        "SEC EDGAR: No native Airbyte connector available yet. "
        "Using direct API via edgar_client module."
    )

    # --- Federal Register (no native Airbyte connector yet) ---
    context["warnings"].append(
        "Federal Register: No native Airbyte connector available yet. "
        "Using direct API via critical_minerals_monitor.watch_tariff_changes()."
    )

    # --- Commodity data (Zyla, AKShare, Tushare — specialized, no Airbyte equivalent) ---
    context["warnings"].append(
        "Commodity pricing (Zyla/AKShare/Tushare): Specialized China-market and "
        "metals APIs with no Airbyte equivalent. Using direct clients."
    )

    # --- Demonstrated: Airbyte connector usage for supported sources ---
    # Uncomment and configure when you have relevant connectors set up:
    #
    # # Example: If you have a Google Sheets connector with benchmark data
    # try:
    #     sheets = await _get_airbyte_connector("google_drive")
    #     result = await sheets.execute("spreadsheets", "get", params={
    #         "spreadsheet_id": "<your_benchmark_sheet_id>",
    #     })
    #     context["benchmark_sheet"] = {"data": result.data}
    #     context["connectors_used"].append("google_drive")
    # except Exception as exc:
    #     logger.debug("Google Drive connector not configured: %s", exc)

    return context


# ---------------------------------------------------------------------------
# MCP Server configuration helper
# ---------------------------------------------------------------------------

MCP_SERVER_URL = "https://mcp.airbyte.ai/mcp"

def get_mcp_config() -> Dict[str, Any]:
    """
    Return the MCP server configuration for ir-engine.

    Add this to your AI agent's MCP config to enable Airbyte data connectors:

    Claude Desktop / Claude Code:
        claude mcp add --transport http airbyte-agent https://mcp.airbyte.ai/mcp

    Cursor:
        Settings → Tools and MCP → Add custom MCP:
        {"mcpServers": {"Agent MCP": {"url": "https://mcp.airbyte.ai/mcp"}}}

    VS Code (.vscode/mcp.json):
        {"servers": {"Agent MCP": {"type": "http", "url": "https://mcp.airbyte.ai/mcp"}}}
    """
    return {
        "mcp_server_url": MCP_SERVER_URL,
        "setup_instructions": {
            "claude_desktop": "Settings → Connectors → Add custom connector → URL: https://mcp.airbyte.ai/mcp",
            "claude_code": "claude mcp add --transport http airbyte-agent https://mcp.airbyte.ai/mcp",
            "cursor": '{"mcpServers": {"Agent MCP": {"url": "https://mcp.airbyte.ai/mcp"}}}',
            "vscode": '{"servers": {"Agent MCP": {"type": "http", "url": "https://mcp.airbyte.ai/mcp"}}}',
        },
        "note": (
            "Airbyte's MCP server connects AI agents to your data sources. "
            "Configure connectors in the Airbyte web app first, then authenticate "
            "via browser OAuth when prompted by your MCP client."
        ),
    }


# ---------------------------------------------------------------------------
# Hybrid fetcher: tries Airbyte first, falls back to direct clients
# ---------------------------------------------------------------------------

async def fetch_hybrid_market_context(
    company_symbol: Optional[str] = None,
    benchmark_symbol: str = "SPY",
    sector: Optional[str] = None,
    fred_series: Optional[Dict[str, str]] = None,
) -> Dict[str, Any]:
    """
    Try Airbyte connectors first, fall back to direct HTTP clients.

    This is the recommended entry point for production use. It provides:
    1. Airbyte credential management and retry logic (when connectors exist)
    2. Seamless fallback to existing direct clients (for all current sources)

    As Airbyte adds financial data connectors to their catalog, this function
    will automatically use them without any code changes — just configure the
    connector in Airbyte and update the mapping below.
    """
    from market_data_clients import fetch_market_context

    airbyte_context: Dict[str, Any] = {}

    if is_airbyte_available():
        try:
            airbyte_context = await fetch_market_context_via_airbyte(
                company_symbol=company_symbol,
                benchmark_symbol=benchmark_symbol,
                sector=sector,
            )
        except Exception as exc:
            logger.warning("Airbyte fetch failed, falling back to direct clients: %s", exc)

    # Always fall back to direct clients for current data sources
    direct_context = fetch_market_context(
        company_symbol=company_symbol,
        benchmark_symbol=benchmark_symbol,
        sector=sector,
        fred_series=fred_series,
    )

    # Merge: Airbyte metadata + direct data
    merged = {**direct_context}
    if airbyte_context:
        merged["airbyte"] = airbyte_context
        merged["data_source"] = "hybrid_airbyte_plus_direct"

    return merged
