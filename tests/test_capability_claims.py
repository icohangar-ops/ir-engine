"""Focused capability-claim tests for the ir-engine evidence matrix.

Each test executes a capability the README/docs state, hermetically: the
modules exercised here are import-free of network and optional dependencies
(investor_relations_engine and veris_simulation_engine are pure stdlib;
airbyte_providers guards its SDK import). Sample payloads are the committed
fixtures served by the GET sample endpoints.
"""

import asyncio
import inspect
import json
import os
import sys

import pytest

PROJECT_ROOT = os.path.join(os.path.dirname(__file__), "..")
sys.path.insert(0, PROJECT_ROOT)

from airbyte_providers import (  # noqa: E402
    fetch_hybrid_market_context,
    fetch_market_context_via_airbyte,
    get_mcp_config,
    is_airbyte_available,
)
from investor_relations_engine import (  # noqa: E402
    derive_macro_adjustments,
    generate_investor_relations_package,
    validate_payload,
)
from veris_simulation_engine import (  # noqa: E402
    build_veris_briefing,
    build_veris_memory_packet,
    run_veris_simulation,
)


def _load_sample(name):
    path = os.path.join(PROJECT_ROOT, name)
    with open(path, encoding="utf-8") as handle:
        return json.load(handle)


def test_generate_investor_relations_package_from_sample():
    """POST /v1/investor-relations/generate produces the full IR package."""
    payload = _load_sample("sample_investor_relations_request.json")
    package = generate_investor_relations_package(payload)

    for section in (
        "validation_issues",
        "investment_evaluation",
        "risk_assessment",
        "financial_story",
        "quarterly_update",
        "pitch_deck",
        "board_materials",
    ):
        assert section in package, f"missing IR package section: {section}"

    assert package["validation_issues"] == []
    evaluation = package["investment_evaluation"]
    assert 0 <= evaluation["overall_score"] <= 100
    assert evaluation["recommendation"] in {
        "Strongly Recommended",
        "Recommended",
        "Conditional",
        "Not Recommended",
    }
    assert len(package["pitch_deck"]["slides"]) == 5
    assert (
        package["board_materials"]["decisions_required"] == payload["board_requests"]
    )
    assert len(package["risk_assessment"]["risk_register"]) == 3


def test_validate_payload_flags_missing_required_fields():
    """Payload validation reports the documented required fields."""
    fields = {issue["field"] for issue in validate_payload({})}
    assert {
        "company.name",
        "financials.current_revenue",
        "financials.prior_revenue",
        "financials.cash_balance",
        "metrics.growth_score",
        "metrics.efficiency_score",
        "metrics.market_score",
    }.issubset(fields)


def test_derive_macro_adjustments_applies_market_regime():
    """Macro regime adjustments derive from FRED/Alpha Vantage context."""
    payload = {
        "market_context": {
            "fred": {
                "series": {
                    "federal_funds_rate": {"latest_value": 5.3},
                    "ten_year_treasury": {"latest_value": 4.4},
                    "unemployment_rate": {"latest_value": 3.7},
                    "inflation_cpi": {"latest_value": 320.0},
                }
            },
            "alpha_vantage": {
                "benchmark": {"quote": {"10. change percent": "1.20%"}},
                "company": {"quote": {"10. change percent": "0.20%"}},
            },
        }
    }
    adjustments = derive_macro_adjustments(payload)
    assert adjustments["regime"] == "headwind"
    assert set(adjustments["adjustments"]) == {
        "strategic_alignment",
        "financial_return",
        "execution_capability",
        "risk_profile",
        "stakeholder_impact",
    }
    assert adjustments["adjustments"]["financial_return"] == -0.55
    assert adjustments["reasons"]


def test_veris_simulation_runs_four_scenarios():
    """POST /v1/veris/simulate runs base, bull, bear, and stress scenarios."""
    simulation = run_veris_simulation(_load_sample("sample_veris_simulation_request.json"))
    scenario_names = [scenario["scenario"] for scenario in simulation["scenarios"]]
    assert scenario_names == ["base", "bull", "bear", "stress"]
    assert simulation["summary"]["scenario_count"] == 4
    for scenario in simulation["scenarios"]:
        assert "revenue_delta_pct" in scenario
        assert "adjusted_runway_months" in scenario
        assert scenario["valuation_signal"]


def test_veris_briefing_builds_prompt_and_memory_facts():
    """POST /v1/veris/briefing builds a Veris-ready context briefing."""
    briefing = build_veris_briefing(_load_sample("sample_veris_simulation_request.json"))
    assert "Atlas Critical Minerals" in briefing["prompt"]
    assert len(briefing["memory_facts"]) >= 4
    assert len(briefing["scenario_summary_lines"]) == 4


def test_veris_memory_packet_renders_markdown_artifact():
    """POST /v1/veris/export returns a JSON packet with a Markdown artifact."""
    packet = build_veris_memory_packet(_load_sample("sample_veris_simulation_request.json"))
    markdown = packet["memory_markdown"]
    assert markdown.startswith("# Veris Memory Packet: Atlas Critical Minerals")
    assert "## Downside Control Case" in markdown
    assert "- Scenario: stress" in markdown
    assert packet["control_case"]["scenario"] == "stress"
    # The packet is the JSON artifact: fully serializable.
    json.dumps(packet, allow_nan=False)


def test_airbyte_graceful_fallback_without_sdk():
    """Without the SDK or credentials, hybrid fetch falls back to direct clients."""
    with pytest.MonkeyPatch.context() as patcher:
        patcher.delenv("AIRBYTE_CLIENT_ID", raising=False)
        patcher.delenv("AIRBYTE_CLIENT_SECRET", raising=False)
        assert is_airbyte_available() is False
        result = asyncio.run(
            fetch_hybrid_market_context(company_symbol=None, benchmark_symbol="SPY")
        )
    # Direct-client result with per-provider warnings; no Airbyte metadata.
    assert "data_source" not in result
    assert "airbyte" not in result
    assert any(warning.startswith("FRED unavailable") for warning in result["warnings"])
    assert any("Alpha Vantage unavailable" in warning for warning in result["warnings"])


def test_airbyte_hybrid_is_async_and_mcp_configured():
    """The Airbyte layer is async and exposes the documented MCP config."""
    assert inspect.iscoroutinefunction(fetch_hybrid_market_context)
    assert inspect.iscoroutinefunction(fetch_market_context_via_airbyte)
    config = get_mcp_config()
    assert config["mcp_server_url"].startswith("https://")
    assert {"claude_desktop", "claude_code", "cursor", "vscode"}.issubset(
        config["setup_instructions"]
    )
