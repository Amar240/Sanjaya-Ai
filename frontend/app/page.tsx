"use client";

import { useEffect, useState } from "react";

import IntakeForm from "@/components/IntakeForm";
import PlanDashboard from "@/components/PlanDashboard";
import { createPlan, fetchRoles } from "@/lib/api";
import type { PlanRequest, PlanResponse, RoleOption } from "@/lib/types";

export default function HomePage(): JSX.Element {
  const [roles, setRoles] = useState<RoleOption[]>([]);
  const [loadingRoles, setLoadingRoles] = useState<boolean>(true);
  const [planning, setPlanning] = useState<boolean>(false);
  const [pageError, setPageError] = useState<string>("");
  const [plan, setPlan] = useState<PlanResponse | null>(null);

  useEffect(() => {
    let mounted = true;
    const loadRoles = async () => {
      setLoadingRoles(true);
      setPageError("");
      try {
        const data = await fetchRoles();
        if (mounted) {
          setRoles(data);
        }
      } catch (error) {
        if (mounted) {
          setPageError(
            error instanceof Error ? error.message : "Failed to load roles."
          );
        }
      } finally {
        if (mounted) {
          setLoadingRoles(false);
        }
      }
    };

    void loadRoles();
    return () => {
      mounted = false;
    };
  }, []);

  async function handlePlanSubmit(payload: PlanRequest): Promise<void> {
    setPlanning(true);
    setPageError("");
    try {
      const result = await createPlan(payload);
      setPlan(result);
    } catch (error) {
      setPageError(error instanceof Error ? error.message : "Failed to create plan.");
    } finally {
      setPlanning(false);
    }
  }

  return (
    <main className="app-shell">
      <div className="background-noise" aria-hidden />
      <header className="hero panel">
        <p className="eyebrow">Sanjaya AI</p>
        <h1>Grounded Career-to-Course Roadmaps</h1>
        <p>
          Market-evidenced role skills, prerequisite-safe semester planning, and
          explainability built into every recommendation.
        </p>
      </header>

      {pageError ? <p className="error-banner">{pageError}</p> : null}

      <IntakeForm
        roles={roles}
        loadingRoles={loadingRoles}
        planning={planning}
        onSubmit={handlePlanSubmit}
      />

      {plan ? (
        <PlanDashboard plan={plan} />
      ) : (
        <section className="panel empty-state">
          <h2>Plan Output</h2>
          <p>
            Submit intake details to generate a role-to-skill-to-course roadmap
            with evidence and verifier trace.
          </p>
        </section>
      )}
    </main>
  );
}
