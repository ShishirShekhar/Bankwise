from fastapi import FastAPI
from pydantic import BaseModel

from app.calculators.fd import calculate_fd


app = FastAPI(title="BankWise API")


class FDCalculationRequest(BaseModel):
    principal: float
    annual_rate: float
    tenure_months: int
    compounding_frequency: int = 4


@app.get("/api/health")
def health_check():
    return {"status": "healthy"}


@app.post("/api/calculations/fd")
def calculate_fd_api(request: FDCalculationRequest):
    return calculate_fd(
        principal=request.principal,
        annual_rate=request.annual_rate,
        tenure_months=request.tenure_months,
        compounding_frequency=request.compounding_frequency,
    )