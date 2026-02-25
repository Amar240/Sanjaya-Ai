from __future__ import annotations

from contextlib import asynccontextmanager
import os

from fastapi import FastAPI, HTTPException

from .agents.advisor_agent import answer_advisor_question
from .agents.chat_workflow import run_chat_workflow
from .agents.workflow import LANGGRAPH_AVAILABLE, run_plan_workflow
from .data_loader import CatalogStore, DataValidationError, load_catalog_store
from .schemas.advisor import AdvisorRequest, AdvisorResponse
from .schemas.chat import ChatRequest, ChatResponse
from .schemas.plan import PlanRequest, PlanResponse

catalog_store: CatalogStore | None = None
startup_error: str | None = None


@asynccontextmanager
async def lifespan(_: FastAPI):
    global catalog_store
    global startup_error

    try:
        catalog_store = load_catalog_store()
        startup_error = None
    except (DataValidationError, FileNotFoundError) as exc:
        catalog_store = None
        startup_error = str(exc)
    yield


app = FastAPI(
    title="Sanjaya AI Backend",
    version="0.1.0",
    description="Grounded advising backend for role-to-skill-to-course planning.",
    lifespan=lifespan,
)


@app.get("/health")
def health() -> dict:
    return {
        "status": "ok" if catalog_store else "degraded",
        "startup_error": startup_error,
        "datasets_loaded": bool(catalog_store),
        "roles_source_file": catalog_store.roles_source_file if catalog_store else None,
        "counts": {
            "courses": len(catalog_store.courses) if catalog_store else 0,
            "course_skills": len(catalog_store.course_skills) if catalog_store else 0,
            "curated_role_skill_courses": len(catalog_store.curated_role_skill_courses)
            if catalog_store
            else 0,
            "fusion_roles": len(catalog_store.fusion_role_profiles) if catalog_store else 0,
            "roles_market": len(catalog_store.roles) if catalog_store else 0,
            "skills_market": len(catalog_store.skills) if catalog_store else 0,
            "evidence_links": len(catalog_store.evidence_links) if catalog_store else 0,
        },
        "workflow": {
            "langgraph_available": LANGGRAPH_AVAILABLE,
            "llm_provider": os.getenv("LLM_PROVIDER", "auto"),
            "openai_configured": bool(os.getenv("OPENAI_API_KEY", "").strip()),
            "groq_configured": bool(os.getenv("GROQ_API_KEY", "").strip()),
        },
    }


@app.get("/roles")
def roles() -> list[dict]:
    if not catalog_store:
        raise HTTPException(status_code=503, detail=startup_error or "Data store unavailable")
    fusion_role_ids = {profile.role_id for profile in catalog_store.fusion_role_profiles}
    return [
        {
            "role_id": role.role_id,
            "title": role.title,
            "market_grounding": role.market_grounding,
            "fusion_available": role.role_id in fusion_role_ids,
        }
        for role in catalog_store.roles
    ]


@app.post("/plan", response_model=PlanResponse)
def plan(request: PlanRequest) -> PlanResponse:
    if not catalog_store:
        raise HTTPException(status_code=503, detail=startup_error or "Data store unavailable")
    return run_plan_workflow(request, catalog_store)


@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
    if not catalog_store:
        raise HTTPException(status_code=503, detail=startup_error or "Data store unavailable")
    return run_chat_workflow(request, catalog_store)


@app.post("/advisor/ask", response_model=AdvisorResponse)
def advisor_ask(request: AdvisorRequest) -> AdvisorResponse:
    if not catalog_store:
        raise HTTPException(status_code=503, detail=startup_error or "Data store unavailable")
    return answer_advisor_question(request, catalog_store)
