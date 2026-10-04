from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from app.agents.orchestrator import run_decision_agent
from app.config import BIGQUERY_PROJECT, CORS_ORIGINS, FIRESTORE_PROJECT, GOOGLE_CLOUD_PROJECT
from app.repositories.bigquery import BigQueryRepository
from app.repositories.firestore import FirestoreSessionRepository
from app.schemas import CompareRequest, DecisionRequest, FDCalculationRequest, HealthResponse
from app.services import compare_products, extract_requirements, freshness, new_id, product_payload, rate_is_usable, redact_sensitive_input

app = FastAPI(title="Bankwise API", version="0.2.0", description="Source-grounded fixed deposit decision support")
app.add_middleware(CORSMiddleware, allow_origins=CORS_ORIGINS, allow_credentials=False, allow_methods=["GET", "POST"], allow_headers=["*"])


def get_catalog():
    return BigQueryRepository()


def get_sessions():
    return FirestoreSessionRepository()


@app.get("/api/health", response_model=HealthResponse)
def health():
    return {"status": "healthy"}


@app.get("/api/products")
def list_products(category: str = "FD", amount: float = Query(default=None, gt=0),
                  tenure_months: int = Query(default=None, alias="tenureMonths", gt=0),
                  catalog: BigQueryRepository = Depends(get_catalog)):
    products = catalog.list_products(category=category.upper())
    return {"products": [product_payload(product, catalog, amount, tenure_months) for product in products]}


@app.get("/api/products/{product_id}")
def get_product(product_id: str, catalog: BigQueryRepository = Depends(get_catalog)):
    product = catalog.get_product(product_id)
    if not product:
        raise HTTPException(404, "Product not found")
    return product_payload(product, catalog)


@app.get("/api/products/{product_id}/sources")
def get_product_sources(product_id: str, catalog: BigQueryRepository = Depends(get_catalog)):
    product = catalog.get_product(product_id)
    if not product:
        raise HTTPException(404, "Product not found")
    return {"product_id": product_id, "sources": product_payload(product, catalog)["sources"]}


@app.post("/api/calculations/fd")
def calculate_fd_endpoint(request: FDCalculationRequest, catalog: BigQueryRepository = Depends(get_catalog)):
    if not request.product_id:
        raise HTTPException(422, "Calculations require a product_id so the rate and source can be verified")
    product = catalog.get_product(request.product_id, category="FD", status="ACTIVE")
    if not product:
        raise HTTPException(404, "FD product not found")
    matching = [rate for rate in product["rates"]
                if (rate.get("tenure_months") == request.tenure_months or (rate.get("tenure_months") is None
                    and (rate.get("tenure_min_months") is None or request.tenure_months >= rate["tenure_min_months"])
                    and (rate.get("tenure_max_months") is None or request.tenure_months <= rate["tenure_max_months"])))
                and (rate.get("min_amount") is None or request.principal >= rate["min_amount"])
                and (rate.get("max_amount") is None or request.principal <= rate["max_amount"])]
    if len(matching) != 1:
        raise HTTPException(422, "No unique rate matches the supplied amount and tenure")
    rate = matching[0]
    usable, reason = rate_is_usable(catalog, product["id"], rate)
    if not usable:
        raise HTTPException(409, "Calculation blocked: " + str(reason))
    from app.calculators.fd import CalculationError, calculate_fd
    if rate.get("payout_type", "").upper() != "CUMULATIVE":
        raise HTTPException(422, "Only cumulative payout calculations are currently supported")
    try:
        return calculate_fd(request.principal, rate["rate"], request.tenure_months, rate.get("compounding_frequency"))
    except CalculationError as exc:
        raise HTTPException(422, str(exc))


@app.post("/api/compare")
def compare_endpoint(request: CompareRequest, catalog: BigQueryRepository = Depends(get_catalog)):
    if request.requirements.amount is None or request.requirements.duration_months is None:
        raise HTTPException(422, "Amount and duration_months are required to compare products")
    return compare_products(catalog, request.product_ids, request.requirements.amount, request.requirements.duration_months)


@app.post("/api/decision")
async def decision(request: DecisionRequest, catalog: BigQueryRepository = Depends(get_catalog),
                   sessions: FirestoreSessionRepository = Depends(get_sessions)):
    safe_query = redact_sensitive_input(request.query)
    requirements = extract_requirements(safe_query)
    request_id = new_id("req")
    session_id = new_id("session")
    if requirements.missing_information:
        try:
            sessions.save_decision(session_id, requirements.model_dump(), [], requirements.missing_information)
            session_persisted = True
        except Exception:
            session_persisted = False
        return {"request_id": request_id, "session_id": session_id, "requirements": requirements.model_dump(),
                "products": [], "comparisons": [], "tradeoffs": [],
                "warnings": [] if session_persisted else ["Clarification state could not be persisted to Firestore."], "sources": [],
                "clarification_needed": requirements.missing_information,
                "ai": {"provider": "Google ADK + Gemini", "status": "clarification_required"},
                "session_persisted": session_persisted}
    product_ids = [product["id"] for product in catalog.list_products(category="FD")]
    result = compare_products(catalog, product_ids, requirements.amount, requirements.duration_months)
    explanation = await run_decision_agent(safe_query, requirements.model_dump(), result)
    try:
        sessions.save_decision(session_id, requirements.model_dump(), result["products"])
        session_persisted = True
    except Exception:
        session_persisted = False
        result["warnings"].append("Decision completed, but Firestore session persistence was unavailable.")
    ai_status = "completed" if explanation else ("unavailable" if GOOGLE_CLOUD_PROJECT else "not_configured")
    return {"request_id": request_id, "session_id": session_id, "requirements": requirements.model_dump(),
            "products": [item["product"] for item in result["products"]], "comparisons": result["products"],
            "tradeoffs": [item["tradeoff"] for item in result["products"] if item.get("tradeoff")],
            "warnings": result["warnings"],
            "sources": list({source["id"]: source for item in result["products"] for source in item["product"]["sources"]}.values()),
            "explanation": explanation,
            "ai": {"provider": "Google ADK + Gemini", "agent": "bankwise_decision_agent", "status": ai_status},
            "clarification_needed": [], "session_persisted": session_persisted}


@app.get("/api/sessions/{session_id}")
def get_decision_session(session_id: str, sessions: FirestoreSessionRepository = Depends(get_sessions)):
    session = sessions.get(session_id)
    if not session:
        raise HTTPException(404, "Decision session not found")
    return session


@app.post("/api/verification/run")
def verification_run(catalog: BigQueryRepository = Depends(get_catalog)):
    reports = []
    for product in catalog.list_products(category="FD", status="ACTIVE"):
        conflicts = catalog.get_conflicts(product["id"])
        for rate in product["rates"]:
            usable, reason = rate_is_usable(catalog, product["id"], rate)
            reports.append({"product_id": product["id"], "field": "rate", "rate_id": rate["id"],
                            "status": "HIGH" if usable else ("CONFLICT" if reason and "conflict" in reason.lower() else "LOW"), "notes": reason})
        for conflict in conflicts:
            reports.append({"product_id": product["id"], "field": conflict["field_name"], "status": "CONFLICT", "conflict_id": conflict["id"]})
        for source in product["sources"]:
            reports.append({"product_id": product["id"], "field": "source", "source_id": source["id"], "freshness": freshness(source)})
    return {"checked": len(reports), "records": reports, "web_fetch_performed": False}


@app.get("/api/agent/health")
def agent_health():
    from importlib.util import find_spec
    from app.config import GEMINI_MODEL
    def installed(module: str) -> bool:
        try:
            return find_spec(module) is not None
        except (ImportError, ModuleNotFoundError):
            return False
    return {"adk_configured": bool(GOOGLE_CLOUD_PROJECT and installed("google.adk")),
            "gemini_configured": bool(GOOGLE_CLOUD_PROJECT and installed("google.genai")),
            "bigquery_configured": bool(BIGQUERY_PROJECT and installed("google.cloud.bigquery")),
            "firestore_configured": bool(FIRESTORE_PROJECT and installed("google.cloud.firestore")),
            "model": GEMINI_MODEL}
