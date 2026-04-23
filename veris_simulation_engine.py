from __future__ import annotations

from copy import deepcopy
from datetime import datetime
from typing import Any, Dict, List


DEFAULT_SCENARIOS = {
    "base": {
        "commodity_price_shock_pct": 0.0,
        "tariff_severity_shift": 0.0,
        "macro_pressure_shift": 0.0,
        "financing_pressure_shift": 0.0,
    },
    "bull": {
        "commodity_price_shock_pct": 0.12,
        "tariff_severity_shift": 0.1,
        "macro_pressure_shift": -0.1,
        "financing_pressure_shift": -0.05,
    },
    "bear": {
        "commodity_price_shock_pct": -0.12,
        "tariff_severity_shift": 0.15,
        "macro_pressure_shift": 0.15,
        "financing_pressure_shift": 0.1,
    },
    "stress": {
        "commodity_price_shock_pct": -0.25,
        "tariff_severity_shift": 0.3,
        "macro_pressure_shift": 0.25,
        "financing_pressure_shift": 0.2,
    },
}


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None:
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def _money(value: float) -> str:
    sign = "-" if value < 0 else ""
    value = abs(value)
    if value >= 1_000_000_000:
        return f"{sign}${value / 1_000_000_000:.2f}B"
    if value >= 1_000_000:
        return f"{sign}${value / 1_000_000:.2f}M"
    if value >= 1_000:
        return f"{sign}${value / 1_000:.1f}K"
    return f"{sign}${value:.0f}"


def _pct(value: float) -> str:
    return f"{value * 100:.1f}%"


def build_veris_input_schema(payload: Dict[str, Any]) -> Dict[str, Any]:
    company = payload.get("company_profile", {})
    financials = payload.get("financials", {})
    commodity_context = payload.get("commodity_context", {})
    tariff_watch = commodity_context.get("tariff_watch", {})
    commodity_agents = commodity_context.get("commodity_agents", {})

    supported_commodities: List[Dict[str, Any]] = []
    for commodity_name, item in commodity_agents.items():
        if "error" in item:
            continue
        supported_commodities.append(
            {
                "commodity": commodity_name,
                "price": item.get("price"),
                "unit": item.get("unit"),
                "provider": item.get("provider"),
                "contract": item.get("contract"),
            }
        )

    return {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "company_profile": {
            "name": company.get("name", "Unknown Company"),
            "value_chain_position": company.get("value_chain_position", "producer"),
            "geography_focus": company.get("geography_focus", "global"),
        },
        "financial_base": {
            "revenue": _safe_float(financials.get("revenue")),
            "ebitda_margin": _safe_float(financials.get("ebitda_margin")),
            "cash_balance": _safe_float(financials.get("cash_balance")),
            "runway_months": _safe_float(financials.get("runway_months")),
        },
        "commodity_exposure": supported_commodities,
        "tariff_signal_count": len(tariff_watch.get("federal_register", {}).get("documents", []))
        + len(tariff_watch.get("ustr", {}).get("items", [])),
    }


def _estimate_scenario_outcome(veris_input: Dict[str, Any], scenario_name: str, assumptions: Dict[str, float]) -> Dict[str, Any]:
    company_profile = veris_input["company_profile"]
    financial_base = veris_input["financial_base"]
    value_chain_position = company_profile["value_chain_position"].lower()

    revenue = _safe_float(financial_base.get("revenue"))
    ebitda_margin = _safe_float(financial_base.get("ebitda_margin"))
    cash_balance = _safe_float(financial_base.get("cash_balance"))
    runway_months = _safe_float(financial_base.get("runway_months"))

    commodity_shock = assumptions["commodity_price_shock_pct"]
    tariff_shift = assumptions["tariff_severity_shift"]
    macro_shift = assumptions["macro_pressure_shift"]
    financing_shift = assumptions["financing_pressure_shift"]

    if value_chain_position in {"producer", "miner", "upstream"}:
        revenue_delta_pct = commodity_shock * 0.8 - tariff_shift * 0.15 - macro_shift * 0.25
        margin_delta = commodity_shock * 0.25 - tariff_shift * 0.06 - macro_shift * 0.08
    else:
        revenue_delta_pct = -commodity_shock * 0.25 - tariff_shift * 0.1 - macro_shift * 0.2
        margin_delta = -commodity_shock * 0.2 - tariff_shift * 0.08 - macro_shift * 0.08

    adjusted_revenue = revenue * (1 + revenue_delta_pct)
    adjusted_ebitda_margin = ebitda_margin + margin_delta
    cash_flow_effect = revenue * (adjusted_ebitda_margin - ebitda_margin)
    adjusted_cash_balance = cash_balance + cash_flow_effect
    adjusted_runway = runway_months * (1 - financing_shift - max(0.0, -margin_delta))

    valuation_signal = "stable"
    if revenue_delta_pct >= 0.08 and margin_delta >= 0:
        valuation_signal = "multiple expansion bias"
    elif revenue_delta_pct <= -0.08 or margin_delta <= -0.05:
        valuation_signal = "multiple compression risk"

    narrative_shift = []
    if commodity_shock > 0 and value_chain_position in {"producer", "miner", "upstream"}:
        narrative_shift.append("Stronger commodity pricing supports realized-price upside.")
    if commodity_shock < 0 and value_chain_position in {"producer", "miner", "upstream"}:
        narrative_shift.append("Weaker commodity pricing pressures near-term revenue realization.")
    if tariff_shift > 0.1:
        narrative_shift.append("Trade-policy risk becomes a more prominent investor concern.")
    if macro_shift > 0.1:
        narrative_shift.append("Macro headwinds require tighter capital-allocation discipline.")
    if financing_shift > 0.1:
        narrative_shift.append("Funding conditions weaken, increasing scrutiny on runway and spend pace.")
    if not narrative_shift:
        narrative_shift.append("Scenario remains broadly consistent with the current investment narrative.")

    board_talking_points = [
        f"Scenario: {scenario_name}",
        f"Revenue sensitivity: {_pct(revenue_delta_pct)}",
        f"EBITDA margin change: {_pct(margin_delta)}",
        f"Valuation read-through: {valuation_signal}",
    ]

    investor_qa = [
        "How much of the revenue base is directly exposed to benchmark commodity pricing?",
        "Which tariff pathways most affect concentrate, refined product, or equipment costs?",
        "What spending levers preserve runway if the downside scenario persists?",
    ]

    return {
        "scenario": scenario_name,
        "assumptions": assumptions,
        "revenue_delta_pct": round(revenue_delta_pct, 4),
        "adjusted_revenue": round(adjusted_revenue, 2),
        "adjusted_ebitda_margin": round(adjusted_ebitda_margin, 4),
        "cash_flow_effect": round(cash_flow_effect, 2),
        "adjusted_cash_balance": round(adjusted_cash_balance, 2),
        "adjusted_runway_months": round(adjusted_runway, 2),
        "valuation_signal": valuation_signal,
        "narrative_shift": narrative_shift,
        "board_talking_points": board_talking_points,
        "investor_qa": investor_qa,
    }


def run_veris_simulation(payload: Dict[str, Any]) -> Dict[str, Any]:
    veris_input = build_veris_input_schema(payload)
    scenario_overrides = payload.get("scenario_overrides", {})

    scenarios: List[Dict[str, Any]] = []
    for name, default_assumptions in DEFAULT_SCENARIOS.items():
        assumptions = deepcopy(default_assumptions)
        assumptions.update(scenario_overrides.get(name, {}))
        scenarios.append(_estimate_scenario_outcome(veris_input, name, assumptions))

    return {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "veris_input": veris_input,
        "scenarios": scenarios,
        "summary": {
            "company": veris_input["company_profile"]["name"],
            "scenario_count": len(scenarios),
            "base_revenue": _money(veris_input["financial_base"]["revenue"]),
            "base_cash_balance": _money(veris_input["financial_base"]["cash_balance"]),
        },
    }


def build_veris_briefing(payload: Dict[str, Any]) -> Dict[str, Any]:
    simulation = run_veris_simulation(payload)
    company = simulation["veris_input"]["company_profile"]["name"]
    scenarios = simulation["scenarios"]

    scenario_lines: List[str] = []
    for scenario in scenarios:
        scenario_lines.append(
            f"{scenario['scenario'].upper()}: revenue {_pct(scenario['revenue_delta_pct'])}, "
            f"EBITDA margin { _pct(scenario['adjusted_ebitda_margin']) }, "
            f"valuation {scenario['valuation_signal']}."
        )

    memory_facts = [
        f"Company: {company}",
        f"Value chain: {simulation['veris_input']['company_profile']['value_chain_position']}",
        f"Geography: {simulation['veris_input']['company_profile']['geography_focus']}",
        f"Commodity exposures tracked: {len(simulation['veris_input']['commodity_exposure'])}",
        f"Tariff signal count: {simulation['veris_input']['tariff_signal_count']}",
    ]

    prompt = (
        f"You are preparing investor-relations and board communications for {company}. "
        "Use the scenario outputs below as persistent strategic context. "
        "Emphasize commodity-price sensitivity, tariff risk, financing resilience, "
        "and management talking points. Treat the stress scenario as the downside control case."
    )

    return {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "prompt": prompt,
        "memory_facts": memory_facts,
        "scenario_summary_lines": scenario_lines,
        "simulation": simulation,
    }


def build_veris_memory_packet(payload: Dict[str, Any]) -> Dict[str, Any]:
    briefing = build_veris_briefing(payload)
    simulation = briefing["simulation"]
    scenarios = simulation["scenarios"]
    company_profile = simulation["veris_input"]["company_profile"]
    financial_base = simulation["veris_input"]["financial_base"]

    packet = {
        "generated_at": briefing["generated_at"],
        "provider": "veris_local_context_export",
        "entity_type": "investor_relations_simulation",
        "company": company_profile["name"],
        "context_window": {
            "value_chain_position": company_profile["value_chain_position"],
            "geography_focus": company_profile["geography_focus"],
            "tracked_commodity_count": len(simulation["veris_input"]["commodity_exposure"]),
            "tariff_signal_count": simulation["veris_input"]["tariff_signal_count"],
        },
        "financial_base": financial_base,
        "memory_facts": briefing["memory_facts"],
        "scenario_summary_lines": briefing["scenario_summary_lines"],
        "recommended_prompt": briefing["prompt"],
        "control_case": next((scenario for scenario in scenarios if scenario["scenario"] == "stress"), scenarios[-1]),
        "scenarios": scenarios,
    }
    packet["memory_markdown"] = render_veris_memory_markdown(packet)
    return packet


def render_veris_memory_markdown(packet: Dict[str, Any]) -> str:
    context_window = packet["context_window"]
    financial_base = packet["financial_base"]
    control_case = packet["control_case"]

    lines = [
        f"# Veris Memory Packet: {packet['company']}",
        "",
        f"- Generated at: {packet['generated_at']}",
        f"- Entity type: {packet['entity_type']}",
        f"- Value chain position: {context_window['value_chain_position']}",
        f"- Geography focus: {context_window['geography_focus']}",
        f"- Tracked commodity count: {context_window['tracked_commodity_count']}",
        f"- Tariff signal count: {context_window['tariff_signal_count']}",
        "",
        "## Base Financial Profile",
        f"- Revenue: {_money(_safe_float(financial_base.get('revenue')))}",
        f"- EBITDA margin: {_pct(_safe_float(financial_base.get('ebitda_margin')))}",
        f"- Cash balance: {_money(_safe_float(financial_base.get('cash_balance')))}",
        f"- Runway months: {_safe_float(financial_base.get('runway_months')):.1f}",
        "",
        "## Persistent Memory Facts",
    ]

    lines.extend(f"- {fact}" for fact in packet["memory_facts"])
    lines.extend(
        [
            "",
            "## Scenario Summary",
        ]
    )
    lines.extend(f"- {line}" for line in packet["scenario_summary_lines"])
    lines.extend(
        [
            "",
            "## Downside Control Case",
            f"- Scenario: {control_case['scenario']}",
            f"- Revenue delta: {_pct(control_case['revenue_delta_pct'])}",
            f"- Adjusted revenue: {_money(control_case['adjusted_revenue'])}",
            f"- Adjusted EBITDA margin: {_pct(control_case['adjusted_ebitda_margin'])}",
            f"- Adjusted cash balance: {_money(control_case['adjusted_cash_balance'])}",
            f"- Adjusted runway months: {control_case['adjusted_runway_months']:.1f}",
            f"- Valuation signal: {control_case['valuation_signal']}",
            "",
            "## Veris Prompt",
            packet["recommended_prompt"],
        ]
    )
    return "\n".join(lines)
