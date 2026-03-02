# Sanjaya AI - Explainable Career Roadmaps

Explainable, deterministic course-to-career planner with evidence-backed recommendations.

Repo: `https://github.com/Amar240/AiIgnite-Sanjaya-Ai.git`

## Judge TL;DR
- Problem solved: students pick courses without clear proof that those choices map to real jobs, required skills, and feasible timelines.
- Why this is different: Sanjaya AI connects course plans to role reality, skill evidence, and job-posting checks in one governed workflow.
- What is deterministic: role selection constraints, semester scheduling, prerequisite/credit validation, and readiness gates.
- How to evaluate in 2-3 minutes: run the canonical demo below and verify the expected outputs checklist.

## Why This Should Score High
### Innovation
- We connect role -> skills -> courses -> semester plan -> job-posting gap analysis in one product loop, not as separate tools.
- Proof: `Your path in 5 steps` combines market reality, skill gaps, storyboard, and job-match outcomes in one flow.

### Technical Rigor
- Core planning and validation are deterministic, with typed error codes and reproducible outputs.
- Proof: backend test suite validates planner, verifier, cache behavior, governance, and endpoint behavior.

### Explainability and Safety
- Recommendations include source-backed evidence and explicit validation warnings instead of opaque text output.
- Proof: evidence panel, citation fields, and validation codes such as `PREREQ_ORDER` and `CREDIT_OVER_MAX`.

### Real-World Feasibility
- Admin workflows support role-request intake, draft curation, readiness gates, and controlled publishing.
- Proof: `/admin/role-requests`, `/admin/drafts/[draftId]`, and publish governance tests.

### Student and Advisor Impact
- Students get actionable gap closure (courses + projects), while advisors get explainable Q&A and portfolio-level insights.
- Proof: advisor flows with citations plus `/admin/insights` aggregate trends and risk signals.

### Rubric Mapping (Criterion -> Evidence)
| Criterion | Evidence in Project | Where to Verify |
| --- | --- | --- |
| Innovation | End-to-end roadmap from course intake to job-posting match | UI flow at `/` -> `Your path in 5 steps` |
| Technical rigor | Deterministic planner/verifier and typed response schemas | `backend/tests/` and FastAPI responses |
| Explainability and safety | Citation-linked evidence and structured validation warnings | Skills/Evidence panel and Validation tab |
| Feasibility and operations | Admin curation + readiness gates before publish | `/admin/role-requests`, `/admin/drafts/[draftId]` |
| Impact | Student-facing clarity plus advisor/admin monitoring | `/`, `/admin/insights`, advisor Q&A |

## 90-Second Judge Demo (Deterministic Script)
Use this exact seed so all 5 steps populate consistently.

### Demo seed
| Field | Value |
| --- | --- |
| Level | UG (Undergraduate) |
| Mode | Fusion |
| Fusion domain | `finance` |
| Goal type | Pick a role |
| Preferred role | Quant Risk Analyst or FinTech Engineer |
| Current semester | 1 |
| Start term | Fall |
| Interests | operations research, analytics, optimization |

### Click path and expected outputs
1. Open `http://127.0.0.1:3000/` and complete intake using the seed above.
Expected: plan hero appears with selected role and summary bar.
2. Open Step 1 `Target Reality`.
Expected: role tasks and salary band with market grounding.
3. Open Step 2 `Skill Gaps`.
Expected: covered vs missing skills and recommended projects.
4. Open Step 3 `Fusion Opportunities`.
Expected: fusion pack summary with cross-domain readiness signal.
5. Open Step 4 `Career Storyboard` and click generate.
Expected: narrative sections with citations; if no LLM key, deterministic fallback still renders.
6. Open Step 5 `Reality Check (Job Posting)`, click `Load Preset 1`, then `Extract & Match`.
Expected: mapped vs unmapped terms, covered/missing skills, and project recommendations.
7. In Advisor Q&A, ask `Why this role?`.
Expected: constrained answer with reasoning and citations tied to plan context.

## Proof Block (Metrics + Reliability)
As of March 2, 2026:

| Check | Result | Command |
| --- | --- | --- |
| Backend tests | Pass (`73/73`) | `cd backend && .venv312\Scripts\python -m pytest` |
| Frontend lint | Pass | `cd frontend && npm run lint` |
| Frontend production build | Pass | `cd frontend && npm run build` |
| LLM-off mode | Supported | planner/validation still run without API keys |

Failure-safe behavior:
- If LLM is unavailable, planning, validation, and roadmap generation still work.
- Storyboard and advisor flows degrade gracefully with deterministic fallback behavior.
- Core feasibility rules (prereqs, credits, degree totals) are never delegated to LLM output.

## How It Works (Architecture in 60 Seconds)
1. Intake captures level/mode/preferences and degree constraints.
2. Role selector ranks curated market roles from interests and optional preferred role.
3. Deterministic planner schedules semester-by-semester courses under credit/prereq constraints.
4. Verifier emits structured warnings/errors (`PlanError` codes) for feasibility issues.
5. Evidence layer links skills and claims to source-backed market/course artifacts.
6. Optional LLM layer generates narrative text and advisor responses from structured context only.
7. Job-match module extracts skills from posting text and maps to covered/missing skill IDs.

LLM boundary:
- Allowed: narrative rewrite, advisor phrasing, text extraction with fallback.
- Not allowed: deciding course feasibility, prerequisites, or core validation outcomes.

## Quick Start
### Judge fastest path (Docker)
From repo root:

```bash
docker compose up --build
```

Open:
- App: `http://localhost:3000`
- Backend health: `http://localhost:8000/health`

### Local run (Python + Node)
Backend:

```powershell
cd backend
python -m pip install -r requirements.txt
copy .env.example .env
uvicorn app.main:app --reload --port 8000
```

Frontend (new terminal):

```powershell
cd frontend
copy .env.local.example .env.local
npm install
npm run dev
```

Open:
- App: `http://127.0.0.1:3000/`
- API docs: `http://127.0.0.1:8000/docs`

## Evaluation Checklist for Judges (Pass/Fail)
- [ ] Plan generates from intake and shows role-specific roadmap hero.
- [ ] Validation tab shows structured feasibility codes/warnings (not free-text guesses).
- [ ] Skills view shows covered vs missing skills with evidence/citations.
- [ ] Reality Check maps job text to covered/missing skills and recommends projects.
- [ ] Advisor answers stay grounded in plan context with citations.
- [ ] Admin flow supports role requests, draft readiness gates, and controlled publish path.

## Limitations and Responsible Use
- No job guarantee is made; this is decision support for planning and advising.
- Salary values are market estimates, not promises.
- LLM is optional and bounded; deterministic logic remains the source of truth.
- Results depend on current catalog/market data coverage and curation quality.

## Data Transparency (`data/processed/`)
| File | Purpose |
| --- | --- |
| `courses.json` | Course catalog with credits, prerequisites, terms |
| `course_skills*.json` | Course-to-skill mappings (curated + fallback) |
| `roles_market*.json` | Roles + required skills + evidence source IDs |
| `skills_market.json` | Canonical skill taxonomy |
| `role_skill_evidence.json` + `market_sources.json` | Evidence snippets + source metadata |
| `role_reality_usa.json` | Role tasks and salary bands (USA posture) |
| `project_templates.json` | Project templates for missing-skill closure |

## Admin Auth (Minimal Setup)
Set the same token in both files:
- `frontend/.env.local` -> `SANJAYA_ADMIN_TOKEN`
- `backend/.env` -> `SANJAYA_ADMIN_TOKEN`

Default token in Docker compose: `dev-admin-token`

Admin routes:
- `/admin/insights`
- `/admin/role-requests`
- `/admin/drafts/[draftId]`

## Deep-Dive Links
- Submission document: `docs/submission.md`
- Demo script: `docs/demo-script.md`
- Operations runbook: `docs/ops-runbook.md`
- Integration options: `docs/integration-options.md`

## Backend Tests
```bash
cd backend
pytest
```

## Troubleshooting
- Ports in use (`8000`/`3000`): stop existing processes or change ports.
- Frontend cannot reach backend: verify `NEXT_PUBLIC_API_BASE_URL` in `frontend/.env.local`, then restart frontend.
- Admin `401/403`: ensure matching `SANJAYA_ADMIN_TOKEN` in backend and frontend env files.
- Backend startup data error: ensure `data/processed/*.json` files exist; check `/health` and backend logs.
