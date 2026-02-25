import AdvisorQAPanel from "@/components/AdvisorQAPanel";
import CareerPathMap from "@/components/CareerPathMap";
import type { CoursePurposeCard, PlanResponse, SkillCoverage } from "@/lib/types";

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

export default function PlanDashboard({ plan }: PlanDashboardProps): JSX.Element {
  const coveragePct = percentCovered(plan);

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

      <CareerPathMap plan={plan} />

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

          {plan.fusion_summary.unlock_skills.length ? (
            <div>
              <h4>Unlock Skills</h4>
              <ul className="plain-list">
                {plan.fusion_summary.unlock_skills.map((item) => (
                  <li key={`unlock-${item.skill_id}`}>
                    <p>
                      <strong className="mono">{item.skill_id}</strong>{" "}
                      <span className={item.covered ? "chip good" : "chip bad"}>
                        {item.covered ? "Covered" : "Not yet covered"}
                      </span>
                    </p>
                    <p className="muted">{item.reason}</p>
                    {item.matched_courses.length ? (
                      <p className="muted mono">{item.matched_courses.join(", ")}</p>
                    ) : null}
                  </li>
                ))}
              </ul>
            </div>
          ) : null}
        </article>
      ) : null}

      <div className="grid-two">
        <article className="subpanel">
          <h3>Skill Coverage</h3>
          <ul className="chip-list">
            {plan.skill_coverage.map((skill) => (
              <li key={skill.required_skill_id} className="chip-item">
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

          {plan.validation_errors.length > 0 ? (
            <>
              <h4 className="error-title">Validation Errors</h4>
              <ul className="plain-list error-list">
                {plan.validation_errors.map((error, idx) => (
                  <li key={`${error}-${idx}`}>{error}</li>
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
                {semester.courses.map((courseId) => (
                  <li key={`${semester.semester_index}-${courseId}`} className="mono">
                    {courseId}
                  </li>
                ))}
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
          <ul className="plain-list evidence-list">
            {plan.evidence_panel.map((evidence, idx) => (
              <li key={`${evidence.source_id}-${evidence.skill_id}-${idx}`}>
                <p>
                  <strong>{evidence.skill_name}</strong> - {evidence.source_provider}
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

      <AdvisorQAPanel plan={plan} />
    </section>
  );
}
