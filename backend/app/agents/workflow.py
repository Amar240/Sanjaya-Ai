from __future__ import annotations

from typing import TypedDict

from ..data_loader import CatalogStore
from ..rag import MarketEvidenceRetriever
from ..schemas.plan import PlanRequest, PlanResponse
from .planner import build_plan

try:
    from langgraph.graph import END, StateGraph

    LANGGRAPH_AVAILABLE = True
except Exception:  # pragma: no cover - optional dependency guard
    END = "__end__"
    StateGraph = None
    LANGGRAPH_AVAILABLE = False


class WorkflowState(TypedDict, total=False):
    request: PlanRequest
    selected_role_id: str
    candidate_role_ids: list[str]
    draft_plan: PlanResponse
    validation_errors: list[str]
    retries: int
    retry_required: bool
    agent_trace: list[str]


_RETRIEVER_CACHE: dict[int, MarketEvidenceRetriever] = {}


def run_plan_workflow(request: PlanRequest, store: CatalogStore) -> PlanResponse:
    retriever = _get_retriever(store)
    if LANGGRAPH_AVAILABLE and StateGraph is not None:
        return _run_langgraph(request, store, retriever)
    return _run_fallback(request, store, retriever)


def _run_langgraph(
    request: PlanRequest,
    store: CatalogStore,
    retriever: MarketEvidenceRetriever,
) -> PlanResponse:
    graph = StateGraph(WorkflowState)

    def intake_node(state: WorkflowState) -> dict:
        trace = list(state.get("agent_trace", []))
        trace.append("intake: normalized student profile into planner state")
        return {"agent_trace": trace}

    def role_retrieval_node(state: WorkflowState) -> dict:
        trace = list(state.get("agent_trace", []))
        selected_role_id, candidates = _resolve_role_candidates(state["request"], store, retriever)
        trace.append(
            f"role_retrieval: selected {selected_role_id} from {len(candidates)} candidates"
        )
        return {
            "selected_role_id": selected_role_id,
            "candidate_role_ids": candidates,
            "agent_trace": trace,
        }

    def planner_node(state: WorkflowState) -> dict:
        trace = list(state.get("agent_trace", []))
        plan_request = state["request"].model_copy(deep=True)
        plan_request.preferred_role_id = state.get("selected_role_id")
        draft_plan = build_plan(plan_request, store)
        trace.append(
            f"planner: produced {len(draft_plan.semesters)} semesters with "
            f"{len(draft_plan.validation_errors)} validation errors"
        )
        return {
            "draft_plan": draft_plan,
            "validation_errors": list(draft_plan.validation_errors),
            "agent_trace": trace,
        }

    def verifier_node(state: WorkflowState) -> dict:
        trace = list(state.get("agent_trace", []))
        retries = int(state.get("retries", 0))
        errors = list(state.get("validation_errors", []))

        if errors and retries < 1:
            patched = state["request"].model_copy(deep=True)
            patched.student_profile.include_optional_terms = True
            trace.append(
                "verifier: errors detected, retrying planner with optional terms enabled"
            )
            return {
                "request": patched,
                "retries": retries + 1,
                "retry_required": True,
                "agent_trace": trace,
            }

        if errors:
            trace.append("verifier: errors remain after retry budget exhausted")
        else:
            trace.append("verifier: plan passed structural validation checks")
        return {"retry_required": False, "agent_trace": trace}

    def evidence_node(state: WorkflowState) -> dict:
        trace = list(state.get("agent_trace", []))
        draft = state["draft_plan"]
        role = store.roles_by_id[draft.selected_role_id]

        evidence_panel = retriever.retrieve_role_evidence(role=role, top_k=10)
        course_cards = retriever.build_course_purpose_cards(
            plan=draft,
            role=role,
            evidence_panel=evidence_panel,
        )
        draft.evidence_panel = evidence_panel
        draft.course_purpose_cards = course_cards
        vector_status = "enabled" if retriever.using_chroma else "fallback_lexical"
        trace.append(f"evidence: attached {len(evidence_panel)} evidence snippets via {vector_status}")
        draft.agent_trace = trace
        return {"draft_plan": draft, "agent_trace": trace}

    def verifier_route(state: WorkflowState) -> str:
        return "retry" if state.get("retry_required") else "evidence"

    graph.add_node("intake", intake_node)
    graph.add_node("role_retrieval", role_retrieval_node)
    graph.add_node("planner", planner_node)
    graph.add_node("verifier", verifier_node)
    graph.add_node("evidence", evidence_node)

    graph.set_entry_point("intake")
    graph.add_edge("intake", "role_retrieval")
    graph.add_edge("role_retrieval", "planner")
    graph.add_edge("planner", "verifier")
    graph.add_conditional_edges(
        "verifier",
        verifier_route,
        {"retry": "planner", "evidence": "evidence"},
    )
    graph.add_edge("evidence", END)

    compiled = graph.compile()
    out = compiled.invoke(
        {
            "request": request,
            "retries": 0,
            "retry_required": False,
            "agent_trace": [],
        }
    )
    return out["draft_plan"]


def _run_fallback(
    request: PlanRequest,
    store: CatalogStore,
    retriever: MarketEvidenceRetriever,
) -> PlanResponse:
    state: WorkflowState = {
        "request": request,
        "retries": 0,
        "agent_trace": [],
    }
    state["agent_trace"].append(
        "workflow: langgraph unavailable, using deterministic sequential fallback"
    )

    selected_role_id, candidates = _resolve_role_candidates(request, store, retriever)
    state["selected_role_id"] = selected_role_id
    state["candidate_role_ids"] = candidates
    state["agent_trace"].append(
        f"role_retrieval: selected {selected_role_id} from {len(candidates)} candidates"
    )

    max_retries = 1
    while True:
        plan_request = state["request"].model_copy(deep=True)
        plan_request.preferred_role_id = state["selected_role_id"]
        draft_plan = build_plan(plan_request, store)
        state["draft_plan"] = draft_plan
        state["validation_errors"] = list(draft_plan.validation_errors)
        state["agent_trace"].append(
            f"planner: produced {len(draft_plan.semesters)} semesters with "
            f"{len(draft_plan.validation_errors)} validation errors"
        )

        errors = state["validation_errors"]
        retries = int(state.get("retries", 0))
        if errors and retries < max_retries:
            patched = state["request"].model_copy(deep=True)
            patched.student_profile.include_optional_terms = True
            state["request"] = patched
            state["retries"] = retries + 1
            state["agent_trace"].append(
                "verifier: errors detected, retrying planner with optional terms enabled"
            )
            continue
        break

    role = store.roles_by_id[state["draft_plan"].selected_role_id]
    evidence_panel = retriever.retrieve_role_evidence(role=role, top_k=10)
    course_cards = retriever.build_course_purpose_cards(
        plan=state["draft_plan"],
        role=role,
        evidence_panel=evidence_panel,
    )
    state["draft_plan"].evidence_panel = evidence_panel
    state["draft_plan"].course_purpose_cards = course_cards
    vector_status = "enabled" if retriever.using_chroma else "fallback_lexical"
    state["agent_trace"].append(
        f"evidence: attached {len(evidence_panel)} evidence snippets via {vector_status}"
    )
    state["draft_plan"].agent_trace = state["agent_trace"]
    return state["draft_plan"]


def _resolve_role_candidates(
    request: PlanRequest,
    store: CatalogStore,
    retriever: MarketEvidenceRetriever,
) -> tuple[str, list[str]]:
    fusion_role_ids = {profile.role_id for profile in store.fusion_role_profiles}
    if request.student_profile.mode == "FUSION" and fusion_role_ids:
        preferred = request.preferred_role_id
        candidates = [
            role_id
            for role_id in retriever.retrieve_roles_by_interest(
                request.student_profile.interests, top_k=8
            )
            if role_id in fusion_role_ids
        ]
        if not candidates:
            candidates = sorted(fusion_role_ids)[:5]

        if preferred and preferred in fusion_role_ids:
            ordered = [preferred] + [role_id for role_id in candidates if role_id != preferred]
            return preferred, ordered

        return candidates[0], candidates

    preferred = request.preferred_role_id
    if preferred and preferred in store.roles_by_id:
        candidates = [preferred]
        from_interests = retriever.retrieve_roles_by_interest(
            request.student_profile.interests, top_k=5
        )
        for role_id in from_interests:
            if role_id not in candidates:
                candidates.append(role_id)
        return preferred, candidates

    candidates = retriever.retrieve_roles_by_interest(
        request.student_profile.interests, top_k=5
    )
    if not candidates:
        candidates = [role.role_id for role in store.roles[:5]]
    return candidates[0], candidates


def _get_retriever(store: CatalogStore) -> MarketEvidenceRetriever:
    cache_key = id(store)
    retriever = _RETRIEVER_CACHE.get(cache_key)
    if retriever is None:
        retriever = MarketEvidenceRetriever(store)
        _RETRIEVER_CACHE[cache_key] = retriever
    return retriever
