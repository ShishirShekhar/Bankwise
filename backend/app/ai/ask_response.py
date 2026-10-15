"""Shape source grounded decision results for the comparison UI contract."""

from decimal import ROUND_HALF_UP, Decimal


def _bank_name(bank: str | dict | None) -> str:
    """Return the display name for either catalog repository's bank shape."""
    if isinstance(bank, dict):
        name = bank.get("name")
        return name if isinstance(name, str) and name else "Unknown bank"
    return bank if isinstance(bank, str) and bank else "Unknown bank"


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


def _early_withdrawal_result(options: list[dict], requested: bool) -> dict | None:
    """Compare only complete, verified withdrawal terms; never infer missing penalties."""
    if not requested:
        return None
    unranked = [
        option["bank"]
        for option in options
        if option.get("withdrawal_allowed") is not True
        or option.get("penalty_pp") is None
        or not option.get("penalty_source_url")
    ]
    if unranked or not options:
        return {
            "status": "INSUFFICIENT_DATA",
            "reason": "Verified withdrawal permission and penalty data are not available for every compared product.",
            "unranked_banks": unranked,
        }
    lowest_penalty = min(option["penalty_pp"] for option in options)
    winners = [option for option in options if option["penalty_pp"] == lowest_penalty]
    if len(winners) != 1:
        return {
            "status": "TIE",
            "banks": [option["bank"] for option in winners],
            "penalty_pp": lowest_penalty,
            "ranking_basis": "lowest verified premature-withdrawal penalty",
        }
    winner = winners[0]
    return {
        "status": "RANKED",
        "bank": winner["bank"],
        "penalty_pp": lowest_penalty,
        "source_url": winner["penalty_source_url"],
        "ranking_basis": "lowest verified premature-withdrawal penalty",
        "payout_note": "A withdrawal date and actual holding-period rate are required to calculate an early-exit amount.",
    }


def to_ask_response(result: dict) -> dict:
    requirements = result["requirements"]
    missing = requirements.get("missing_information", [])
    category = requirements.get("product_category")
    comparisons = result.get("comparisons", [])

    options = []
    skipped = []
    for comparison in comparisons if category in (None, "FD") else []:
        product = comparison["product"]
        bank = _bank_name(product.get("bank"))
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

        def verified_condition(condition_type: str, product_conditions: list[dict]):
            return next(
                (
                    condition
                    for condition in product_conditions
                    if condition.get("type") == condition_type
                    and (
                        condition.get("verification_status") == "HIGH"
                        or condition.get("verified") is True
                    )
                ),
                None,
            )

        withdrawal = next(
            (
                condition
                for condition in conditions
                if condition.get("type") == "premature_withdrawal_policy"
                and (
                    condition.get("verification_status") == "HIGH"
                    or condition.get("verified") is True
                )
            ),
            None,
        )
        withdrawal_allowed_condition = verified_condition(
            "premature_withdrawal_allowed", conditions
        )
        withdrawal_allowed = (
            withdrawal_allowed_condition.get("value")
            if withdrawal_allowed_condition
            else None
        )
        penalty_condition = verified_condition(
            "premature_withdrawal_penalty_percentage_points", conditions
        )
        penalty = penalty_condition.get("value") if penalty_condition else None
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
                "withdrawal_allowed": withdrawal_allowed,
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
                # Deterministic calculator output, unchanged, for the breakdown view.
                "calculation": comparison.get("calculation"),
                "penalty_source_url": withdrawal.get("source_url") if withdrawal else None,
                "tradeoff": comparison.get("tradeoff"),
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
        liquidity = requirements.get("liquidity_preference")
        decision = (
            f"For {amount_text} over {duration} months, {top['bank']} has the highest calculated maturity "
            f"among the currently verified options: {top['maturity']} ({top['rate']})."
        )
        if liquidity:
            decision += f" Your stated liquidity preference is {liquidity.lower()}."
        tradeoff_text = result.get("tradeoff_summary") or (
            "No verified alternative has a comparable calculated outcome for these inputs."
        )
        calculation = top.get("calculation") or {}
        frequency = calculation.get("compounding_frequency_per_year")
        source = top.get("source") or {}
        conditions = top.get("early_exit_note") or "Withdrawal terms are unavailable."
        transparency = (
            f"The estimate uses the sourced compounding frequency of {frequency} times per year. "
            if frequency
            else "A maturity estimate is unavailable because compounding terms are missing. "
        )
        transparency += f"Withdrawal terms: {conditions}"
        verified_at = source.get("verified_at")
        transparency += (
            f" Source verification date: {verified_at[:10]}."
            if verified_at
            else " Source verification date is unavailable."
        )
        warning = (calculation.get("warnings") or [None])[0]
        if warning:
            transparency += f" {warning}"
        explanation = "\n\n".join(
            [
                f"1. Executive Decision Summary: {decision}",
                f"2. The Key Trade-off ('What Am I Giving Up?'): {tradeoff_text}",
                f"3. Conditions & Transparency: {transparency}",
            ]
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
        "best_if_withdrawn_early": _early_withdrawal_result(
            options, requirements.get("premature_withdrawal_important") is True
        ),
        "explanation": explanation,
        "tradeoff_summary": result.get("tradeoff_summary"),
        "warnings": result.get("warnings", []),
        "sources": result.get("sources", []),
        "ai": result.get("ai"),
        "request_id": result.get("request_id"),
        "session_id": result.get("session_id"),
        "session_persisted": result.get("session_persisted"),
        "research": result.get("research"),
    }
