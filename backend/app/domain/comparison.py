"""Focused service operations: comparison and deterministic trade-off analysis."""

from app.domain.catalog import product_payload
from app.domain.rates import calculate_product_fd, matching_rates


def _extract_penalty_pp(conditions: list[dict]) -> float | None:
    for cond in conditions:
        if cond.get("type") == "premature_withdrawal_penalty_percentage_points":
            val = cond.get("value")
            if val is not None:
                try:
                    return float(val)
                except (ValueError, TypeError):
                    pass
    return None


def compare_products(catalog, product_ids: list, amount: float, tenure: int) -> dict:
    results = []
    for product_id in dict.fromkeys(product_ids):
        product = catalog.get_product(product_id, status="ACTIVE")
        if product is None:
            continue
        payload = product_payload(product, catalog, amount, tenure)
        eligible_rates = matching_rates(product.get("rates", []), amount, tenure)
        eligible = len(eligible_rates) == 1
        calculation = None
        reason = None
        if eligible:
            outcome = calculate_product_fd(catalog, product["id"], amount, tenure)
            if outcome["status"] == "CALCULATED":
                calculation = outcome["result"]
            else:
                reason = outcome["reason"]
        else:
            reason = "No single eligible rate band is available"
        results.append(
            {
                "product": payload,
                "eligible": eligible,
                "calculation": calculation,
                "calculation_blocked_reason": reason if calculation is None else None,
            }
        )

    # Calculate trade-offs among calculated products
    calculated_items = [x for x in results if x.get("calculation")]
    tradeoff_summary = None

    if calculated_items:
        calculated_items.sort(
            key=lambda x: x["calculation"]["maturity_amount"], reverse=True
        )
        best_item = calculated_items[0]
        best_id = best_item["product"]["id"]
        best_amount = best_item["calculation"]["maturity_amount"]
        best_bank = best_item["product"]["bank"]
        best_penalty = _extract_penalty_pp(best_item["product"].get("conditions", []))

        second_item = calculated_items[1] if len(calculated_items) > 1 else None
        second_amount = (
            second_item["calculation"]["maturity_amount"] if second_item else None
        )
        second_bank = second_item["product"]["bank"] if second_item else None
        second_penalty = (
            _extract_penalty_pp(second_item["product"].get("conditions", []))
            if second_item
            else None
        )

        min_penalty = None
        for item in calculated_items:
            p = _extract_penalty_pp(item["product"].get("conditions", []))
            if p is not None and (min_penalty is None or p < min_penalty):
                min_penalty = p

        for item in results:
            calc = item["calculation"]
            if not calc:
                item["tradeoff"] = None
                continue

            maturity = calc["maturity_amount"]
            diff = round(best_amount - maturity, 2)
            is_best = item["product"]["id"] == best_id
            penalty = _extract_penalty_pp(item["product"].get("conditions", []))

            gains = []
            give_ups = []

            if is_best:
                if second_item and second_amount is not None:
                    lead = round(best_amount - second_amount, 2)
                    gains.append(
                        f"+₹{lead:,.2f} higher calculated maturity vs {second_bank}"
                    )
                gains.append("Highest calculated return among verified options")

                if (
                    penalty is not None
                    and min_penalty is not None
                    and penalty > min_penalty
                ):
                    give_ups.append(
                        f"Higher early exit penalty ({penalty:.2f}% vs {min_penalty:.2f}%)"
                    )
                else:
                    give_ups.append(
                        "Standard premature withdrawal terms and conditions apply"
                    )
            else:
                give_ups.append(f"-₹{diff:,.2f} lower calculated maturity vs {best_bank}")
                if (
                    penalty is not None
                    and best_penalty is not None
                    and penalty < best_penalty
                ):
                    gains.append(
                        f"Lower exit penalty ({penalty:.2f}% vs {best_penalty:.2f}%)"
                    )
                else:
                    gains.append("Verified domestic term deposit terms")

            item["tradeoff"] = {
                "maturity_difference_vs_highest": diff,
                "is_highest_calculated_maturity": is_best,
                "gains": gains,
                "give_ups": give_ups,
            }

        if second_item and second_amount is not None:
            lead = round(best_amount - second_amount, 2)
            if (
                second_penalty is not None
                and best_penalty is not None
                and second_penalty < best_penalty
            ):
                tradeoff_summary = (
                    f"Choosing {best_bank} yields approximately ₹{lead:,.2f} more at maturity. "
                    f"However, {second_bank} provides more favorable liquidity with a lower premature "
                    f"withdrawal penalty ({second_penalty:.2f}% vs {best_penalty:.2f}%) if you need funds early."
                )
            else:
                tradeoff_summary = (
                    f"{best_bank} offers the highest calculated maturity at ₹{best_amount:,.2f}, "
                    f"exceeding {second_bank} by ₹{lead:,.2f} over the {tenure}-month period."
                )

    return {
        "products": results,
        "tradeoff_summary": tradeoff_summary,
        "warnings": (
            []
            if calculated_items
            else [
                "No products have a current, conflict-free, authoritative rate for this request."
            ]
        ),
    }
