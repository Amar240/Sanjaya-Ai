"use client";

import { type FormEvent, useEffect, useMemo, useState } from "react";

import type {
  PlanMode,
  PlanRequest,
  ProgramLevel,
  RoleOption,
  Term
} from "@/lib/types";

type IntakeFormProps = {
  roles: RoleOption[];
  loadingRoles: boolean;
  planning: boolean;
  onSubmit: (payload: PlanRequest) => Promise<void> | void;
};

function parseCsv(input: string): string[] {
  return input
    .split(",")
    .map((item) => item.trim())
    .filter(Boolean);
}

export default function IntakeForm({
  roles,
  loadingRoles,
  planning,
  onSubmit
}: IntakeFormProps): JSX.Element {
  const [level, setLevel] = useState<ProgramLevel>("UG");
  const [mode, setMode] = useState<PlanMode>("CORE");
  const [currentSemester, setCurrentSemester] = useState<number>(1);
  const [startTerm, setStartTerm] = useState<Term>("Fall");
  const [includeOptionalTerms, setIncludeOptionalTerms] =
    useState<boolean>(false);
  const [minCredits, setMinCredits] = useState<number>(12);
  const [targetCredits, setTargetCredits] = useState<number>(15);
  const [maxCredits, setMaxCredits] = useState<number>(17);
  const [interestsText, setInterestsText] = useState<string>(
    "operations research, analytics, optimization"
  );
  const [fusionDomainText, setFusionDomainText] = useState<string>("");
  const [completedCoursesText, setCompletedCoursesText] = useState<string>("");
  const [preferredRoleId, setPreferredRoleId] = useState<string>("");
  const [requestedRoleText, setRequestedRoleText] = useState<string>("");
  const [localError, setLocalError] = useState<string>("");

  const roleOptions = useMemo(() => {
    if (mode !== "FUSION") {
      return roles;
    }
    return roles.filter((role) => role.fusion_available);
  }, [mode, roles]);

  useEffect(() => {
    if (roleOptions.length === 0) {
      setPreferredRoleId("");
      return;
    }
    if (!preferredRoleId || !roleOptions.some((role) => role.role_id === preferredRoleId)) {
      setPreferredRoleId(roleOptions[0].role_id);
    }
  }, [roleOptions, preferredRoleId]);

  function handleLevelChange(nextLevel: ProgramLevel): void {
    setLevel(nextLevel);
    if (nextLevel === "UG") {
      setMinCredits(12);
      setTargetCredits(15);
      setMaxCredits(17);
    } else {
      setMinCredits(9);
      setTargetCredits(9);
      setMaxCredits(12);
    }
  }

  const submitDisabled = planning || loadingRoles || roleOptions.length === 0;

  const helperText = useMemo(() => {
    if (loadingRoles) {
      return "Loading role catalog from backend...";
    }
    if (!roleOptions.length) {
      return "No roles loaded yet. Check backend and refresh.";
    }
    if (mode === "FUSION") {
      return `${roleOptions.length} fusion-ready roles loaded.`;
    }
    return `${roleOptions.length} market-grounded roles loaded.`;
  }, [loadingRoles, roleOptions.length, mode]);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setLocalError("");

    if (targetCredits < minCredits || targetCredits > maxCredits) {
      setLocalError("Target credits must be between minimum and maximum.");
      return;
    }

    const payload: PlanRequest = {
      student_profile: {
        level,
        mode,
        fusion_domain: mode === "FUSION" ? fusionDomainText.trim() || null : null,
        current_semester: currentSemester,
        start_term: startTerm,
        include_optional_terms: includeOptionalTerms,
        completed_courses: parseCsv(completedCoursesText),
        min_credits: minCredits,
        target_credits: targetCredits,
        max_credits: maxCredits,
        interests: parseCsv(interestsText)
      },
      preferred_role_id: preferredRoleId || null,
      requested_role_text: requestedRoleText.trim() || null
    };

    await onSubmit(payload);
  }

  return (
    <section className="panel intake-panel">
      <div className="panel-header">
        <h2>Intake Chat</h2>
        <p>Structured intake that feeds the planner agents.</p>
      </div>

      <div className="chat-stack">
        <div className="chat-bubble ai">
          What program level and planning mode are you using?
        </div>
        <div className="chat-bubble user compact-grid">
          <label>
            Level
            <select
              value={level}
              onChange={(e) =>
                handleLevelChange(e.target.value as ProgramLevel)
              }
            >
              <option value="UG">Undergraduate</option>
              <option value="GR">Graduate</option>
            </select>
          </label>
          <label>
            Mode
            <select
              value={mode}
              onChange={(e) => setMode(e.target.value as PlanMode)}
            >
              <option value="CORE">Core Role Mapping</option>
              <option value="FUSION">Fusion Mode</option>
            </select>
          </label>
        </div>

        <div className="chat-bubble ai">
          Which role do you want to target from market-grounded options?
        </div>
        <div className="chat-bubble user">
          <label>
            Preferred Role
            <select
              value={preferredRoleId}
              onChange={(e) => setPreferredRoleId(e.target.value)}
              disabled={loadingRoles || roleOptions.length === 0}
            >
              {roleOptions.map((role) => (
                <option key={role.role_id} value={role.role_id}>
                  {role.title}
                </option>
              ))}
            </select>
          </label>
          <p className="muted">{helperText}</p>
        </div>

        {mode === "FUSION" ? (
          <>
            <div className="chat-bubble ai">
              Which domain passion should be combined with technology in this plan?
            </div>
            <div className="chat-bubble user">
              <label>
                Fusion Domain
                <input
                  type="text"
                  value={fusionDomainText}
                  onChange={(e) => setFusionDomainText(e.target.value)}
                  placeholder="finance, biology, policy, healthcare"
                />
              </label>
            </div>
          </>
        ) : null}
      </div>

      <form onSubmit={handleSubmit} className="intake-form">
        <div className="field-grid">
          <label>
            Current Semester
            <input
              type="number"
              min={1}
              max={12}
              value={currentSemester}
              onChange={(e) => setCurrentSemester(Number(e.target.value))}
              required
            />
          </label>
          <label>
            Start Term
            <select
              value={startTerm}
              onChange={(e) => setStartTerm(e.target.value as Term)}
            >
              <option value="Fall">Fall</option>
              <option value="Spring">Spring</option>
              <option value="Summer">Summer</option>
              <option value="Winter">Winter</option>
            </select>
          </label>
          <label className="checkbox-line">
            <input
              type="checkbox"
              checked={includeOptionalTerms}
              onChange={(e) => setIncludeOptionalTerms(e.target.checked)}
            />
            Include Summer/Winter terms
          </label>
        </div>

        <div className="field-grid three">
          <label>
            Min Credits
            <input
              type="number"
              min={0}
              max={30}
              value={minCredits}
              onChange={(e) => setMinCredits(Number(e.target.value))}
              required
            />
          </label>
          <label>
            Target Credits
            <input
              type="number"
              min={0}
              max={30}
              value={targetCredits}
              onChange={(e) => setTargetCredits(Number(e.target.value))}
              required
            />
          </label>
          <label>
            Max Credits
            <input
              type="number"
              min={0}
              max={30}
              value={maxCredits}
              onChange={(e) => setMaxCredits(Number(e.target.value))}
              required
            />
          </label>
        </div>

        <label>
          Interests (comma-separated)
          <input
            type="text"
            value={interestsText}
            onChange={(e) => setInterestsText(e.target.value)}
            placeholder="ai, finance, cybersecurity"
          />
        </label>

        <label>
          Role I&apos;m Looking For (optional)
          <input
            type="text"
            value={requestedRoleText}
            onChange={(e) => setRequestedRoleText(e.target.value)}
            placeholder="e.g. AI policy architect"
          />
        </label>

        <label>
          Completed Courses (comma-separated IDs)
          <input
            type="text"
            value={completedCoursesText}
            onChange={(e) => setCompletedCoursesText(e.target.value)}
            placeholder="CISC-108, MATH-201"
          />
        </label>

        {localError ? <p className="error-line">{localError}</p> : null}

        <button type="submit" disabled={submitDisabled} className="btn-primary">
          {planning ? "Generating Plan..." : "Generate Explainable Roadmap"}
        </button>
      </form>
    </section>
  );
}
