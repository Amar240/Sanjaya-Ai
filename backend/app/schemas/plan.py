from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

ProgramLevel = Literal["UG", "GR"]
PlanMode = Literal["CORE", "FUSION"]
Term = Literal["Fall", "Spring", "Summer", "Winter"]


class StudentProfile(BaseModel):
    level: ProgramLevel
    mode: PlanMode = "CORE"
    fusion_domain: str | None = None
    current_semester: int = Field(ge=1, le=12)
    start_term: Term = "Fall"
    include_optional_terms: bool = False
    completed_courses: list[str] = Field(default_factory=list)
    min_credits: int = Field(default=12, ge=0, le=30)
    target_credits: int = Field(default=15, ge=0, le=30)
    max_credits: int = Field(default=17, ge=0, le=30)
    interests: list[str] = Field(default_factory=list)


class PlanRequest(BaseModel):
    student_profile: StudentProfile
    preferred_role_id: str | None = None


class SkillCoverage(BaseModel):
    required_skill_id: str
    covered: bool
    matched_courses: list[str] = Field(default_factory=list)


class PlanSemester(BaseModel):
    semester_index: int
    term: Term = "Fall"
    courses: list[str] = Field(default_factory=list)
    total_credits: float = 0
    warnings: list[str] = Field(default_factory=list)


class EvidencePanelItem(BaseModel):
    role_id: str
    skill_id: str
    skill_name: str
    source_id: str
    source_provider: str
    source_title: str
    source_url: str
    snippet: str
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)


class CoursePurposeCard(BaseModel):
    course_id: str
    course_title: str
    why_this_course: str
    satisfied_skills: list[str] = Field(default_factory=list)
    evidence: list[EvidencePanelItem] = Field(default_factory=list)


class FusionReadiness(BaseModel):
    domain_ready_pct: float = Field(ge=0.0, le=1.0)
    tech_ready_pct: float = Field(ge=0.0, le=1.0)
    overall_fit_pct: float = Field(ge=0.0, le=1.0)


class FusionUnlockSkillStatus(BaseModel):
    skill_id: str
    reason: str
    covered: bool
    matched_courses: list[str] = Field(default_factory=list)


class FusionSummary(BaseModel):
    domain: str
    domain_weight: float = Field(ge=0.0, le=1.0)
    tech_weight: float = Field(ge=0.0, le=1.0)
    domain_skill_coverage: list[SkillCoverage] = Field(default_factory=list)
    tech_skill_coverage: list[SkillCoverage] = Field(default_factory=list)
    unlock_skills: list[FusionUnlockSkillStatus] = Field(default_factory=list)
    readiness: FusionReadiness


class PlanResponse(BaseModel):
    selected_role_id: str
    selected_role_title: str
    skill_coverage: list[SkillCoverage] = Field(default_factory=list)
    semesters: list[PlanSemester] = Field(default_factory=list)
    validation_errors: list[str] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)
    evidence_panel: list[EvidencePanelItem] = Field(default_factory=list)
    course_purpose_cards: list[CoursePurposeCard] = Field(default_factory=list)
    fusion_summary: FusionSummary | None = None
    agent_trace: list[str] = Field(default_factory=list)
