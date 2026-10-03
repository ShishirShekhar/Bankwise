import re
import uuid
from datetime import date, datetime, timedelta, timezone
from typing import Optional

from app.calculators.fd import calculate_fd
from app.config import GEMINI_MODEL, SOURCE_MAX_AGE_DAYS
from app.schemas import Requirements


def redact_sensitive_input(query: str) -> str:
    """Remove common credential/identity values before sending free text to a model."""
    redacted = re.sub(r"(?i)\b(?:PAN|Aadhaar|account number|card number|CVV|UPI PIN|banking password)\b\s*(?:is|:|=)?\s*[A-Z0-9-]{4,}", "[REDACTED]", query)
    redacted = re.sub(r"\b[A-Z]{5}[0-9]{4}[A-Z]\b", "[REDACTED]", redacted, flags=re.I)
    redacted = re.sub(r"(?<!\d)(?:\d[ -]?){11}\d(?!\d)", "[REDACTED]", redacted)
    redacted = re.sub(r"(?<!\d)(?:\d[ -]?){15}\d(?!\d)", "[REDACTED]", redacted)
    return redacted


def extract_requirements(query: str, use_gemini: bool = True) -> Requirements:
    """Use Gemini when configured; otherwise extract only values stated explicitly."""
    query = redact_sensitive_input(query)
    amount_match = re.search(r"(?:₹|rs\.?\s*|inr\s*)([\d,]+(?:\.\d+)?)\s*(lakh|lac| lakhs|crore)?", query, re.I)
    amount = None
    if amount_match:
        amount = float(amount_match.group(1).replace(",", ""))
        scale = (amount_match.group(2) or "").strip().lower()
        amount *= 100000 if scale.startswith(("lakh", "lac")) else 10000000 if scale == "crore" else 1
    tenure = None
    years = re.search(r"(\d+(?:\.\d+)?)\s*years?", query, re.I)
    months = re.search(r"(\d+)\s*months?", query, re.I)
    if years:
        tenure = int(float(years.group(1)) * 12)
    elif months:
        tenure = int(months.group(1))
    try:
        from google import genai
        from google.genai import types
        from app.config import GOOGLE_CLOUD_LOCATION, GOOGLE_CLOUD_PROJECT
        if use_gemini and GOOGLE_CLOUD_PROJECT:
            client = genai.Client(vertexai=True, project=GOOGLE_CLOUD_PROJECT, location=GOOGLE_CLOUD_LOCATION)
            response = client.models.generate_content(
                model=GEMINI_MODEL,
                contents=("Extract stated FD requirements and preferences. Never infer an amount or duration that is not explicit. "
                          "Return the requested JSON fields. Do not request/store sensitive banking credentials. Query: " + query),
                config=types.GenerateContentConfig(response_mime_type="application/json", response_schema=Requirements, temperature=0),
            )
            parsed = Requirements.model_validate_json(response.text or "{}")
            # Numeric facts must be found in the user text by deterministic parsing.
            parsed.amount = amount
            parsed.duration_months = tenure
            parsed.missing_information = (["amount"] if amount is None else []) + (["duration_months"] if tenure is None else [])
            return parsed
    except Exception:
        # Keep local operation available when credentials or Vertex AI are unavailable.
        pass
    missing = []
    if amount is None:
        missing.append("amount")
    if tenure is None:
        missing.append("duration_months")
    lowered = query.lower()
    liquidity = "HIGH" if any(x in lowered for x in ("early", "withdraw", "liquid", "flexib")) else None
    return Requirements(amount=amount, duration_months=tenure, liquidity_preference=liquidity,
                        premature_withdrawal_important=liquidity == "HIGH", missing_information=missing)


def freshness(source: dict) -> str:
    if source.get("status") != "ACTIVE":
        return "LOW"
    checked = source.get("verified_at") or source.get("retrieved_at")
    if not checked:
        return "LOW"
    if checked.tzinfo is None:
        checked = checked.replace(tzinfo=timezone.utc)
    if checked < datetime.now(timezone.utc) - timedelta(days=SOURCE_MAX_AGE_DAYS):
        return "LOW"
    return "HIGH" if source.get("source_type", "").upper().startswith("OFFICIAL_BANK") else "MEDIUM"


def rate_is_usable(catalog, product_id: str, rate: dict) -> tuple:
    if rate.get("verification_status") != "HIGH":
        return False, "Rate is not verified at HIGH confidence"
    today = date.today()
    if rate.get("effective_from") and rate["effective_from"] > today:
        return False, "Rate is not effective yet"
    if rate.get("effective_to") and rate["effective_to"] < today:
        return False, "Rate has expired"
    if catalog.get_conflicts(product_id, field_name="rate"):
        return False, "Rate has an unresolved source conflict"
    source = catalog.get_source(rate.get("source_id")) if rate.get("source_id") else None
    if not source or freshness(source) != "HIGH":
        return False, "Rate does not have a current official source"
    return True, None


def product_payload(product: dict, catalog, amount: Optional[float] = None, tenure: Optional[int] = None) -> dict:
    rates = []
    for rate in product.get("rates", []):
        eligible = True
        if amount is not None and ((rate.get("min_amount") is not None and amount < rate["min_amount"]) or (rate.get("max_amount") is not None and amount > rate["max_amount"])):
            eligible = False
        min_tenure = rate.get("tenure_min_months") or rate.get("tenure_months")
        max_tenure = rate.get("tenure_max_months") or rate.get("tenure_months")
        if tenure is not None and ((min_tenure is not None and tenure < min_tenure) or (max_tenure is not None and tenure > max_tenure)):
            eligible = False
        usable, reason = rate_is_usable(catalog, product["id"], rate)
        rates.append({"id": rate["id"], "annual_rate_percent": rate["rate"], "min_amount": rate.get("min_amount"),
                      "max_amount": rate.get("max_amount"), "tenure_months": rate.get("tenure_months"),
                      "tenure_min_months": rate.get("tenure_min_months"), "tenure_max_months": rate.get("tenure_max_months"),
                      "compounding_frequency": rate.get("compounding_frequency"), "payout_type": rate.get("payout_type"),
                      "effective_from": rate.get("effective_from"), "effective_to": rate.get("effective_to"),
                      "verification_status": "CONFLICT" if not usable and reason and "conflict" in reason.lower() else rate.get("verification_status"),
                      "usable_for_calculation": usable, "ineligibility_reason": None if eligible else "Amount or tenure is outside the sourced rate band"})
    return {"id": product["id"], "bank": product["bank"],
            "category": product["category"], "name": product["name"], "description": product.get("description"), "status": product["status"],
            "rates": rates,
            "conditions": [{"type": c["condition_type"], "value": c["condition_value"], "verification_status": c.get("verification_status")} for c in product.get("conditions", [])],
            "sources": [{"id": s["id"], "type": s["source_type"], "url": s["url"], "title": s["title"], "retrieved_at": s.get("retrieved_at"),
                         "verified_at": s.get("verified_at"), "freshness": freshness(s)} for s in product.get("sources", [])]}


def compare_products(catalog, product_ids: list, amount: float, tenure: int) -> dict:
    results = []
    for product_id in dict.fromkeys(product_ids):
        product = catalog.get_product(product_id, status="ACTIVE")
        if product is None:
            continue
        payload = product_payload(product, catalog, amount, tenure)
        eligible_rates = [r for r in product.get("rates", []) if (r.get("tenure_months") == tenure or (r.get("tenure_months") is None and (r.get("tenure_min_months") is None or tenure >= r["tenure_min_months"]) and (r.get("tenure_max_months") is None or tenure <= r["tenure_max_months"]))) and (r.get("min_amount") is None or amount >= r["min_amount"]) and (r.get("max_amount") is None or amount <= r["max_amount"])]
        rate = eligible_rates[0] if len(eligible_rates) == 1 else None
        if rate:
            ok, reason = rate_is_usable(catalog, product["id"], rate)
        else:
            ok, reason = False, "No single eligible rate band is available"
        calculation = None
        if ok and rate.get("payout_type", "").upper() == "CUMULATIVE":
            try:
                calculation = calculate_fd(amount, rate["rate"], tenure, rate.get("compounding_frequency"))
            except ValueError as exc:
                reason = str(exc)
        if ok and calculation is None:
            reason = "Only cumulative payout calculation is currently supported"
        results.append({"product": payload, "eligible": bool(rate), "calculation": calculation,
                        "calculation_blocked_reason": reason if calculation is None else None})
    amounts = [(x["product"]["id"], x["calculation"]["maturity_amount"]) for x in results if x["calculation"]]
    if amounts:
        best_id, best = max(amounts, key=lambda item: item[1])
        for item in results:
            calc = item["calculation"]
            item["tradeoff"] = ({"maturity_difference_vs_highest": round(best - calc["maturity_amount"], 2),
                                  "is_highest_calculated_maturity": item["product"]["id"] == best_id} if calc else None)
    return {"products": results, "warnings": [] if amounts else ["No products have a current, conflict-free, authoritative rate for this request."]}


def new_id(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex}"
