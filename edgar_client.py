from __future__ import annotations

import os
from datetime import datetime
from typing import Any, Dict, List, Optional

from edgar import Company, Filing, set_identity


def _get_identity() -> str:
    return os.environ.get("SEC_EDGAR_EMAIL", "ir-engine@example.com")


def _ensure_identity() -> None:
    set_identity(_get_identity())


def _safe_float(value: Any) -> Optional[float]:
    try:
        if value is None:
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def get_filing(
    ticker: str,
    filing_type: str = "10-K",
    limit: int = 1,
) -> Optional[Filing]:
    _ensure_identity()
    company = Company(ticker)
    filings = company.get_filings(form=filing_type)
    if filings is None or len(filings) == 0:
        return None
    return filings.latest()


def get_financials(
    ticker: str,
    filing_type: str = "10-K",
) -> Dict[str, Any]:
    _ensure_identity()
    company = Company(ticker)
    filings = company.get_filings(form=filing_type)
    if filings is None or len(filings) == 0:
        return {"error": f"No {filing_type} filings found for {ticker}"}

    filing = filings.latest()
    financials_data: Dict[str, Any] = {
        "ticker": ticker,
        "filing_type": filing_type,
        "fetched_at": datetime.utcnow().isoformat() + "Z",
        "statements": {},
    }

    try:
        financials = filing.obj()
        if hasattr(financials, "income_statement"):
            income = financials.income_statement()
            if income is not None:
                financials_data["statements"]["income_statement"] = _statement_to_dict(income)

        if hasattr(financials, "balance_sheet"):
            balance = financials.balance_sheet()
            if balance is not None:
                financials_data["statements"]["balance_sheet"] = _statement_to_dict(balance)

        if hasattr(financials, "cashflow_statement"):
            cashflow = financials.cashflow_statement()
            if cashflow is not None:
                financials_data["statements"]["cashflow_statement"] = _statement_to_dict(cashflow)
    except Exception as exc:
        financials_data["error"] = f"Failed to extract financials: {exc}"

    return financials_data


def get_filing_text(
    ticker: str,
    filing_type: str = "10-K",
) -> Optional[str]:
    _ensure_identity()
    company = Company(ticker)
    filings = company.get_filings(form=filing_type)
    if filings is None or len(filings) == 0:
        return None
    filing = filings.latest()
    return str(filing)


def get_filings_list(
    ticker: str,
    filing_type: Optional[str] = None,
    limit: int = 10,
) -> List[Dict[str, Any]]:
    _ensure_identity()
    company = Company(ticker)
    if filing_type:
        filings = company.get_filings(form=filing_type)
    else:
        filings = company.get_filings()

    if filings is None:
        return []

    result: List[Dict[str, Any]] = []
    for i, filing in enumerate(filings):
        if i >= limit:
            break
        result.append({
            "accession_number": filing.accession_number,
            "form_type": filing.form,
            "filing_date": str(filing.filing_date),
            "primary_document": filing.primary_document,
        })
    return result


def _statement_to_dict(statement: Any) -> Dict[str, Any]:
    try:
        if hasattr(statement, "to_dataframe"):
            df = statement.to_dataframe()
            if df is not None and not df.empty:
                return {
                    "columns": list(df.columns),
                    "data": df.head(20).to_dict(orient="records"),
                }
    except Exception:
        pass
    return {}
