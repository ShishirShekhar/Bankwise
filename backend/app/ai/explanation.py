import json
import re

from google.genai import types
from google.genai.errors import APIError

from app.ai.extraction import Requirements, _get_client
from app.config import GEMINI_MODEL

SYSTEM_PROMPT = """You explain fixed deposit options to a non-expert in simple English.
Rules:
- Use ONLY the facts in the JSON. Never invent or compute any number, rate, fee or penalty.
- Write rupee amounts and percentages exactly as given. No rounding, no "lakh" shorthand.
- Do not say one bank is the best overall. Say what each choice gains and what it gives up.
- If the user may need the money early, explain the early-withdrawal difference first.
- Rates and penalties are stored demo values; amounts are calculated.
- Maximum 90 words, no bullet points, no markdown."""

_NUMBER = re.compile(r"\d[\d,]*(?:\.\d+)?")


def format_inr(amount: float) -> str:
    """Indian digit grouping, whole rupees: 577269.77 -> '₹5,77,270'."""
    whole = f"{round(amount):d}"
    if len(whole) > 3:
        head, tail = whole[:-3], whole[-3:]
        parts = []
        while len(head) > 2:
            parts.insert(0, head[-2:])
            head = head[:-2]
        if head:
            parts.insert(0, head)
        whole = ",".join(parts + [tail])
    return f"₹{whole}"


def build_facts(req: Requirements, options: list, best_early: str | None) -> dict:
    return {
        "amount": req.amount,
        "duration_months": req.duration_months,
        "may_need_money_early": req.liquidity_need == "HIGH",
        "best_if_withdrawn_early": best_early,
        "options": [o.model_dump(exclude_none=True) for o in options],
    }


def _numbers(text: str) -> list[float]:
    return [float(n.replace(",", "")) for n in _NUMBER.findall(text)]


def _allowed_numbers(facts: dict) -> set[float]:
    return set(_numbers(json.dumps(facts)))


def _matches(claim: float, allowed: set[float]) -> bool:
    for a in allowed:
        if abs(claim - a) < 0.01:  # rates, penalties, exact amounts
            return True
        if claim >= 1000 and claim == int(claim) and abs(claim - a) <= 0.5:  # whole-rupee rounding
            return True
    return False


def is_grounded(text: str, facts: dict) -> bool:
    """Every number in the text, in any format, must exist in the calculated facts."""
    allowed = _allowed_numbers(facts)
    return all(_matches(c, allowed) for c in _numbers(text))


def template(req: Requirements, options: list, best_early: str | None) -> str:
    top = options[0]
    text = (
        f"For {format_inr(req.amount)} over {req.duration_months} months, {top.bank} gives the highest "
        f"calculated maturity ({format_inr(top.maturity_amount)})."
    )
    if best_early and best_early != top.bank:
        other = next(o for o in options if o.bank == best_early)
        text += (
            f" If you withdraw after {other.early_exit_months} months, {best_early} pays more "
            f"({format_inr(other.early_exit_amount)}) because its early-exit penalty is lower."
        )
    return text


def _generate(facts: dict) -> str | None:
    try:
        response = _get_client().models.generate_content(
            model=GEMINI_MODEL,
            contents=json.dumps(facts, ensure_ascii=False),
            config=types.GenerateContentConfig(system_instruction=SYSTEM_PROMPT, temperature=0.2),
        )
        return (response.text or "").strip() or None
    except (APIError, RuntimeError, OSError):
        return None


def explain(req: Requirements, options: list, best_early: str | None) -> str:
    facts = build_facts(req, options, best_early)
    text = _generate(facts)
    if text and is_grounded(text, facts):
        return text
    return template(req, options, best_early)
