"use client";

import { useMemo, useState } from "react";

import AdvisorQAPanel from "@/components/AdvisorQAPanel";
import CareerPathMap from "@/components/CareerPathMap";
import type {
  CoursePurposeCard,
  PlanError,
  PlanResponse,
  SkillCoverage,
} from "@/lib/types";

type PlanDashboardProps = {
  plan: PlanResponse;
};

function percentCovered(plan: PlanResponse): number {
  if (!plan.skill_coverage.length) {
    return 0;
  }
  const covered = plan.skill_coverage.filter((skill) => skill.covered).length;
  return Math.round((covered / plan.skill_coverage.length) * 100);
}

function courseCardKey(card: CoursePurposeCard, idx: number): string {
  return `${card.course_id}-${idx}`;
}

function skillLine(skill: SkillCoverage): string {
  if (!skill.matched_courses.length) {
    return "No mapped courses";
  }
  return skill.matched_courses.join(", ");
}

function anchorId(prefix: string, raw: string): string {
  return `${prefix}-${raw.replace(/[^a-zA-Z0-9_-]/g, "-")}`;
}

function errorSeverity(error: PlanError): "warning" | "error" {
  const severity = String(error.details?.severity ?? "").toLowerCase();
  return severity === "warning" ? "warning" : "error";
}

export default function PlanDashboard({ plan }: PlanDashboardProps): JSX.Element {
  const coveragePct = percentCovered(plan);
  const [filterSelectedSkills, setFilterSelectedSkills] = useState<boolean>(false);
  const [queuedAdvisorQuestion, setQueuedAdvisorQuestion] = useState<string | null>(null);
  const [queuedAdvisorNonce, setQueuedAdvisorNonce] = useState<number>(0);

  const selectedSkillIds = useMemo(
    () => new Set(plan.skill_coverage.map((skill) => skill.required_skill_id)),
    [plan.skill_coverage]
  );
  const filteredEvidence = useMemo(() => {
    const evidence = plan.evidence_panel || [];
    if (!filterSelectedSkills) {
      return evidence;
    }
    return evidence.filter((item) => selectedSkillIds.has(item.skill_id));
  }, [filterSelectedSkills, plan.evidence_panel, selectedSkillIds]);

  const groupedValidation = useMemo(() => {
    const groups = new Map<string, { code: string; severity: "warning" | "error"; items: PlanError[] }>();
    for (const error of plan.validation_errors) {
      const severity = errorSeverity(error);
      const key = `${error.code}|${severity}`;
      const existing = groups.get(key);
      if (existing) {
        existing.items.push(error);
      } else {
        groups.set(key, { code: error.code, severity, items: [error] });
      }
    }
    return Array.from(groups.values()).sort((a, b) => {
      if (a.severity !== b.severity) {
        return a.severity === "error" ? -1 : 1;
      }
      return a.code.localeCompare(b.code);
    });
  }, [plan.validation_errors]);

  function handleAskWhyNotRole(roleId: string, roleTitle: string): void {
    const question = `Why not ${roleTitle} (${roleId})?`;
    setQueuedAdvisorQuestion(question);
    setQueuedAdvisorNonce((value) => value + 1);
  }

  const firstCourseAnchorById = new Set<string>();

  return (
    <section className="panel dashboard-panel">
      <div className="plan-head">
        <div>
          <p className="eyebrow">Selected Role</p>
          <h2>{plan.selected_role_title}</h2>
          <p className="muted mono">{plan.selected_role_id}</p>
        </div>
        <div className="kpi-card">
          <span>Skill Coverage</span>
          <strong>{coveragePct}%</strong>
        </div>
      </div>

      <article className="subpanel">
        <h3>Plan Metadata</h3>
        <p className="muted">
          Plan ID: <span className="mono">{plan.plan_id}</span>
        </p>
        <p className="muted">
          Data Version: <span className="mono">{plan.data_version}</span>
        </p>
        <p className="muted">Cache Status: {plan.cache_status}</p>
        <p className="muted">
          Request ID: <span className="mono">{plan.request_id}</span>
        </p>
        {plan.node_timings?.length ? (
          <details>
            <summary>Node Timings ({plan.node_timings.length})</summary>
            <ul className="plain-list">
              {plan.node_timings.map((item, idx) => (
                <li key={`${item.node}-${idx}`}>
                  <span className="mono">{item.node}</span> - {item.timing_ms}ms
                </li>
              ))}
            </ul>
          </details>
        ) : null}
      </article>

      <CareerPathMap plan={plan} onAskWhyNotRole={handleAskWhyNotRole} />

      {plan.fusion_summary ? (
        <article className="subpanel fusion-panel">
          <h3>Fusion Readiness</h3>
          <p className="muted">
            Domain: <strong>{plan.fusion_summary.domain}</strong> | Weights:
            domain {Math.round(plan.fusion_summary.domain_weight * 100)}% and tech{" "}
            {Math.round(plan.fusion_summary.tech_weight * 100)}%
          </p>
          <div className="fusion-kpis">
            <div className="kpi-mini">
              <span>Domain Ready</span>
              <strong>{Math.round(plan.fusion_summary.readiness.domain_ready_pct * 100)}%</strong>
            </div>
            <div className="kpi-mini">
              <span>Tech Ready</span>
              <strong>{Math.round(plan.fusion_summary.readiness.tech_ready_pct * 100)}%</strong>
            </div>
            <div className="kpi-mini">
              <span>Overall Fit</span>
              <strong>{Math.round(plan.fusion_summary.readiness.overall_fit_pct * 100)}%</strong>
            </div>
          </div>

          <div className="grid-two">
            <div>
              <h4>Domain Skills</h4>
              <ul className="chip-list">
                {plan.fusion_summary.domain_skill_coverage.map((skill) => (
                  <li key={`domain-${skill.required_skill_id}`} className="chip-item">
                    <span className={skill.covered ? "chip good" : "chip bad"}>
                      {skill.covered ? "Covered" : "Gap"}
                    </span>
                    <div>
                      <p className="mono">{skill.required_skill_id}</p>
                      <p className="muted">{skillLine(skill)}</p>
                    </div>
                  </li>
                ))}
              </ul>
            </div>
            <div>
              <h4>Tech Skills</h4>
              <ul className="chip-list">
                {plan.fusion_summary.tech_skill_coverage.map((skill) => (
                  <li key={`tech-${skill.required_skill_id}`} className="chip-item">
                    <span className={skill.covered ? "chip good" : "chip bad"}>
                      {skill.covered ? "Covered" : "Gap"}
                    </span>
                    <div>
                      <p className="mono">{skill.required_skill_id}</p>
                      <p className="muted">{skillLine(skill)}</p>
                    </div>
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </article>
      ) : null}

      <div className="grid-two">
        <article className="subpanel">
          <h3>Skill Coverage</h3>
          <ul className="chip-list">
            {plan.skill_coverage.map((skill) => (
              <li
                id={anchorId("skill", skill.required_skill_id)}
                key={skill.required_skill_id}
                className="chip-item"
              >
                <span className={skill.covered ? "chip good" : "chip bad"}>
                  {skill.covered ? "Covered" : "Gap"}
                </span>
                <div>
                  <p className="mono">{skill.required_skill_id}</p>
                  <p className="muted">{skillLine(skill)}</p>
                </div>
              </li>
            ))}
          </ul>
        </article>

        <article className="subpanel">
          <h3>Planner Notes</h3>
          <ul className="plain-list">
            {plan.notes.map((note, idx) => (
              <li key={`${note}-${idx}`}>{note}</li>
            ))}
          </ul>

          {groupedValidation.length ? (
            <>
              <h4 className="error-title">Validation Issues</h4>
              <ul className="plain-list">
                {groupedValidation.map((group) => (
                  <li key={`${group.code}-${group.severity}`}>
                    <p>
                      <strong>{group.code}</strong>{" "}
                      <span className={`issue-pill ${group.severity}`}>
                        {group.severity}
                      </span>{" "}
                      ({group.items.length})
                    </p>
                    <ul className="plain-list">
                      {group.items.slice(0, 5).map((item, idx) => (
                        <li key={`${group.code}-item-${idx}`}>{item.message}</li>
                      ))}
                    </ul>
                  </li>
                ))}
              </ul>
            </>
          ) : null}
        </article>
      </div>

      <article className="subpanel">
        <h3>Semester Roadmap</h3>
        <div className="timeline-grid">
          {plan.semesters.map((semester) => (
            <div className="timeline-card" key={`semester-${semester.semester_index}`}>
              <header>
                <p className="eyebrow">
                  Semester {semester.semester_index} - {semester.term}
                </p>
                <strong>{semester.total_credits} credits</strong>
              </header>
              <ul>
                {semester.courses.map((courseId) => {
                  const courseAnchor = anchorId("course", courseId);
                  const shouldAnchor = !firstCourseAnchorById.has(courseAnchor);
                  if (shouldAnchor) {
                    firstCourseAnchorById.add(courseAnchor);
                  }
                  return (
                    <li
                      id={shouldAnchor ? courseAnchor : undefined}
                      key={`${semester.semester_index}-${courseId}`}
                      className="mono"
                    >
                      {courseId}
                    </li>
                  );
                })}
              </ul>
              {semester.warnings.length ? (
                <details>
                  <summary>{semester.warnings.length} warning(s)</summary>
                  <ul className="plain-list warning-list">
                    {semester.warnings.map((warning, idx) => (
                      <li key={`${warning}-${idx}`}>{warning}</li>
                    ))}
                  </ul>
                </details>
              ) : null}
            </div>
          ))}
        </div>
      </article>

      {plan.course_purpose_cards?.length ? (
        <article className="subpanel">
          <h3>Course Purpose Cards</h3>
          <div className="cards-grid">
            {plan.course_purpose_cards.map((card, idx) => (
              <div className="purpose-card" key={courseCardKey(card, idx)}>
                <p className="mono">
                  {card.course_id} - {card.course_title}
                </p>
                <p>{card.why_this_course}</p>
                <div className="skill-tags">
                  {card.satisfied_skills.length ? (
                    card.satisfied_skills.map((skillId) => (
                      <span key={`${card.course_id}-${skillId}`} className="tag">
                        {skillId}
                      </span>
                    ))
                  ) : (
                    <span className="tag muted-tag">Support / prerequisite</span>
                  )}
                </div>
                {card.evidence.length ? (
                  <details>
                    <summary>Evidence ({card.evidence.length})</summary>
                    <ul className="plain-list">
                      {card.evidence.map((evidence, evidenceIdx) => (
                        <li key={`${card.course_id}-${evidence.source_id}-${evidenceIdx}`}>
                          <p>
                            <strong>{evidence.source_provider}</strong> -{" "}
                            {evidence.source_title}
                          </p>
                          <p className="muted">{evidence.snippet}</p>
                          <a href={evidence.source_url} target="_blank" rel="noreferrer">
                            Open source
                          </a>
                        </li>
                      ))}
                    </ul>
                  </details>
                ) : null}
              </div>
            ))}
          </div>
        </article>
      ) : null}

      {plan.evidence_panel?.length ? (
        <article className="subpanel">
          <h3>Evidence Panel</h3>
          <label className="checkbox-line">
            <input
              type="checkbox"
              checked={filterSelectedSkills}
              onChange={(event) => setFilterSelectedSkills(event.target.checked)}
            />
            <span>Show only selected-plan skills</span>
          </label>
          <ul className="plain-list evidence-list">
            {filteredEvidence.map((evidence, idx) => (
              <li id={anchorId("evidence", evidence.evidence_id)} key={`${evidence.evidence_id}-${idx}`}>
                <p>
                  <strong>{evidence.skill_name}</strong>
                </p>
                <p className="meta-line">
                  <span className="tag">{evidence.source_provider}</span>
                  <span className="tag">{evidence.retrieval_method}</span>
                  {typeof evidence.rank_score === "number" ? (
                    <span className="tag">Rank {evidence.rank_score.toFixed(3)}</span>
                  ) : null}
                </p>
                <p className="muted">{evidence.snippet}</p>
                <p className="meta-line">
                  <a href={evidence.source_url} target="_blank" rel="noreferrer">
                    {evidence.source_title}
                  </a>
                  {typeof evidence.confidence === "number" ? (
                    <span>Confidence: {Math.round(evidence.confidence * 100)}%</span>
                  ) : null}
                </p>
              </li>
            ))}
          </ul>
        </article>
      ) : null}

      {plan.agent_trace?.length ? (
        <article className="subpanel">
          <h3>Agent Trace</h3>
          <ol className="plain-list">
            {plan.agent_trace.map((trace, idx) => (
              <li key={`${trace}-${idx}`}>{trace}</li>
            ))}
          </ol>
        </article>
      ) : null}

      <AdvisorQAPanel
        plan={plan}
        queuedQuestion={queuedAdvisorQuestion}
        queuedQuestionNonce={queuedAdvisorNonce}
      />
    </section>
  );
}
