from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from .plan import PlanResponse


class AdvisorRequest(BaseModel):
    question: str = Field(min_length=1, max_length=4000)
    plan: PlanResponse
    tone: Literal["friendly", "concise"] = "friendly"


class AdvisorCitation(BaseModel):
    citation_type: Literal[
        "evidence_source",
        "course",
        "policy_note",
        "skill_coverage",
        "semester",
    ]
    label: str
    detail: str
    source_url: str | None = None


class AdvisorResponse(BaseModel):
    intent: str
    answer: str
    reasoning_points: list[str] = Field(default_factory=list)
    citations: list[AdvisorCitation] = Field(default_factory=list)
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    used_llm: bool = False
    llm_status: Literal["used", "fallback", "disabled"] = "disabled"
    llm_error: str | None = None
