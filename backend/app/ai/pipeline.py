from typing import Literal

from pydantic import BaseModel, Field

from app.ai.explanation import explain
from app.ai.extraction import Requirements, extract
from app.ai.tools import DEMO_RATES, calculate_early_withdrawal, calculate_fd_maturity


class Option(BaseModel):
    bank: str
    rate_percent: float
    maturity_amount: float
    interest_earned: float
    early_exit_months: int | None = None
    early_exit_amount: float | None = None
    penalty_pp: float | None = None
    lock_in_months: int | None = None
    early_exit_note: str | None = None


class Skipped(BaseModel):
    bank: str
    reason: str


class PipelineResult(BaseModel):
    status: Literal["OK", "NEEDS_CLARIFICATION", "UNSUPPORTED", "NO_MATCH"]
    message: str | None = None
    requirements: Requirements
    options: list[Option] = Field(default_factory=list)
    skipped: list[Skipped] = Field(default_factory=list)
    best_if_withdrawn_early: str | None = None
    explanation: str | None = None


def default_months_held(duration_months: int) -> int:
    return 12 if duration_months > 12 else max(1, duration_months // 2)


def clarifying_question(missing: list[str]) -> str:
    if len(missing) == 2:
        return "How much would you like to invest, and for how long?"
    if missing == ["amount"]:
        return "How much would you like to invest?"
    return "For how long would you like to keep the money invested?"


def build_option(bank: str, maturity: dict, amount: float, duration: int) -> Option:
    held = default_months_held(duration)
    early = calculate_early_withdrawal(bank, amount, duration, held)
    return Option(
        bank=bank,
        rate_percent=maturity["rate_percent"],
        maturity_amount=maturity["maturity_amount"],
        interest_earned=maturity["interest_earned"],
        early_exit_months=held,
        early_exit_amount=early.get("amount_received"),
        penalty_pp=early.get("penalty_pp"),
        lock_in_months=early.get("lock_in_months"),
        early_exit_note=(
            f"Locked in for {early['lock_in_months']} months"
            if early.get("error") == "locked_in"
            else None
        ),
    )


def run(text: str) -> PipelineResult:
    req = extract(text)

    if req.category not in (None, "FD"):
        return PipelineResult(
            status="UNSUPPORTED",
            requirements=req,
            message="Only fixed deposits are supported for now.",
        )
    if req.missing:
        return PipelineResult(
            status="NEEDS_CLARIFICATION",
            requirements=req,
            message=clarifying_question(req.missing),
        )

    options: list[Option] = []
    skipped: list[Skipped] = []
    for bank in DEMO_RATES:
        maturity = calculate_fd_maturity(bank, req.amount, req.duration_months)
        if "error" in maturity:
            skipped.append(Skipped(bank=bank, reason=maturity["error"]))
        else:
            options.append(
                build_option(bank, maturity, req.amount, req.duration_months)
            )

    if not options:
        return PipelineResult(
            status="NO_MATCH",
            requirements=req,
            skipped=skipped,
            message="No bank has a stored rate for that duration.",
        )

    options.sort(key=lambda o: o.maturity_amount, reverse=True)
    with_exit = [o for o in options if o.early_exit_amount is not None]
    best_early = (
        max(with_exit, key=lambda o: o.early_exit_amount).bank if with_exit else None
    )

    return PipelineResult(
        status="OK",
        requirements=req,
        options=options,
        skipped=skipped,
        best_if_withdrawn_early=best_early,
        explanation=explain(req, options, best_early),
    )
