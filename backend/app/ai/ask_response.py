"""Shape source grounded decision results for the comparison UI contract."""

from decimal import ROUND_HALF_UP, Decimal


def _inr(value: float | None) -> str | None:
    if value is None:
        return None
    whole = str(int(Decimal(str(value)).quantize(Decimal(1), rounding=ROUND_HALF_UP)))
    if len(whole) <= 3:
        grouped = whole
    else:
        grouped = whole[-3:]
        prefix = whole[:-3]
        groups = []
        while len(prefix) > 2:
            groups.insert(0, prefix[-2:])
            prefix = prefix[:-2]
        if prefix:
            groups.insert(0, prefix)
        grouped = ",".join(groups + [grouped])
    return f"₹{grouped}"


def to_ask_response(result: dict) -> dict:
    requirements = result["requirements"]
    missing = requirements.get("missing_information", [])
    category = requirements.get("product_category")
    comparisons = result.get("comparisons", [])

    options = []
    skipped = []
    for comparison in comparisons if category in (None, "FD") else []:
        product = comparison["product"]
        bank = product["bank"]
        if not comparison["eligible"]:
            skipped.append(
                {"bank": bank, "reason": "No rate slab matches this amount and duration"}
            )
            continue
        rate = next(
            (
                candidate
                for candidate in product["rates"]
                if candidate.get("ineligibility_reason") is None
            ),
            None,
        )
        if rate is None:
            skipped.append({"bank": bank, "reason": "No unique rate matches these inputs"})
            continue
        if not rate.get("usable_for_calculation"):
            skipped.append(
                {
                    "bank": bank,
                    "reason": rate.get("verification_status")
                    or "Rate is not currently verified",
                    "sources": product.get("sources", []),
                    "conflicts": product.get("conflicts", []),
                }
            )
            continue

        source = next(
            (
                source
                for source in product.get("sources", [])
                if source.get("id") == rate.get("source_id")
            ),
            product.get("sources", [{}])[0],
        )
        calculation = comparison.get("calculation") or {}
        conditions = product.get("conditions", [])
        withdrawal = next(
            (
                condition
                for condition in conditions
                if condition.get("type") == "premature_withdrawal_policy"
            ),
            None,
        )
        withdrawal_allowed = next(
            (
                condition.get("value")
                for condition in conditions
                if condition.get("type") == "premature_withdrawal_allowed"
            ),
            None,
        )
        penalty = next(
            (
                condition.get("value")
                for condition in conditions
                if condition.get("type")
                == "premature_withdrawal_penalty_percentage_points"
            ),
            None,
        )
        early_note = (
            withdrawal.get("value") if withdrawal else "Penalty terms are unavailable."
        )
        if withdrawal_allowed is True:
            early_note = "Early withdrawal is allowed. " + early_note
        elif withdrawal_allowed is False:
            early_note = "Early withdrawal is not allowed. " + early_note
        early_note += " An early-exit amount needs a specific withdrawal date."

        maturity = calculation.get("maturity_amount")
        interest = calculation.get("interest_earned")
        options.append(
            {
                "bank": bank,
                "product_name": product["name"],
                "rate_percent": rate["annual_rate_percent"],
                "maturity_amount": maturity,
                "interest_earned": interest,
                "early_exit_months": None,
                "early_exit_amount": None,
                "penalty_pp": penalty,
                "lock_in_months": None,
                "early_exit_note": early_note,
                "rate": f"{rate['annual_rate_percent']:.2f}%",
                "maturity": _inr(maturity) or "Unavailable",
                "interest": _inr(interest) or "Unavailable",
                "flexibility": (
                    "Available"
                    if withdrawal_allowed is True
                    else "Unavailable"
                    if withdrawal_allowed is False
                    else "Terms unavailable"
                ),
                "penalty": early_note,
                "verified": (
                    f"Verified {source['verified_at'][:10]} · {source['freshness']}"
                    if source.get("verified_at")
                    else f"Verification: {source.get('freshness', 'unknown')}"
                ),
                "tag": "Estimate available" if maturity is not None else "Rate available",
                "calculation_note": (
                    calculation.get("warnings", [None])[0]
                    if calculation
                    else comparison.get("calculation_blocked_reason")
                ),
                "source": source,
                "calculation_source_url": rate.get("calculation_source_url"),
                "penalty_source_url": withdrawal.get("source_url") if withdrawal else None,
            }
        )

    options.sort(
        key=lambda option: (
            option["maturity_amount"] is not None,
            option["maturity_amount"] or option["rate_percent"],
        ),
        reverse=True,
    )
    if options and options[0]["maturity_amount"] is not None:
        options[0]["tag"] = "Highest estimated maturity"

    if category not in (None, "FD"):
        status = "UNSUPPORTED"
        message = "Only fixed deposits are currently supported."
        explanation = message
        options = []
    elif missing:
        status = "NEEDS_CLARIFICATION"
        message = "Please provide the missing FD amount or duration."
        explanation = message
    elif options:
        status = "OK"
        message = None
        top = options[0]
        amount_text = _inr(requirements.get("amount"))
        duration = requirements.get("duration_months")
        explanation = (
            f"For {amount_text} over {duration} months, {top['bank']} has the highest "
            f"estimated maturity at {top['maturity']}. Estimates assume a cumulative FD "
            "with quarterly reinvestment and may differ from the bank's exact day-count method. "
            "You mentioned possible early withdrawal; the amount is not estimated because no "
            "withdrawal date was provided. Review each option's sourced withdrawal terms."
        )
    else:
        status = "NO_MATCH"
        message = "No currently verified rate matches this amount and duration."
        explanation = message

    return {
        "status": status,
        "message": message,
        "requirements": {
            "category": category or "FD",
            "amount": requirements.get("amount"),
            "duration_months": requirements.get("duration_months"),
            "liquidity_need": requirements.get("liquidity_preference"),
            "missing": missing,
        },
        "options": options,
        "skipped": skipped,
        "best_if_withdrawn_early": None,
        "explanation": explanation,
        "warnings": result.get("warnings", []),
        "sources": result.get("sources", []),
        "ai": result.get("ai"),
        "request_id": result.get("request_id"),
        "session_id": result.get("session_id"),
        "session_persisted": result.get("session_persisted"),
    }
