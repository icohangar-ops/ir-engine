from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Tuple


INVESTMENT_WEIGHTS = {
    "strategic_alignment": 25,
    "financial_return": 30,
    "execution_capability": 20,
    "risk_profile": 15,
    "stakeholder_impact": 10,
}

RISK_LEVELS = (
    (20, "Critical"),
    (12, "High"),
    (6, "Medium"),
    (1, "Low"),
)


@dataclass
class ValidationIssue:
    field: str
    message: str


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None:
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def _bounded_score(value: Any) -> float:
    return max(1.0, min(5.0, _safe_float(value, 3.0)))


def _pct(value: float) -> str:
    return f"{value * 100:.1f}%"


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


def _risk_level(score: int) -> str:
    for threshold, label in RISK_LEVELS:
        if score >= threshold:
            return label
    return "Low"


def _recommendation(total_score: float) -> str:
    if total_score >= 90:
        return "Strongly Recommended"
    if total_score >= 75:
        return "Recommended"
    if total_score >= 60:
        return "Conditional"
    return "Not Recommended"


def _clamp(value: float, lower: float, upper: float) -> float:
    return max(lower, min(upper, value))


def validate_payload(payload: Dict[str, Any]) -> List[Dict[str, str]]:
    company = payload.get("company", {})
    financials = payload.get("financials", {})
    metrics = payload.get("metrics", {})

    issues: List[ValidationIssue] = []

    if not company.get("name"):
        issues.append(ValidationIssue("company.name", "Company name is required."))

    required_financials = ("current_revenue", "prior_revenue", "cash_balance")
    for field in required_financials:
        if field not in financials:
            issues.append(
                ValidationIssue(f"financials.{field}", f"Missing required financial field '{field}'.")
            )

    required_metrics = ("growth_score", "efficiency_score", "market_score")
    for field in required_metrics:
        if field not in metrics:
            issues.append(
                ValidationIssue(f"metrics.{field}", f"Missing required metric '{field}'.")
            )

    return [{"field": issue.field, "message": issue.message} for issue in issues]


def derive_macro_adjustments(payload: Dict[str, Any]) -> Dict[str, Any]:
    market_context = payload.get("market_context", {})
    fred_series = market_context.get("fred", {}).get("series", {})
    alpha_context = market_context.get("alpha_vantage", {})

    fed_funds = _safe_float(fred_series.get("federal_funds_rate", {}).get("latest_value"))
    ten_year = _safe_float(fred_series.get("ten_year_treasury", {}).get("latest_value"))
    unemployment = _safe_float(fred_series.get("unemployment_rate", {}).get("latest_value"))
    cpi_level = _safe_float(fred_series.get("inflation_cpi", {}).get("latest_value"))

    benchmark_change_raw = alpha_context.get("benchmark", {}).get("quote", {}).get("10. change percent", "")
    company_change_raw = alpha_context.get("company", {}).get("quote", {}).get("10. change percent", "")
    benchmark_change = _safe_float(str(benchmark_change_raw).replace("%", ""))
    company_change = _safe_float(str(company_change_raw).replace("%", ""))

    adjustments = {
        "strategic_alignment": 0.0,
        "financial_return": 0.0,
        "execution_capability": 0.0,
        "risk_profile": 0.0,
        "stakeholder_impact": 0.0,
    }
    reasons: List[str] = []

    if fed_funds is not None and fed_funds >= 4.5:
        adjustments["financial_return"] -= 0.35
        adjustments["risk_profile"] -= 0.25
        reasons.append("Higher policy rates raise financing pressure and increase the hurdle rate.")
    elif fed_funds is not None and fed_funds <= 2.0:
        adjustments["financial_return"] += 0.2
        reasons.append("Lower policy rates improve financing conditions for growth investments.")

    if ten_year is not None and ten_year >= 4.25:
        adjustments["financial_return"] -= 0.2
        reasons.append("Higher long-end yields reduce valuation support and increase capital costs.")

    if unemployment is not None and unemployment <= 4.0:
        adjustments["strategic_alignment"] += 0.15
        reasons.append("A still-healthy labor market supports demand resilience.")
    elif unemployment is not None and unemployment >= 5.0:
        adjustments["strategic_alignment"] -= 0.15
        adjustments["risk_profile"] -= 0.15
        reasons.append("A weaker labor market raises demand risk and execution uncertainty.")

    if cpi_level is not None and cpi_level > 0:
        # Inference: using CPI level change requires separate inflation rate series, so only apply mild caution.
        adjustments["execution_capability"] -= 0.05
        reasons.append("Persistent inflation pressure can keep labor and input costs elevated.")

    if benchmark_change is not None:
        if benchmark_change >= 1.0:
            adjustments["strategic_alignment"] += 0.15
            reasons.append("Positive benchmark momentum supports sector sentiment and fundraising receptivity.")
        elif benchmark_change <= -1.0:
            adjustments["risk_profile"] -= 0.2
            reasons.append("Negative benchmark momentum signals a more fragile market backdrop.")

    if company_change is not None and benchmark_change is not None:
        relative_move = company_change - benchmark_change
        if relative_move >= 1.5:
            adjustments["stakeholder_impact"] += 0.2
            adjustments["strategic_alignment"] += 0.1
            reasons.append("Company market performance is outpacing its benchmark, strengthening investor credibility.")
        elif relative_move <= -1.5:
            adjustments["stakeholder_impact"] -= 0.2
            reasons.append("Company market performance is lagging its benchmark, weakening investor confidence.")

    net_adjustment = round(sum(adjustments.values()), 2)
    regime = "neutral"
    if net_adjustment >= 0.25:
        regime = "supportive"
    elif net_adjustment <= -0.25:
        regime = "headwind"

    return {
        "regime": regime,
        "adjustments": {key: round(value, 2) for key, value in adjustments.items()},
        "reasons": reasons,
    }


def compute_investment_evaluation(payload: Dict[str, Any]) -> Dict[str, Any]:
    financials = payload.get("financials", {})
    metrics = payload.get("metrics", {})
    evaluation = payload.get("evaluation_inputs", {})

    current_revenue = _safe_float(financials.get("current_revenue"))
    prior_revenue = _safe_float(financials.get("prior_revenue"))
    gross_margin = _safe_float(financials.get("gross_margin"))
    ebitda_margin = _safe_float(financials.get("ebitda_margin"))
    burn_multiple = _safe_float(financials.get("burn_multiple"))
    runway_months = _safe_float(financials.get("runway_months"))
    nrr = _safe_float(metrics.get("net_revenue_retention"))
    pipeline_coverage = _safe_float(metrics.get("pipeline_coverage"))

    growth_rate = 0.0 if prior_revenue == 0 else (current_revenue - prior_revenue) / prior_revenue
    return_strength = 3.0
    if growth_rate >= 0.5:
        return_strength += 1.0
    elif growth_rate < 0.1:
        return_strength -= 0.5
    if gross_margin >= 0.7:
        return_strength += 0.5
    elif gross_margin < 0.45:
        return_strength -= 0.5
    if runway_months >= 18:
        return_strength += 0.5
    elif runway_months and runway_months < 9:
        return_strength -= 1.0
    if burn_multiple and burn_multiple > 2.0:
        return_strength -= 0.5

    macro_adjustments = derive_macro_adjustments(payload)

    base_scores = {
        "strategic_alignment": _bounded_score(
            evaluation.get("strategic_alignment_score", metrics.get("market_score"))
        ),
        "financial_return": _bounded_score(
            evaluation.get("financial_return_score", return_strength)
        ),
        "execution_capability": _bounded_score(
            evaluation.get("execution_capability_score", metrics.get("efficiency_score"))
        ),
        "risk_profile": _bounded_score(
            evaluation.get("risk_profile_score", 6 - metrics.get("growth_score", 3))
        ),
        "stakeholder_impact": _bounded_score(
            evaluation.get("stakeholder_impact_score", nrr / 30 if nrr else 3)
        ),
    }

    category_scores = {
        name: _clamp(base_scores[name] + macro_adjustments["adjustments"].get(name, 0.0), 1.0, 5.0)
        for name in base_scores
    }

    weighted_scores = {
        name: round((score / 5.0) * INVESTMENT_WEIGHTS[name], 1)
        for name, score in category_scores.items()
    }
    total_score = round(sum(weighted_scores.values()), 1)
    recommendation = _recommendation(total_score)

    strengths: List[str] = []
    concerns: List[str] = []

    if growth_rate > 0:
        strengths.append(f"Revenue grew {_pct(growth_rate)} versus the prior period.")
    if gross_margin:
        strengths.append(f"Gross margin is {_pct(gross_margin)}, supporting scalable economics.")
    if nrr:
        strengths.append(f"Net revenue retention sits at {nrr:.0f}%, showing account expansion capacity.")
    if pipeline_coverage:
        strengths.append(f"Pipeline coverage is {pipeline_coverage:.1f}x against target demand.")

    if runway_months and runway_months < 12:
        concerns.append(f"Cash runway is only {runway_months:.1f} months.")
    if ebitda_margin < 0:
        concerns.append(f"EBITDA margin remains negative at {_pct(ebitda_margin)}.")
    if burn_multiple and burn_multiple > 2:
        concerns.append(f"Burn multiple of {burn_multiple:.1f}x indicates inefficient growth.")
    if growth_rate <= 0:
        concerns.append("Growth is flat or negative, weakening near-term investor confidence.")

    return {
        "overall_score": total_score,
        "recommendation": recommendation,
        "macro_regime": macro_adjustments["regime"],
        "macro_adjustments": macro_adjustments,
        "base_category_scores": {name: round(score, 2) for name, score in base_scores.items()},
        "category_scores": category_scores,
        "weighted_scores": weighted_scores,
        "top_strengths": strengths[:3],
        "top_concerns": concerns[:3],
    }


def compute_risk_matrix(payload: Dict[str, Any]) -> Dict[str, Any]:
    input_risks = payload.get("risks", [])
    default_risks = [
        {
            "id": "RISK-001",
            "name": "Revenue concentration",
            "category": "Strategic",
            "probability": 4,
            "impact": 4,
            "description": "Dependence on a small number of key accounts or channels.",
            "mitigation": "Diversify channel mix and expand mid-market pipeline.",
        },
        {
            "id": "RISK-002",
            "name": "Cash runway compression",
            "category": "Liquidity",
            "probability": 3,
            "impact": 5,
            "description": "Spend outpaces financing or collections.",
            "mitigation": "Reduce burn, tighten collections, and stage fundraising milestones.",
        },
        {
            "id": "RISK-003",
            "name": "Go-to-market execution slippage",
            "category": "Operational",
            "probability": 4,
            "impact": 3,
            "description": "Pipeline conversion and onboarding lag forecast.",
            "mitigation": "Install weekly pipeline reviews and tighter launch accountability.",
        },
    ]

    risks = input_risks or default_risks
    assessed: List[Dict[str, Any]] = []
    level_counts = {"Critical": 0, "High": 0, "Medium": 0, "Low": 0}

    for index, risk in enumerate(risks, start=1):
        probability = max(1, min(5, int(_safe_float(risk.get("probability"), 3))))
        impact = max(1, min(5, int(_safe_float(risk.get("impact"), 3))))
        score = probability * impact
        level = _risk_level(score)
        level_counts[level] += 1
        assessed.append(
            {
                "id": risk.get("id", f"RISK-{index:03d}"),
                "name": risk.get("name", f"Risk {index}"),
                "category": risk.get("category", "Strategic"),
                "probability": probability,
                "impact": impact,
                "score": score,
                "level": level,
                "description": risk.get("description", ""),
                "mitigation": risk.get("mitigation", ""),
            }
        )

    assessed.sort(key=lambda item: (-item["score"], item["name"]))
    aggregate = round(sum(item["score"] for item in assessed) / len(assessed), 1) if assessed else 0.0

    return {
        "aggregate_risk_score": aggregate,
        "risk_counts": level_counts,
        "top_risks": assessed[:5],
        "risk_register": assessed,
    }


def build_financial_story(payload: Dict[str, Any], evaluation: Dict[str, Any], risk_matrix: Dict[str, Any]) -> Dict[str, Any]:
    company = payload.get("company", {})
    financials = payload.get("financials", {})
    metrics = payload.get("metrics", {})
    decision = payload.get("decision_focus") or "Decide whether to support the next growth plan and fundraising narrative."

    current_revenue = _safe_float(financials.get("current_revenue"))
    prior_revenue = _safe_float(financials.get("prior_revenue"))
    cash_balance = _safe_float(financials.get("cash_balance"))
    runway_months = _safe_float(financials.get("runway_months"))
    gross_margin = _safe_float(financials.get("gross_margin"))
    ebitda_margin = _safe_float(financials.get("ebitda_margin"))
    growth_rate = 0.0 if prior_revenue == 0 else (current_revenue - prior_revenue) / prior_revenue
    burn_multiple = _safe_float(financials.get("burn_multiple"))
    nrr = _safe_float(metrics.get("net_revenue_retention"))

    top_risk = risk_matrix["top_risks"][0] if risk_matrix["top_risks"] else None
    recommendation = evaluation["recommendation"]

    return {
        "context": f"{company.get('name', 'The company')} needs stakeholders aligned around one question: {decision}",
        "state": (
            f"Current revenue is {_money(current_revenue)}, cash balance is {_money(cash_balance)}, "
            f"gross margin is {_pct(gross_margin)}, and EBITDA margin is {_pct(ebitda_margin)}."
        ),
        "delta": (
            f"Revenue changed {_pct(growth_rate)} versus the prior period while net revenue retention is "
            f"{nrr:.0f}%."
            if nrr
            else f"Revenue changed {_pct(growth_rate)} versus the prior period."
        ),
        "drivers": [
            "Growth score reflects demand capture, pipeline quality, and commercial momentum.",
            "Efficiency score reflects gross margin durability, spend discipline, and payback profile.",
            "Market score reflects category attractiveness, competitive posture, and strategic fit.",
        ],
        "trajectory": (
            f"If current trends persist, the business carries {runway_months:.1f} months of runway"
            f"{'' if runway_months else ' an uncertain runway horizon'}, with a burn multiple of {burn_multiple:.1f}x."
        ),
        "exposure": (
            f"Top exposure is {top_risk['name']} ({top_risk['level']}, score {top_risk['score']})"
            if top_risk
            else "No material risks were supplied."
        ),
        "choice": (
            f"Current engine output is '{recommendation}': lean in with measured investment, "
            "tighten operating controls, or defer expansion until the next reporting cycle."
        ),
    }


def _status_label(value: float, good_threshold: float, warn_threshold: float) -> str:
    if value >= good_threshold:
        return "GREEN"
    if value >= warn_threshold:
        return "YELLOW"
    return "RED"


def _macro_summary(payload: Dict[str, Any]) -> List[str]:
    market_context = payload.get("market_context", {})
    fred = market_context.get("fred", {})
    series = fred.get("series", {})
    summary: List[str] = []

    fed_funds = series.get("federal_funds_rate", {})
    inflation = series.get("inflation_cpi", {})
    unemployment = series.get("unemployment_rate", {})
    treasury = series.get("ten_year_treasury", {})

    if fed_funds.get("latest_value") is not None:
        summary.append(
            f"Federal funds rate: {fed_funds['latest_value']:.2f}%"
        )
    if treasury.get("latest_value") is not None:
        summary.append(
            f"10Y Treasury: {treasury['latest_value']:.2f}%"
        )
    if inflation.get("latest_value") is not None:
        summary.append(
            f"CPI index level: {inflation['latest_value']:.2f}"
        )
    if unemployment.get("latest_value") is not None:
        summary.append(
            f"Unemployment rate: {unemployment['latest_value']:.2f}%"
        )
    return summary


def _market_signal_summary(payload: Dict[str, Any]) -> List[str]:
    market_context = payload.get("market_context", {})
    alpha = market_context.get("alpha_vantage", {})
    summary: List[str] = []

    benchmark_quote = alpha.get("benchmark", {}).get("quote", {})
    benchmark_selection = alpha.get("benchmark_selection", {})
    if benchmark_quote:
        symbol = benchmark_quote.get("01. symbol", alpha.get("benchmark_symbol", "Benchmark"))
        price = benchmark_quote.get("05. price")
        change_pct = benchmark_quote.get("10. change percent")
        summary.append(f"{symbol} latest quote: {price} ({change_pct})")
        if benchmark_selection.get("reason") and benchmark_selection.get("reason") != "default_market_benchmark":
            summary.append(
                f"Benchmark selected via sector mapping: {benchmark_selection.get('input_sector') or benchmark_selection.get('normalized_sector')}"
            )

    company_quote = alpha.get("company", {}).get("quote", {})
    if company_quote:
        symbol = company_quote.get("01. symbol", alpha.get("company_symbol", "Company"))
        price = company_quote.get("05. price")
        change_pct = company_quote.get("10. change percent")
        summary.append(f"{symbol} latest quote: {price} ({change_pct})")

    return summary


def build_board_materials(payload: Dict[str, Any], evaluation: Dict[str, Any], risk_matrix: Dict[str, Any], story: Dict[str, Any]) -> Dict[str, Any]:
    company = payload.get("company", {})
    financials = payload.get("financials", {})
    metrics = payload.get("metrics", {})
    recommendations = payload.get("board_requests", [])

    current_revenue = _safe_float(financials.get("current_revenue"))
    cash_balance = _safe_float(financials.get("cash_balance"))
    runway_months = _safe_float(financials.get("runway_months"))
    nrr = _safe_float(metrics.get("net_revenue_retention"))
    growth_score = _safe_float(metrics.get("growth_score"))
    efficiency_score = _safe_float(metrics.get("efficiency_score"))

    kpis = [
        {
            "metric": "Revenue",
            "value": _money(current_revenue),
            "status": _status_label(growth_score, 4.0, 3.0),
        },
        {
            "metric": "Cash Balance",
            "value": _money(cash_balance),
            "status": _status_label(runway_months, 18.0, 12.0),
        },
        {
            "metric": "NRR",
            "value": f"{nrr:.0f}%" if nrr else "N/A",
            "status": _status_label(nrr, 120.0, 100.0) if nrr else "YELLOW",
        },
        {
            "metric": "Execution",
            "value": f"{efficiency_score:.1f}/5",
            "status": _status_label(efficiency_score, 4.0, 3.0),
        },
    ]

    decisions = recommendations or [
        "Approve the next-quarter operating plan and hiring envelope.",
        "Confirm fundraising readiness timing and target milestones.",
        "Review top risks and sponsor the mitigation owners.",
    ]

    return {
        "title": f"{company.get('name', 'Company')} Board Update",
        "executive_summary": [
            story["context"],
            story["state"],
            story["choice"],
        ],
        "kpi_dashboard": kpis,
        "macro_context": _macro_summary(payload),
        "market_signals": _market_signal_summary(payload),
        "macro_adjustments": evaluation.get("macro_adjustments", {}),
        "top_risks": risk_matrix["top_risks"][:3],
        "decisions_required": decisions,
    }


def build_quarterly_update(payload: Dict[str, Any], evaluation: Dict[str, Any], risk_matrix: Dict[str, Any], story: Dict[str, Any]) -> Dict[str, Any]:
    company = payload.get("company", {})
    return {
        "headline": f"{company.get('name', 'Company')} posted a {evaluation['recommendation'].lower()} profile this quarter.",
        "summary": [
            story["state"],
            story["delta"],
            story["trajectory"],
        ],
        "strengths": evaluation["top_strengths"],
        "concerns": evaluation["top_concerns"],
        "macro_context": _macro_summary(payload),
        "macro_regime": evaluation.get("macro_regime"),
        "watch_items": [risk["name"] for risk in risk_matrix["top_risks"][:3]],
    }


def build_pitch_deck(payload: Dict[str, Any], evaluation: Dict[str, Any], risk_matrix: Dict[str, Any], story: Dict[str, Any]) -> Dict[str, Any]:
    company = payload.get("company", {})
    financials = payload.get("financials", {})
    current_revenue = _safe_float(financials.get("current_revenue"))
    cash_balance = _safe_float(financials.get("cash_balance"))

    slides = [
        {
            "title": "Why Now",
            "points": [
                story["context"],
                story["delta"],
                *(_macro_summary(payload)[:2] or ["Market timing and internal readiness are translated into a board-level decision frame."]),
            ],
        },
        {
            "title": "Business Health",
            "points": [
                f"Revenue: {_money(current_revenue)}",
                f"Cash balance: {_money(cash_balance)}",
                f"Investment score: {evaluation['overall_score']}/100 ({evaluation['recommendation']})",
                f"Macro regime: {evaluation.get('macro_regime', 'neutral')}",
            ],
        },
        {
            "title": "Growth Engine",
            "points": evaluation["top_strengths"] or ["Growth drivers not supplied."],
        },
        {
            "title": "Risk & Resilience",
            "points": [
                f"{risk['name']} ({risk['level']}) - {risk['mitigation']}"
                for risk in risk_matrix["top_risks"][:3]
            ],
        },
        {
            "title": "The Ask",
            "points": [
                story["choice"],
                "Translate the recommendation into fundraising, spend, and milestone commitments.",
            ],
        },
    ]

    return {"deck_title": f"{company.get('name', 'Company')} Investor Pitch", "slides": slides}


def generate_investor_relations_package(payload: Dict[str, Any]) -> Dict[str, Any]:
    validation_issues = validate_payload(payload)
    evaluation = compute_investment_evaluation(payload)
    risk_matrix = compute_risk_matrix(payload)
    story = build_financial_story(payload, evaluation, risk_matrix)
    quarterly_update = build_quarterly_update(payload, evaluation, risk_matrix, story)
    pitch_deck = build_pitch_deck(payload, evaluation, risk_matrix, story)
    board_materials = build_board_materials(payload, evaluation, risk_matrix, story)

    return {
        "validation_issues": validation_issues,
        "market_context": payload.get("market_context", {}),
        "investment_evaluation": evaluation,
        "risk_assessment": risk_matrix,
        "financial_story": story,
        "quarterly_update": quarterly_update,
        "pitch_deck": pitch_deck,
        "board_materials": board_materials,
    }
