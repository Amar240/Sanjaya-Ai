from __future__ import annotations

import hashlib
import math
import re
from collections import defaultdict

from ..data_loader import CatalogStore
from ..schemas.catalog import RoleMarket
from ..schemas.plan import CoursePurposeCard, EvidencePanelItem, PlanResponse

try:
    from langchain_core.documents import Document
    from langchain_core.embeddings import Embeddings

    LANGCHAIN_CORE_AVAILABLE = True
except Exception:  # pragma: no cover - optional dependency guard
    Document = None
    LANGCHAIN_CORE_AVAILABLE = False

    class Embeddings:  # type: ignore[no-redef]
        pass

try:
    from langchain_chroma import Chroma

    CHROMA_AVAILABLE = True
except Exception:  # pragma: no cover - optional dependency guard
    try:
        from langchain_community.vectorstores import Chroma

        CHROMA_AVAILABLE = True
    except Exception:  # pragma: no cover - optional dependency guard
        Chroma = None
        CHROMA_AVAILABLE = False


def _tokenize(text: str) -> set[str]:
    return set(re.findall(r"[a-z0-9]+", text.lower()))


class HashEmbeddings(Embeddings):
    """Lightweight deterministic embeddings to keep Chroma fully local/offline."""

    def __init__(self, dim: int = 192):
        self.dim = dim

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [self._embed(text) for text in texts]

    def embed_query(self, text: str) -> list[float]:
        return self._embed(text)

    def _embed(self, text: str) -> list[float]:
        vec = [0.0] * self.dim
        for token in _tokenize(text):
            idx = int(hashlib.sha1(token.encode("utf-8")).hexdigest(), 16) % self.dim
            vec[idx] += 1.0
        norm = math.sqrt(sum(x * x for x in vec))
        if norm > 0:
            vec = [x / norm for x in vec]
        return vec


class MarketEvidenceRetriever:
    """Retrieves market evidence and builds explainable course purpose cards."""

    def __init__(self, store: CatalogStore):
        self.store = store
        self._roles_by_id = store.roles_by_id
        self._skills_by_id = {s.skill_id: s for s in store.skills}
        self._sources_by_id = {s.source_id: s for s in store.sources}
        self._course_skill_strength = self._build_course_skill_strength(store)
        self._course_skill_map = self._build_course_skill_map(self._course_skill_strength)

        self._role_rows = self._build_role_rows(store.roles)
        self._evidence_rows = self._build_evidence_rows()
        self._use_vector = False
        self._roles_store = None
        self._evidence_store = None
        self._build_vector_indexes()

    @property
    def using_chroma(self) -> bool:
        return self._use_vector

    def retrieve_roles_by_interest(self, interests: list[str], top_k: int = 5) -> list[str]:
        if not interests:
            return [role.role_id for role in self.store.roles[:top_k]]

        query = " ".join(interests).strip()
        if not query:
            return [role.role_id for role in self.store.roles[:top_k]]

        if self._roles_store:
            try:
                docs = self._roles_store.similarity_search(query, k=max(top_k * 2, 8))
                ids = []
                seen = set()
                for doc in docs:
                    role_id = str(doc.metadata.get("role_id", ""))
                    if role_id and role_id not in seen:
                        ids.append(role_id)
                        seen.add(role_id)
                    if len(ids) >= top_k:
                        break
                if ids:
                    return ids
            except Exception:
                pass

        query_tokens = _tokenize(query)
        scored = []
        for row in self._role_rows:
            row_tokens = _tokenize(row["text"])
            overlap = len(query_tokens & row_tokens)
            phrase_bonus = sum(1 for term in interests if term.lower() in row["text"])
            score = overlap * 2.0 + phrase_bonus * 1.5
            scored.append((score, row["role_id"]))

        scored.sort(key=lambda x: (-x[0], x[1]))
        ranked = [role_id for score, role_id in scored if score > 0]
        if ranked:
            return ranked[:top_k]
        return [role.role_id for role in self.store.roles[:top_k]]

    def retrieve_role_evidence(self, role: RoleMarket, top_k: int = 8) -> list[EvidencePanelItem]:
        required_skills = {req.skill_id for req in role.required_skills}
        query = " ".join(
            [
                role.title,
                role.summary,
                *[self._skill_name(skill_id) for skill_id in required_skills],
            ]
        )

        ranked_rows = self._rank_evidence_rows(role, required_skills, query, top_k)
        primary_rows = [row for row in ranked_rows if row["role_id"] == role.role_id]
        items: list[EvidencePanelItem] = []
        seen = set()

        for row in primary_rows:
            key = (row["skill_id"], row["source_id"])
            if key in seen:
                continue
            seen.add(key)

            source = self._sources_by_id.get(row["source_id"])
            items.append(
                EvidencePanelItem(
                    role_id=row["role_id"],
                    skill_id=row["skill_id"],
                    skill_name=self._skill_name(row["skill_id"]),
                    source_id=row["source_id"],
                    source_provider=source.provider if source else "Unknown",
                    source_title=source.title if source else "Unknown source",
                    source_url=str(source.url) if source else "",
                    snippet=row["evidence_note"],
                    confidence=row["confidence"],
                )
            )
            if len(items) >= top_k:
                break

        return items

    def build_course_purpose_cards(
        self,
        plan: PlanResponse,
        role: RoleMarket,
        evidence_panel: list[EvidencePanelItem],
        max_evidence_per_course: int = 2,
    ) -> list[CoursePurposeCard]:
        role_required = {req.skill_id for req in role.required_skills}
        course_to_skills: dict[str, set[str]] = defaultdict(set)

        for cov in plan.skill_coverage:
            for course_id in cov.matched_courses:
                if cov.required_skill_id in role_required:
                    course = self.store.courses_by_id.get(course_id)
                    if not course:
                        continue
                    strength = self._course_skill_strength.get((course_id, cov.required_skill_id), 0)
                    if self._is_strong_skill_link(course, cov.required_skill_id, strength):
                        course_to_skills[course_id].add(cov.required_skill_id)

        for course_id, skill_ids in self._course_skill_map.items():
            course = self.store.courses_by_id.get(course_id)
            if not course:
                continue
            if course_id not in course_to_skills:
                course_to_skills[course_id] = set()
            for skill_id in skill_ids:
                if skill_id in role_required:
                    strength = self._course_skill_strength.get((course_id, skill_id), 0)
                    if self._is_strong_skill_link(course, skill_id, strength):
                        course_to_skills[course_id].add(skill_id)

        evidence_by_skill: dict[str, list[EvidencePanelItem]] = defaultdict(list)
        for item in evidence_panel:
            evidence_by_skill[item.skill_id].append(item)

        cards: list[CoursePurposeCard] = []
        for semester in plan.semesters:
            for course_id in semester.courses:
                course = self.store.courses_by_id.get(course_id)
                if not course:
                    continue
                skill_ids = sorted(course_to_skills.get(course_id, set()))
                skill_names = [self._skill_name(skill_id) for skill_id in skill_ids]

                if skill_names:
                    summary = ", ".join(skill_names[:3])
                    why = f"Supports {role.title} by building {summary}."
                else:
                    why = "Included as a prerequisite/support course to keep the roadmap feasible."

                card_evidence: list[EvidencePanelItem] = []
                for skill_id in skill_ids:
                    for ev in evidence_by_skill.get(skill_id, []):
                        if ev not in card_evidence:
                            card_evidence.append(ev)
                        if len(card_evidence) >= max_evidence_per_course:
                            break
                    if len(card_evidence) >= max_evidence_per_course:
                        break

                cards.append(
                    CoursePurposeCard(
                        course_id=course.course_id,
                        course_title=course.title,
                        why_this_course=why,
                        satisfied_skills=skill_ids,
                        evidence=card_evidence,
                    )
                )

        return cards

    def _build_vector_indexes(self) -> None:
        if not (LANGCHAIN_CORE_AVAILABLE and CHROMA_AVAILABLE and Document):
            return
        if not self._role_rows or not self._evidence_rows:
            return

        try:
            embeddings = HashEmbeddings()
            self._roles_store = Chroma(
                collection_name="roles_collection",
                embedding_function=embeddings,
            )
            role_docs = [
                Document(
                    page_content=row["text"],
                    metadata={"role_id": row["role_id"]},
                )
                for row in self._role_rows
            ]
            self._roles_store.add_documents(
                role_docs,
                ids=[f"role-{idx}" for idx, _ in enumerate(role_docs)],
            )

            self._evidence_store = Chroma(
                collection_name="role_evidence_collection",
                embedding_function=embeddings,
            )
            evidence_docs = [
                Document(
                    page_content=row["text"],
                    metadata={
                        "role_id": row["role_id"],
                        "skill_id": row["skill_id"],
                        "source_id": row["source_id"],
                        "confidence": row["confidence"],
                        "evidence_note": row["evidence_note"],
                    },
                )
                for row in self._evidence_rows
            ]
            self._evidence_store.add_documents(
                evidence_docs,
                ids=[f"evidence-{idx}" for idx, _ in enumerate(evidence_docs)],
            )
            self._use_vector = True
        except Exception:
            self._roles_store = None
            self._evidence_store = None
            self._use_vector = False

    def _build_role_rows(self, roles: list[RoleMarket]) -> list[dict]:
        rows = []
        for role in roles:
            skill_names = [self._skill_name(req.skill_id) for req in role.required_skills]
            text = f"{role.title} {role.summary} {' '.join(skill_names)}".lower()
            rows.append({"role_id": role.role_id, "text": text})
        return rows

    def _build_evidence_rows(self) -> list[dict]:
        rows: list[dict] = []
        for ev in self.store.evidence_links:
            role = self._roles_by_id.get(ev.role_id)
            role_title = role.title if role else ev.role_id
            skill_name = self._skill_name(ev.skill_id)
            source_ids = ev.evidence_sources or ["UNKNOWN"]
            for source_id in source_ids:
                source = self._sources_by_id.get(source_id)
                source_title = source.title if source else "Unknown source"
                text = (
                    f"{role_title} {skill_name} {ev.evidence_note} "
                    f"{source_title}"
                ).lower()
                rows.append(
                    {
                        "role_id": ev.role_id,
                        "skill_id": ev.skill_id,
                        "source_id": source_id,
                        "confidence": float(ev.confidence),
                        "evidence_note": ev.evidence_note,
                        "text": text,
                    }
                )
        return rows

    def _build_course_skill_strength(self, store: CatalogStore) -> dict[tuple[str, str], int]:
        mapping: dict[tuple[str, str], int] = {}
        for row in store.course_skills:
            key = (row.course_id, row.skill_id)
            mapping[key] = max(mapping.get(key, 0), int(row.strength))
        return mapping

    def _build_course_skill_map(
        self,
        strength_map: dict[tuple[str, str], int],
    ) -> dict[str, set[str]]:
        mapping: dict[str, set[str]] = defaultdict(set)
        for course_id, skill_id in strength_map:
            mapping[course_id].add(skill_id)
        return mapping

    def _is_strong_skill_link(self, course, skill_id: str, strength: int) -> bool:
        if strength <= 0:
            return False
        if self._is_foundational_course(course):
            return False

        dept = course.department
        title = course.title.upper()
        desc = course.description.upper()
        text = f"{title} {desc}"

        if strength >= 4:
            return True

        if skill_id == "SK_BUSINESS_ANALYSIS" and strength >= 2:
            return dept in {"MISY", "BUAD", "ECON", "FINC", "ACCT"}

        if skill_id == "SK_DATA_VIZ" and strength >= 2:
            return dept == "BUAD" or any(k in text for k in ("VISUAL", "DASHBOARD", "TABLEAU", "POWER BI"))

        if skill_id == "SK_SQL" and strength >= 2:
            return dept in {"MISY", "CISC", "BINF"} and any(
                k in text for k in ("DATABASE", "SQL", "QUERY", "RELATIONAL")
            )

        return strength >= 3

    def _is_foundational_course(self, course) -> bool:
        m = re.search(r"-(\d{3})", course.course_id)
        cnum = int(m.group(1)) if m else None
        if cnum is not None and cnum < 100:
            return True
        title_upper = course.title.upper()
        foundational_terms = (
            "INTERMEDIATE ALGEBRA",
            "PRE-CALCULUS",
            "PRECALCULUS",
            "SURVEY OF",
            "CONTEMPORARY MATHEMATICS",
        )
        return any(term in title_upper for term in foundational_terms)

    def _rank_evidence_rows(
        self,
        role: RoleMarket,
        required_skills: set[str],
        query: str,
        top_k: int,
    ) -> list[dict]:
        if self._evidence_store:
            try:
                docs = self._evidence_store.similarity_search(query, k=max(top_k * 3, 16))
                ranked = []
                for doc in docs:
                    role_id = str(doc.metadata.get("role_id", ""))
                    skill_id = str(doc.metadata.get("skill_id", ""))
                    source_id = str(doc.metadata.get("source_id", ""))
                    if role_id != role.role_id:
                        continue
                    role_bonus = 2.0 if role_id == role.role_id else 0.0
                    skill_bonus = 0.7 if skill_id in required_skills else 0.0
                    lexical_bonus = 0.2 * len(_tokenize(query) & _tokenize(doc.page_content))
                    ranked.append(
                        {
                            "role_id": role_id,
                            "skill_id": skill_id,
                            "source_id": source_id,
                            "confidence": float(doc.metadata.get("confidence", 0.0)),
                            "evidence_note": str(
                                doc.metadata.get("evidence_note", doc.page_content)
                            ),
                            "text": doc.page_content,
                            "score": float(doc.metadata.get("confidence", 0.0))
                            + role_bonus
                            + skill_bonus
                            + lexical_bonus,
                        }
                    )
                if ranked:
                    ranked.sort(
                        key=lambda x: (
                            x["role_id"] != role.role_id,
                            -x["score"],
                            -x["confidence"],
                            x["skill_id"],
                            x["source_id"],
                        )
                    )
                    return ranked
            except Exception:
                pass

        query_tokens = _tokenize(query)
        ranked = []
        for row in self._evidence_rows:
            if row["role_id"] != role.role_id:
                continue
            row_tokens = _tokenize(row["text"])
            overlap = len(query_tokens & row_tokens)
            role_bonus = 3.0 if row["role_id"] == role.role_id else 0.0
            skill_bonus = 2.0 if row["skill_id"] in required_skills else 0.0
            score = role_bonus + skill_bonus + overlap * 0.2 + row["confidence"]
            ranked.append((score, row))
        ranked.sort(
            key=lambda x: (
                x[1]["role_id"] != role.role_id,
                -x[0],
                x[1]["skill_id"],
                x[1]["source_id"],
            )
        )
        return [row for _, row in ranked]

    def _skill_name(self, skill_id: str) -> str:
        skill = self._skills_by_id.get(skill_id)
        return skill.name if skill else skill_id
