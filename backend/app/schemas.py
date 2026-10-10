from pydantic import BaseModel, Field


class Requirements(BaseModel):
    product_category: str = "FD"
    amount: float | None = Field(default=None, gt=0, allow_inf_nan=False)
    currency: str = "INR"
    duration_months: int | None = Field(default=None, gt=0)
    liquidity_preference: str | None = None
    risk_preference: str | None = None
    goal: str | None = None
    premature_withdrawal_important: bool = False
    missing_information: list[str] = Field(default_factory=list)


class DecisionRequest(BaseModel):
    query: str = Field(min_length=1, max_length=4000)


class FDCalculationRequest(BaseModel):
    product_id: str
    principal: float = Field(gt=0, allow_inf_nan=False)
    tenure_months: int = Field(gt=0, le=1200)


class CompareRequest(BaseModel):
    product_ids: list[str] = Field(min_length=1, max_length=20)
    requirements: Requirements


class HealthResponse(BaseModel):
    status: str
