"use client";

import { useEffect, useState } from "react";

import { askAdvisor } from "@/lib/api";
import type { AdvisorCitation, AdvisorResponse, PlanResponse } from "@/lib/types";

type AdvisorQAPanelProps = {
  plan: PlanResponse;
  queuedQuestion?: string | null;
  queuedQuestionNonce?: number;
};

function anchorId(prefix: string, raw: string): string {
  return `${prefix}-${raw.replace(/[^a-zA-Z0-9_-]/g, "-")}`;
}

function scrollToCitationTarget(citation: AdvisorCitation): void {
  const targetId = citation.evidence_id
    ? anchorId("evidence", citation.evidence_id)
    : citation.course_id
      ? anchorId("course", citation.course_id)
      : citation.skill_id
        ? anchorId("skill", citation.skill_id)
        : "";
  if (!targetId) {
    return;
  }
  const node = document.getElementById(targetId);
  if (!node) {
    return;
  }
  node.scrollIntoView({ behavior: "smooth", block: "center" });
  node.classList.add("target-highlight");
  window.setTimeout(() => node.classList.remove("target-highlight"), 1200);
}

export default function AdvisorQAPanel({
  plan,
  queuedQuestion,
  queuedQuestionNonce,
}: AdvisorQAPanelProps): JSX.Element {
  const [question, setQuestion] = useState<string>("Why this role for me?");
  const [tone, setTone] = useState<"friendly" | "concise">("friendly");
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string>("");
  const [result, setResult] = useState<AdvisorResponse | null>(null);

  async function handleAsk(explicitQuestion?: string): Promise<void> {
    const content = (explicitQuestion ?? question).trim();
    if (!content) {
      return;
    }
    setLoading(true);
    setError("");
    try {
      const response = await askAdvisor({
        question: content,
        plan_id: plan.plan_id,
        tone,
      });
      setResult(response);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Advisor request failed.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    if (!queuedQuestion || !queuedQuestionNonce) {
      return;
    }
    setQuestion(queuedQuestion);
    void handleAsk(queuedQuestion);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [queuedQuestionNonce]);

  return (
    <article className="subpanel advisor-panel">
      <h3>Ask Advisor</h3>
      <p className="muted">
        Ask why a role/course was recommended, capability/difficulty questions, and get defended reasoning with citations.
      </p>

      <div className="advisor-inputs">
        <input
          type="text"
          value={question}
          onChange={(event) => setQuestion(event.target.value)}
          placeholder="Am I capable for this path? How difficult is this roadmap?"
          disabled={loading}
        />
        <select
          value={tone}
          onChange={(event) => setTone(event.target.value as "friendly" | "concise")}
          disabled={loading}
        >
          <option value="friendly">Friendly</option>
          <option value="concise">Concise</option>
        </select>
        <button
          type="button"
          className="btn-primary"
          onClick={() => void handleAsk()}
          disabled={loading || !question.trim()}
        >
          {loading ? "Thinking..." : "Ask"}
        </button>
      </div>

      {error ? <p className="error-line">{error}</p> : null}

      {result ? (
        <div className="advisor-result">
          <p>
            <strong>Answer:</strong> {result.answer}
          </p>
          <p className="muted">
            Plan: <span className="mono">{result.plan_id}</span> |{" "}
            Intent: {result.intent} | Confidence: {Math.round(result.confidence * 100)}% | LLM:{" "}
            {result.llm_status}
          </p>
          {result.llm_status === "fallback" ? (
            <p className="muted">
              Fallback means deterministic advisor logic answered because the live LLM call was unavailable.
            </p>
          ) : null}
          {result.llm_error ? (
            <p className="muted">LLM detail: {result.llm_error}</p>
          ) : null}

          {result.reasoning_points.length ? (
            <>
              <h4>Reasoning</h4>
              <ul className="plain-list">
                {result.reasoning_points.map((item, idx) => (
                  <li key={`${item}-${idx}`}>{item}</li>
                ))}
              </ul>
            </>
          ) : null}

          {result.citations.length ? (
            <>
              <h4>Citations</h4>
              <ul className="plain-list">
                {result.citations.map((item, idx) => (
                  <li key={`${item.label}-${idx}`}>
                    <p>
                      <strong>{item.label}</strong> ({item.citation_type})
                    </p>
                    <p className="muted">{item.detail}</p>
                    {item.source_url ? (
                      <a href={item.source_url} target="_blank" rel="noreferrer">
                        Open source
                      </a>
                    ) : null}
                    {item.evidence_id || item.course_id || item.skill_id ? (
                      <button
                        type="button"
                        className="btn-secondary"
                        onClick={() => scrollToCitationTarget(item)}
                      >
                        Jump to context
                      </button>
                    ) : null}
                  </li>
                ))}
              </ul>
            </>
          ) : null}
        </div>
      ) : null}
    </article>
  );
}
