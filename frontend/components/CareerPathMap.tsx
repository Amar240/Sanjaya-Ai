"use client";

import type { PlanResponse } from "@/lib/types";

type CareerPathMapProps = {
  plan: PlanResponse;
};

function mappedSkillsForCourse(plan: PlanResponse, courseId: string): string[] {
  const card = (plan.course_purpose_cards || []).find((item) => item.course_id === courseId);
  if (!card) {
    return [];
  }
  return card.satisfied_skills;
}

export default function CareerPathMap({ plan }: CareerPathMapProps): JSX.Element {
  return (
    <article className="subpanel career-map">
      <h3>Visual Career Path</h3>
      <p className="muted">
        Clear top-to-bottom path from selected role to covered skills, then semester-by-semester courses.
      </p>

      <div className="path-flow">
        <div className="path-node role-node">
          <p className="eyebrow">Target Role</p>
          <strong>{plan.selected_role_title}</strong>
          <p className="muted mono">{plan.selected_role_id}</p>
        </div>

        <div className="path-connector" aria-hidden />

        <div className="path-node skill-node">
          <p className="eyebrow">Required Skills</p>
          <div className="path-skill-chips">
            {plan.skill_coverage.map((skill) => (
              <span
                key={`path-skill-${skill.required_skill_id}`}
                className={skill.covered ? "chip good" : "chip bad"}
                title={
                  skill.matched_courses.length
                    ? `Mapped by ${skill.matched_courses.join(", ")}`
                    : "No mapped course yet"
                }
              >
                {skill.required_skill_id}
              </span>
            ))}
          </div>
        </div>

        <div className="path-connector" aria-hidden />

        <div className="path-semesters">
          {plan.semesters.map((semester) => (
            <div className="path-node semester-node" key={`path-sem-${semester.semester_index}`}>
              <p className="eyebrow">
                Semester {semester.semester_index} - {semester.term}
              </p>
              <p className="muted">{semester.total_credits} credits</p>
              <ul className="plain-list">
                {semester.courses.map((courseId) => {
                  const skills = mappedSkillsForCourse(plan, courseId);
                  return (
                    <li key={`path-course-${semester.semester_index}-${courseId}`}>
                      <p className="mono">{courseId}</p>
                      {skills.length ? (
                        <p className="muted">Builds: {skills.join(", ")}</p>
                      ) : (
                        <p className="muted">Support / prerequisite course</p>
                      )}
                    </li>
                  );
                })}
              </ul>
            </div>
          ))}
        </div>
      </div>
    </article>
  );
}
