from datetime import date, datetime
from typing import List, Optional

from pydantic import BaseModel, Field, HttpUrl


class Requirements(BaseModel):
    product_category: str = "FD"
    amount: Optional[float] = Field(default=None, gt=0)
    currency: str = "INR"
    duration_months: Optional[int] = Field(default=None, gt=0)
    liquidity_preference: Optional[str] = None
    risk_preference: Optional[str] = None
    goal: Optional[str] = None
    premature_withdrawal_important: bool = False
    missing_information: List[str] = Field(default_factory=list)


class DecisionRequest(BaseModel):
    query: str = Field(min_length=1, max_length=4000)


class FDCalculationRequest(BaseModel):
    product_id: str
    principal: float = Field(gt=0)
    tenure_months: int = Field(gt=0, le=1200)


class CompareRequest(BaseModel):
    product_ids: List[str] = Field(min_length=1, max_length=20)
    requirements: Requirements


class SourceInput(BaseModel):
    source_type: str
    url: HttpUrl
    title: str
    verified_at: Optional[datetime] = None
    effective_from: Optional[date] = None
    effective_to: Optional[date] = None


class HealthResponse(BaseModel):
    status: str
