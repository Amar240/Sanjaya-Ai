from __future__ import annotations

from collections import defaultdict
import json
import os
import re
import time
from urllib import error as urllib_error
from urllib import request as urllib_request

from ..data_loader import CatalogStore
from ..schemas.advisor import AdvisorCitation, AdvisorRequest, AdvisorResponse
from ..schemas.plan import CoursePurposeCard, EvidencePanelItem, PlanSemester


def answer_advisor_question(request: AdvisorRequest, store: CatalogStore) -> AdvisorResponse:
    question = request.question.strip()
    plan = request.plan
    intent = _detect_intent(question)
    tokens = _tokenize(question)

    course_card_by_id = {card.course_id: card for card in (plan.course_purpose_cards or [])}

    reasoning_points: list[str] = []
    citations: list[AdvisorCitation] = []
    answer = ""
    confidence = 0.55

    if intent == "why_role":
        answer, reasoning_points, citations, confidence = _answer_why_role(
            question=question,
            tokens=tokens,
            plan=plan,
        )
    elif intent == "why_course":
        answer, reasoning_points, citations, confidence = _answer_why_course(
            question=question,
            tokens=tokens,
            plan=plan,
            course_card_by_id=course_card_by_id,
        )
    elif intent == "feasibility":
        answer, reasoning_points, citations, confidence = _answer_feasibility(plan=plan)
    elif intent == "capability":
        answer, reasoning_points, citations, confidence = _answer_capability(
            question=question,
            plan=plan,
        )
    elif intent == "difficulty":
        answer, reasoning_points, citations, confidence = _answer_difficulty(plan=plan)
    elif intent == "alternatives":
        answer, reasoning_points, citations, confidence = _answer_alternatives(
            plan=plan,
            store=store,
        )
    elif intent == "next_best_action":
        answer, reasoning_points, citations, confidence = _answer_next_best_action(
            plan=plan,
            store=store,
        )
    else:
        answer, reasoning_points, citations, confidence = _answer_general(
            question=question,
            plan=plan,
        )

    used_llm = False
    llm_out, llm_error, llm_status = _llm_compose_answer(
        request=request,
        intent=intent,
        answer=answer,
        plan=plan,
        reasoning_points=reasoning_points,
        citations=citations,
    )
    if llm_out:
        answer = llm_out.get("answer", answer)
        llm_reasoning = llm_out.get("reasoning_points")
        if isinstance(llm_reasoning, list):
            reasoning_points = [str(item) for item in llm_reasoning if str(item).strip()][:6]
        llm_conf = llm_out.get("confidence")
        if isinstance(llm_conf, (int, float)):
            confidence = max(0.0, min(1.0, float(llm_conf)))
        used_llm = True
        llm_status = "used"

    return AdvisorResponse(
        intent=intent,
        answer=answer,
        reasoning_points=reasoning_points[:6],
        citations=_dedupe_citations(citations)[:10],
        confidence=max(0.0, min(1.0, confidence)),
        used_llm=used_llm,
        llm_status=llm_status,
        llm_error=llm_error,
    )


def _detect_intent(question: str) -> str:
    lower = question.lower()
    if re.search(r"\bwhy\b", lower) and (
        "role" in lower
        or "data engineer" in lower
        or "software engineer" in lower
        or "operations research" in lower
        or "selected" in lower
    ):
        return "why_role"
    if re.search(r"\bwhy\b", lower) and (
        re.search(r"\b[A-Z]{2,5}-\d{3}[A-Z]?\b", question) is not None
        or "course" in lower
    ):
        return "why_course"
    if any(term in lower for term in ("feasible", "prereq", "prerequisite", "credit", "semester", "load")):
        return "feasibility"
    if any(
        term in lower
        for term in (
            "am i capable",
            "capable",
            "am i ready",
            "ready for",
            "fit for",
            "can i handle",
            "can i do",
        )
    ):
        return "capability"
    if any(
        term in lower
        for term in (
            "difficulty",
            "difficult",
            "hard",
            "easy",
            "challenging",
            "how tough",
            "workload",
        )
    ):
        return "difficulty"
    if any(term in lower for term in ("alternative", "other role", "another role", "instead")):
        return "alternatives"
    if any(
        term in lower
        for term in (
            "next step",
            "what next",
            "next action",
            "how should i prepare",
            "how do i improve",
            "what should i do next",
        )
    ):
        return "next_best_action"
    if any(term in lower for term in ("why this plan", "defend", "justify")):
        return "why_role"
    return "general"


def _answer_why_role(
    question: str,
    tokens: set[str],
    plan,
) -> tuple[str, list[str], list[AdvisorCitation], float]:
    total = len(plan.skill_coverage)
    covered = sum(1 for item in plan.skill_coverage if item.covered)
    coverage_pct = int(round((covered / total) * 100)) if total else 0

    covered_skills = [item for item in plan.skill_coverage if item.covered]
    covered_skills.sort(key=lambda item: len(item.matched_courses), reverse=True)
    top_skills = covered_skills[:3]

    reasoning = [
        f"The selected role is {plan.selected_role_title} ({plan.selected_role_id}), and your plan currently covers {covered}/{total} required skills ({coverage_pct}%).",
        "The roadmap is prerequisite-safe in this plan result (no structural validation errors).",
    ]
    if top_skills:
        summary = ", ".join(
            f"{item.required_skill_id} via {', '.join(item.matched_courses[:2])}"
            for item in top_skills
        )
        reasoning.append(f"Strongest mapped skills include {summary}.")

    citations: list[AdvisorCitation] = []
    for item in top_skills:
        citations.append(
            AdvisorCitation(
                citation_type="skill_coverage",
                label=item.required_skill_id,
                detail=f"Mapped courses: {', '.join(item.matched_courses[:5]) or 'none'}",
            )
        )

    evidence = _rank_evidence(plan.evidence_panel or [], tokens)
    if not evidence and plan.evidence_panel:
        evidence = list(plan.evidence_panel[:3])
    for item in evidence[:4]:
        citations.append(_citation_from_evidence(item))

    for note in plan.notes:
        if "Credit policy applied" in note or "Plan-specific external prerequisite references" in note:
            citations.append(_citation_from_note(note))

    answer = (
        f"Based on your current profile and constraints, {plan.selected_role_title} is defensible because the plan shows high required-skill coverage and maintains feasibility checks."
    )
    if "data engineer" in question.lower() and plan.selected_role_title.lower() != "data engineer":
        answer += (
            f" Your current run selected {plan.selected_role_title}; if you want, we can rerun with preferred_role_id set to ROLE_DATA_ENGINEER and compare both side by side."
        )
    return answer, reasoning, citations, 0.86


def _answer_why_course(
    question: str,
    tokens: set[str],
    plan,
    course_card_by_id: dict[str, CoursePurposeCard],
) -> tuple[str, list[str], list[AdvisorCitation], float]:
    course_ids = re.findall(r"\b[A-Z]{2,5}-\d{3}[A-Z]?\b", question.upper())
    if course_ids:
        course_id = course_ids[0]
    else:
        course_id = _best_matching_course_from_question(question, course_card_by_id)

    if not course_id or course_id not in course_card_by_id:
        answer = (
            "I do not see that course in the current roadmap output. Ask with a planned course ID (for example CISC-275) and I will defend it with mapped skills and evidence."
        )
        return answer, ["No matching planned course found in current plan context."], [], 0.48

    card = course_card_by_id[course_id]
    reasoning = [card.why_this_course]
    if card.satisfied_skills:
        reasoning.append(
            f"Mapped role skills for this course: {', '.join(card.satisfied_skills)}."
        )
    else:
        reasoning.append("This course is currently included as prerequisite/support feasibility, not direct role-skill coverage.")

    citations: list[AdvisorCitation] = [
        _citation_from_course_card(card),
    ]
    for ev in card.evidence[:3]:
        citations.append(_citation_from_evidence(ev))

    if not card.evidence:
        ranked_ev = _rank_evidence(plan.evidence_panel or [], tokens)
        for item in ranked_ev[:2]:
            citations.append(_citation_from_evidence(item))

    answer = (
        f"{course_id} is in your roadmap because it supports the selected role path through mapped skills and/or prerequisite feasibility. "
        "The reasoning and evidence references are listed below."
    )
    return answer, reasoning, citations, 0.82


def _answer_feasibility(plan) -> tuple[str, list[str], list[AdvisorCitation], float]:
    reasoning: list[str] = []
    citations: list[AdvisorCitation] = []

    if plan.validation_errors:
        reasoning.append(
            f"The current plan has {len(plan.validation_errors)} validation error(s), so feasibility is not fully satisfied yet."
        )
    else:
        reasoning.append("The verifier reports no structural validation errors for this roadmap.")

    underloaded = [sem for sem in plan.semesters if sem.total_credits < 12 and sem.term in {"Fall", "Spring"}]
    if underloaded:
        reasoning.append(
            f"{len(underloaded)} regular term(s) are below full-time threshold and already flagged in warnings."
        )
    else:
        reasoning.append("Regular terms in this output meet the full-time credit policy requirements.")

    for sem in plan.semesters[:4]:
        citations.append(_citation_from_semester(sem))

    for note in plan.notes:
        if "Credit policy applied" in note or "Plan-specific external prerequisite references" in note:
            citations.append(_citation_from_note(note))

    answer = (
        "From a planning-constraint perspective, this roadmap is feasible in the current output. "
        "You should still confirm department scheduling and advisor-specific policies before final registration."
    )
    return answer, reasoning, citations, 0.88


def _answer_capability(
    question: str,
    plan,
) -> tuple[str, list[str], list[AdvisorCitation], float]:
    total = len(plan.skill_coverage)
    covered = sum(1 for item in plan.skill_coverage if item.covered)
    coverage_pct = int(round((covered / total) * 100)) if total else 0
    has_errors = bool(plan.validation_errors)
    regular_underloaded = [
        sem for sem in plan.semesters if sem.term in {"Fall", "Spring"} and sem.total_credits < 12
    ]

    hardest_semester = max(
        plan.semesters,
        key=lambda sem: (_semester_difficulty_score(sem), sem.semester_index),
        default=None,
    )
    hardest_label = (
        f"Semester {hardest_semester.semester_index} ({hardest_semester.term})"
        if hardest_semester
        else "N/A"
    )

    readiness = "strong"
    if coverage_pct < 75 or has_errors:
        readiness = "moderate"
    if coverage_pct < 50:
        readiness = "early"

    reasoning = [
        f"Current skill readiness for {plan.selected_role_title}: {covered}/{total} required skills covered ({coverage_pct}%).",
        "The verifier reports no structural errors." if not has_errors else f"The plan currently has {len(plan.validation_errors)} validation error(s).",
        f"Highest workload concentration appears in {hardest_label}.",
    ]
    if regular_underloaded:
        reasoning.append(
            f"{len(regular_underloaded)} regular semester(s) are under full-time load and may need advising alignment."
        )
    if "difficulty" in question.lower() or "hard" in question.lower():
        reasoning.append("Difficulty is manageable when prerequisites and term load remain as planned.")

    citations: list[AdvisorCitation] = []
    for item in sorted(plan.skill_coverage, key=lambda row: len(row.matched_courses), reverse=True)[:3]:
        citations.append(
            AdvisorCitation(
                citation_type="skill_coverage",
                label=item.required_skill_id,
                detail=f"Mapped courses: {', '.join(item.matched_courses[:5]) or 'none'}",
            )
        )
    if hardest_semester:
        citations.append(_citation_from_semester(hardest_semester))
    for note in plan.notes:
        if "Credit policy applied" in note or "Plan-specific external prerequisite references" in note:
            citations.append(_citation_from_note(note))

    answer = (
        f"You are in a {readiness} position for this role based on current coverage and feasibility checks. "
        "The roadmap is achievable if you stay on the planned prerequisite sequence and term load."
    )
    return answer, reasoning, citations, 0.84


def _answer_difficulty(plan) -> tuple[str, list[str], list[AdvisorCitation], float]:
    if not plan.semesters:
        return (
            "I cannot assess difficulty because no semesters were generated yet.",
            ["No semester data in current plan output."],
            [],
            0.35,
        )

    scored = [
        (_semester_difficulty_score(sem), sem)
        for sem in plan.semesters
    ]
    scored.sort(key=lambda row: (-row[0], row[1].semester_index))
    hardest_score, hardest = scored[0]
    avg_score = sum(score for score, _ in scored) / len(scored)

    if avg_score >= 7.0:
        level = "high"
    elif avg_score >= 4.5:
        level = "moderate"
    else:
        level = "low"

    reasoning = [
        f"Overall difficulty is estimated as {level} based on credits, course count, warning load, and upper-level course mix.",
        (
            f"Most demanding term is Semester {hardest.semester_index} ({hardest.term}) "
            f"with score {hardest_score:.1f}."
        ),
        "Difficulty can be reduced by smoothing heavy semesters and avoiding prerequisite bottlenecks.",
    ]

    citations: list[AdvisorCitation] = []
    for _, semester in scored[:3]:
        citations.append(_citation_from_semester(semester))
    for note in plan.notes:
        if "Credit policy applied" in note:
            citations.append(_citation_from_note(note))

    answer = (
        f"This roadmap has {level} difficulty overall. "
        f"The heaviest pressure point is Semester {hardest.semester_index} ({hardest.term})."
    )
    return answer, reasoning, citations, 0.79


def _answer_next_best_action(
    plan,
    store: CatalogStore,
) -> tuple[str, list[str], list[AdvisorCitation], float]:
    uncovered = [item for item in plan.skill_coverage if not item.covered]
    reasoning: list[str] = []
    citations: list[AdvisorCitation] = []

    if uncovered:
        next_skill = uncovered[0]
        reasoning.append(
            f"Highest immediate gap is {next_skill.required_skill_id}; close it first to increase role readiness."
        )
        citations.append(
            AdvisorCitation(
                citation_type="skill_coverage",
                label=next_skill.required_skill_id,
                detail="Currently uncovered in plan skill coverage.",
            )
        )
    else:
        reasoning.append("All required role skills are currently covered in this plan.")

    nearest_sem = min(
        plan.semesters,
        key=lambda sem: sem.semester_index,
        default=None,
    )
    if nearest_sem:
        reasoning.append(
            f"Execution focus: complete Semester {nearest_sem.semester_index} on schedule and re-evaluate after that term."
        )
        citations.append(_citation_from_semester(nearest_sem))

    role = store.roles_by_id.get(plan.selected_role_id)
    if role and role.portfolio_expectations:
        reasoning.append(
            f"Portfolio milestone: {role.portfolio_expectations[0]}."
        )
        citations.append(
            AdvisorCitation(
                citation_type="policy_note",
                label="Portfolio expectation",
                detail=role.portfolio_expectations[0],
            )
        )

    answer = (
        "Next best action: execute the upcoming semester cleanly, then close remaining skill gaps (if any) and complete one portfolio milestone aligned to your selected role."
    )
    return answer, reasoning, citations, 0.76


def _answer_alternatives(
    plan,
    store: CatalogStore,
) -> tuple[str, list[str], list[AdvisorCitation], float]:
    covered_skill_ids = {item.required_skill_id for item in plan.skill_coverage if item.covered}
    scored_roles = []
    for role in store.roles:
        if role.role_id == plan.selected_role_id:
            continue
        required = {req.skill_id for req in role.required_skills}
        overlap = len(required & covered_skill_ids)
        if overlap <= 0:
            continue
        score = overlap / max(1, len(required))
        scored_roles.append((score, overlap, role))

    scored_roles.sort(key=lambda row: (-row[0], -row[1], row[2].role_id))
    top = scored_roles[:3]

    if not top:
        answer = "I do not have strong alternative matches from current covered skills yet."
        return answer, ["No high-overlap alternatives identified from current skill coverage."], [], 0.5

    suggestions = ", ".join(f"{item[2].title} ({item[2].role_id})" for item in top)
    reasoning = [
        f"Alternatives are ranked by overlap between your currently covered skills and each role's required skills.",
        f"Top alternatives from current plan context: {suggestions}.",
    ]

    citations: list[AdvisorCitation] = []
    for item in top:
        role = item[2]
        citations.append(
            AdvisorCitation(
                citation_type="skill_coverage",
                label=role.role_id,
                detail=f"Overlap score: {item[0]:.2f} ({item[1]} overlapping required skills).",
            )
        )

    answer = (
        "Yes, you have nearby alternatives. I ranked them by required-skill overlap with your current covered-skill set, so you can pivot with less additional coursework."
    )
    return answer, reasoning, citations, 0.74


def _answer_general(question: str, plan) -> tuple[str, list[str], list[AdvisorCitation], float]:
    total = len(plan.skill_coverage)
    covered = sum(1 for item in plan.skill_coverage if item.covered)
    reasoning = [
        f"Current selected role: {plan.selected_role_title} ({plan.selected_role_id}).",
        f"Skill coverage in this plan: {covered}/{total}.",
        f"Semesters planned: {len(plan.semesters)}.",
    ]
    citations: list[AdvisorCitation] = []
    for note in plan.notes[:3]:
        citations.append(_citation_from_note(note))
    answer = (
        "I can defend this roadmap with evidence and constraints. Ask targeted questions like 'Why this role?', 'Am I capable for this path?', 'How difficult is this roadmap?', or 'What should I do next?'."
    )
    return answer, reasoning, citations, 0.68


def _best_matching_course_from_question(
    question: str,
    course_card_by_id: dict[str, CoursePurposeCard],
) -> str | None:
    tokens = _tokenize(question)
    best_course = None
    best_score = 0
    for course_id, card in course_card_by_id.items():
        text = f"{course_id} {card.course_title} {card.why_this_course}"
        score = len(tokens & _tokenize(text))
        if score > best_score:
            best_score = score
            best_course = course_id
    return best_course


def _rank_evidence(
    evidence_items: list[EvidencePanelItem],
    question_tokens: set[str],
) -> list[EvidencePanelItem]:
    scored = []
    for item in evidence_items:
        text = f"{item.skill_name} {item.snippet} {item.source_title}"
        tokens = _tokenize(text)
        overlap = len(tokens & question_tokens)
        confidence = float(item.confidence or 0.0)
        score = overlap * 3.0 + confidence
        scored.append((score, confidence, item))
    scored.sort(key=lambda row: (-row[0], -row[1], row[2].source_id))
    positive = [item for score, _, item in scored if score > 0]
    return positive or [row[2] for row in scored]


def _citation_from_evidence(item: EvidencePanelItem) -> AdvisorCitation:
    return AdvisorCitation(
        citation_type="evidence_source",
        label=f"{item.skill_name} via {item.source_provider}",
        detail=item.snippet,
        source_url=item.source_url,
    )


def _citation_from_course_card(card: CoursePurposeCard) -> AdvisorCitation:
    return AdvisorCitation(
        citation_type="course",
        label=f"{card.course_id} - {card.course_title}",
        detail=card.why_this_course,
    )


def _citation_from_note(note: str) -> AdvisorCitation:
    return AdvisorCitation(
        citation_type="policy_note",
        label="Planner note",
        detail=note,
    )


def _citation_from_semester(semester: PlanSemester) -> AdvisorCitation:
    detail = (
        f"Term={semester.term}, credits={semester.total_credits}, courses={', '.join(semester.courses[:6])}"
    )
    return AdvisorCitation(
        citation_type="semester",
        label=f"Semester {semester.semester_index}",
        detail=detail,
    )


def _semester_difficulty_score(semester: PlanSemester) -> float:
    advanced_courses = sum(
        1 for cid in semester.courses if (_course_number(cid) or 0) >= 300
    )
    return (
        float(semester.total_credits) * 0.35
        + len(semester.courses) * 0.9
        + len(semester.warnings) * 1.8
        + advanced_courses * 0.8
    )


def _course_number(course_id: str) -> int | None:
    match = re.search(r"-(\d{3})", course_id)
    if not match:
        return None
    return int(match.group(1))


def _tokenize(text: str) -> set[str]:
    return set(re.findall(r"[a-z0-9]+", text.lower()))


def _dedupe_citations(citations: list[AdvisorCitation]) -> list[AdvisorCitation]:
    unique: dict[tuple[str, str, str], AdvisorCitation] = {}
    for item in citations:
        key = (item.citation_type, item.label, item.detail)
        if key not in unique:
            unique[key] = item
    return list(unique.values())


def _plan_context_for_llm(plan) -> dict:
    covered = sum(1 for item in plan.skill_coverage if item.covered)
    total = len(plan.skill_coverage)
    top_skills = sorted(
        plan.skill_coverage,
        key=lambda item: (item.covered, len(item.matched_courses)),
        reverse=True,
    )[:5]
    return {
        "selected_role_id": plan.selected_role_id,
        "selected_role_title": plan.selected_role_title,
        "skill_coverage_ratio": f"{covered}/{total}",
        "skill_coverage": [
            {
                "skill_id": item.required_skill_id,
                "covered": item.covered,
                "matched_courses": item.matched_courses[:4],
            }
            for item in top_skills
        ],
        "semesters": [
            {
                "semester_index": sem.semester_index,
                "term": sem.term,
                "credits": sem.total_credits,
                "warnings": sem.warnings[:3],
            }
            for sem in plan.semesters[:8]
        ],
        "validation_errors": plan.validation_errors[:6],
        "notes": plan.notes[:8],
    }


def _resolve_llm_target(task: str) -> tuple[str | None, str, str, str]:
    provider_pref = os.getenv("LLM_PROVIDER", "auto").strip().lower()
    openai_key = os.getenv("OPENAI_API_KEY", "").strip()
    groq_key = os.getenv("GROQ_API_KEY", "").strip()

    if task == "advisor":
        openai_model = (
            os.getenv("OPENAI_MODEL_ADVISOR", "").strip()
            or os.getenv("OPENAI_MODEL", "").strip()
            or "gpt-4o-mini"
        )
        groq_model = (
            os.getenv("GROQ_MODEL_ADVISOR", "").strip()
            or os.getenv("GROQ_MODEL", "").strip()
            or "llama-3.3-70b-versatile"
        )
    else:
        openai_model = os.getenv("OPENAI_MODEL", "").strip() or "gpt-4o-mini"
        groq_model = os.getenv("GROQ_MODEL", "").strip() or "llama-3.3-70b-versatile"

    if provider_pref == "openai":
        if openai_key:
            return "openai", openai_key, openai_model, "https://api.openai.com/v1/chat/completions"
        return None, "", "", ""
    if provider_pref == "groq":
        if groq_key:
            return "groq", groq_key, groq_model, "https://api.groq.com/openai/v1/chat/completions"
        return None, "", "", ""

    if openai_key:
        return "openai", openai_key, openai_model, "https://api.openai.com/v1/chat/completions"
    if groq_key:
        return "groq", groq_key, groq_model, "https://api.groq.com/openai/v1/chat/completions"
    return None, "", "", ""


def _llm_compose_answer(
    request: AdvisorRequest,
    intent: str,
    answer: str,
    plan,
    reasoning_points: list[str],
    citations: list[AdvisorCitation],
) -> tuple[dict | None, str | None, str]:
    provider, api_key, model, endpoint = _resolve_llm_target(task="advisor")
    if not provider:
        return None, None, "disabled"
    system_prompt = (
        "You are Sanjaya AI, a grounded academic advisor assistant. "
        "Compose a fresh, human-friendly answer using ONLY the provided context. "
        "Do not add new facts, no job guarantees, no fabricated courses, no fabricated requirements. "
        "If context is insufficient, state limits clearly. "
        "Return strict JSON only."
    )
    user_payload = {
        "tone": request.tone,
        "intent": intent,
        "question": request.question,
        "deterministic_answer": answer,
        "plan_context": _plan_context_for_llm(plan),
        "reasoning_points": reasoning_points,
        "citations": [item.model_dump() for item in citations[:8]],
        "writing_rules": [
            "Write a fresh response; do not simply copy deterministic_answer.",
            "Address the student's question directly in first sentence.",
            "Use 3-6 sentences in friendly mode, 2-4 in concise mode.",
            "Stay factual and grounded to provided context."
        ],
        "required_output_schema": {
            "answer": "string",
            "reasoning_points": ["string"],
            "confidence": "float_0_to_1",
        },
    }
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": json.dumps(user_payload, ensure_ascii=True)},
        ],
        "temperature": 0.45,
        "max_tokens": 900,
        "response_format": {"type": "json_object"},
    }
    raw = json.dumps(payload).encode("utf-8")
    req = urllib_request.Request(
        url=endpoint,
        data=raw,
        method="POST",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
    )
    retries = 2
    transient_http_codes = {408, 409, 425, 429, 500, 502, 503, 504}
    last_error: str | None = None

    for attempt in range(retries + 1):
        try:
            with urllib_request.urlopen(req, timeout=60) as response:
                text = response.read().decode("utf-8")
        except urllib_error.HTTPError as exc:
            last_error = f"{provider}_http_{exc.code}"
            if exc.code in transient_http_codes and attempt < retries:
                time.sleep(1.2 * (attempt + 1))
                continue
            return None, last_error, "fallback"
        except urllib_error.URLError:
            last_error = f"{provider}_network_error"
            if attempt < retries:
                time.sleep(1.0 * (attempt + 1))
                continue
            return None, last_error, "fallback"
        except TimeoutError:
            last_error = f"{provider}_timeout"
            if attempt < retries:
                time.sleep(1.5 * (attempt + 1))
                continue
            return None, last_error, "fallback"

        try:
            parsed = json.loads(text)
            content = (
                parsed.get("choices", [{}])[0]
                .get("message", {})
                .get("content", "")
            )
            out: dict | None = None
            if isinstance(content, str):
                try:
                    candidate = json.loads(content)
                    if isinstance(candidate, dict):
                        out = candidate
                except Exception:
                    match = re.search(r"\{.*\}", content, flags=re.DOTALL)
                    if match:
                        candidate = json.loads(match.group(0))
                        if isinstance(candidate, dict):
                            out = candidate

            if isinstance(out, dict):
                return out, None, "used"

            last_error = f"{provider}_invalid_json_payload"
            if attempt < retries:
                time.sleep(0.8 * (attempt + 1))
                continue
            return None, last_error, "fallback"
        except Exception:
            last_error = f"{provider}_response_parse_failed"
            if attempt < retries:
                time.sleep(0.8 * (attempt + 1))
                continue
            return None, last_error, "fallback"
    return None, last_error or f"{provider}_unknown_error", "fallback"
