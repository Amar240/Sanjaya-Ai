from __future__ import annotations

from collections import defaultdict

from ..schemas.catalog import Course, CourseSkillMapping, CuratedRoleSkillCourse, RoleMarket
from ..schemas.plan import PlanRequest, PlanSemester, SkillCoverage


def verify_plan(
    request: PlanRequest,
    role: RoleMarket,
    semesters: list[PlanSemester],
    courses_by_id: dict[str, Course],
    skill_coverage: list[SkillCoverage],
    all_courses_by_id: dict[str, Course],
    course_skills: list[CourseSkillMapping],
    curated_role_skill_courses: list[CuratedRoleSkillCourse],
) -> tuple[list[str], list[str], list[PlanSemester]]:
    errors: list[str] = []
    notes: list[str] = []

    _verify_course_existence(semesters, courses_by_id, errors)
    _verify_prerequisites(request, semesters, courses_by_id, errors, notes)
    _verify_credit_rules(request, semesters, errors)
    _verify_skill_coverage(role, skill_coverage, notes)
    _verify_skill_level_availability(
        request=request,
        role=role,
        all_courses_by_id=all_courses_by_id,
        course_skills=course_skills,
        curated_role_skill_courses=curated_role_skill_courses,
        notes=notes,
    )

    return errors, notes, semesters


def _verify_course_existence(
    semesters: list[PlanSemester],
    courses_by_id: dict[str, Course],
    errors: list[str],
) -> None:
    for sem in semesters:
        for course_id in sem.courses:
            if course_id not in courses_by_id:
                errors.append(
                    f"Semester {sem.semester_index}: course '{course_id}' does not exist in course catalog."
                )


def _verify_prerequisites(
    request: PlanRequest,
    semesters: list[PlanSemester],
    courses_by_id: dict[str, Course],
    errors: list[str],
    notes: list[str],
) -> None:
    completed = set(request.student_profile.completed_courses)
    external_count = 0
    for sem in semesters:
        for course_id in sem.courses:
            course = courses_by_id.get(course_id)
            if not course:
                continue
            for prereq in course.prerequisites:
                if prereq in completed:
                    continue
                if prereq not in courses_by_id:
                    external_count += 1
                    notes.append(
                        f"Semester {sem.semester_index}: '{course_id}' has external prerequisite '{prereq}' not in current dataset scope."
                    )
                    continue
                errors.append(
                    f"Semester {sem.semester_index}: prerequisite '{prereq}' not satisfied before '{course_id}'."
                )
        completed.update(sem.courses)

    # Plan-specific summary is more useful than global catalog-level counts.
    notes.append(f"Plan-specific external prerequisite references: {external_count}.")


def _verify_credit_rules(
    request: PlanRequest,
    semesters: list[PlanSemester],
    errors: list[str],
) -> None:
    policy = _credit_policy(request.student_profile.level)
    for sem in semesters:
        total = sem.total_credits
        is_optional_term = sem.term in {"Summer", "Winter"}
        if total < policy["full_time_min"] and not is_optional_term:
            sem.warnings.append(
                f"Below full-time minimum ({policy['full_time_min']} credits)."
            )
        if total > policy["normal_max"]:
            overload_msg = (
                "Advisor approval required for overload."
                if request.student_profile.level == "UG"
                else "Over typical graduate load; advisor approval recommended."
            )
            sem.warnings.append(overload_msg)
        if total > request.student_profile.max_credits:
            errors.append(
                f"Semester {sem.semester_index}: planned credits {total} exceed max_credits {request.student_profile.max_credits}."
            )


def _verify_skill_coverage(
    role: RoleMarket,
    skill_coverage: list[SkillCoverage],
    notes: list[str],
) -> None:
    uncovered = [s.required_skill_id for s in skill_coverage if not s.covered]
    if uncovered:
        notes.append(
            f"Role '{role.role_id}' has {len(uncovered)} uncovered required skills in current plan: {', '.join(uncovered)}."
        )


def _verify_skill_level_availability(
    request: PlanRequest,
    role: RoleMarket,
    all_courses_by_id: dict[str, Course],
    course_skills: list[CourseSkillMapping],
    curated_role_skill_courses: list[CuratedRoleSkillCourse],
    notes: list[str],
) -> None:
    curated_levels_by_skill: dict[str, set[str]] = defaultdict(set)
    for row in curated_role_skill_courses:
        if row.role_id != role.role_id:
            continue
        course = all_courses_by_id.get(row.course_id)
        if course:
            curated_levels_by_skill[row.skill_id].add(course.level)

    fallback_levels_by_skill: dict[str, set[str]] = defaultdict(set)
    for row in course_skills:
        course = all_courses_by_id.get(row.course_id)
        if course:
            fallback_levels_by_skill[row.skill_id].add(course.level)

    ug_only_skills: list[str] = []
    gr_only_skills: list[str] = []
    for req in role.required_skills:
        levels = curated_levels_by_skill.get(req.skill_id)
        if not levels:
            levels = fallback_levels_by_skill.get(req.skill_id, set())

        if not levels:
            notes.append(
                f"Required skill '{req.skill_id}' has no mapped courses in current dataset."
            )
            continue

        if levels == {"UG"}:
            ug_only_skills.append(req.skill_id)
        elif levels == {"GR"}:
            gr_only_skills.append(req.skill_id)

    if ug_only_skills:
        notes.append(
            "Skill-level mapping constraint (UG-only): "
            + ", ".join(sorted(ug_only_skills))
            + "."
        )
    if gr_only_skills:
        notes.append(
            "Skill-level mapping constraint (GR-only): "
            + ", ".join(sorted(gr_only_skills))
            + "."
        )

    if request.student_profile.level == "UG" and gr_only_skills:
        notes.append(
            "UG planning impact: GR-only mapped skills may remain uncovered until graduate-level study or mapping updates."
        )
    if request.student_profile.level == "GR" and ug_only_skills:
        notes.append(
            "GR planning impact: some skills currently map only to UG courses; confirm policy with advisor/program."
        )


def _credit_policy(level: str) -> dict[str, int]:
    if level == "GR":
        return {"full_time_min": 9, "normal_max": 12}
    return {"full_time_min": 12, "normal_max": 17}
