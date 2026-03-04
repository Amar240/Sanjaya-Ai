Sanjaya AI 2.0 — Verified Roadmaps from Courses → Skills → Real Jobs (USA)

**Deterministic planner + verifier + evidence-grounded RAG** to generate **prerequisite-safe, credit-aware**, job-aligned semester roadmaps—built to prevent “market shock” for students and to support advisors with transparent governance.

> **Design principle:** separate **truth** from **language**  
> - **Truth/correctness** is decided by deterministic planning + deterministic verification (academic constraints).  
> - **Grounding** comes from retrieval that attaches evidence to role/skill claims.  
> - **LLMs are optional** and restricted to phrasing under strict schemas (they cannot change verified decisions).

---

## Why this exists (problem)
Undergraduate students—especially the “middle layer”—often choose courses without a clear **Skills → Job → Money** picture. Many graduate with silent gaps (SQL, ML deployment, cloud basics, evaluation practices), and those gaps show up as **market shock** during recruiting.

This is harder for interdisciplinary students. A “catalyst” subject (often computer science) can unlock fusion careers like **Computational Chemistry, Bioinformatics, Health AI**, but students need early visibility into pathways and readiness gaps.

Advisors also need support at scale: a governed add-on that keeps role-to-skill mappings maintainable and makes recommendations transparent, reviewable, and auditable.

---

## What Sanjaya AI delivers
1. **Verified roadmap (term-by-term)**  
   Prerequisite-safe, credit-aware, term-offering aware semester plans.

2. **Skill coverage map**  
   Courses → skills → role requirements, with missing skill clusters highlighted.

3. **Evidence-linked explanations**  
   “Why this plan/course” and “why not alternatives,” backed by evidence entries.

4. **Advisor governance layer**  
   Draft → review → publish workflow, readiness gates, and versioned mappings/audit logs.

---

## Repository structure
```txt
SanjayaAi/
  backend/
    app/
    tests/
    docs/
    .env.example
    requirements.txt
    Dockerfile
  frontend/
    app/
    components/
    lib/
    .env.local.example
    package.json
    Dockerfile
  data/
    processed/
    raw/
    analytics/
    ops/
    chroma/
    curation_drafts/
  docs/
  scripts/
  docker-compose.yml
  README.md
  run_local.ps1
  run_local.sh
```

## Quickstart (local, recommended)
### 1) Backend (FastAPI)
```powershell
cd backend
python -m pip install -r requirements.txt
copy .env.example .env
uvicorn app.main:app --reload --port 8000
```

Open:

- Health: http://127.0.0.1:8000/health
- Swagger: http://127.0.0.1:8000/docs

### 2) Frontend (Next.js)

Open a new terminal:

```powershell
cd frontend
copy .env.local.example .env.local
npm install
npm run dev
```

Open:

- UI: http://127.0.0.1:3000

Important: set `NEXT_PUBLIC_API_BASE_URL` in `frontend/.env.local` if your frontend expects an explicit backend base URL.
Example:

```env
NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000
```

## One-command Docker (optional)
```bash
docker compose up --build
```

## Environment variables (what matters)
### Backend (`backend/.env`)
```env
LLM_PROVIDER=auto
GROQ_API_KEY=
GROQ_MODEL=llama-3.3-70b-versatile
OPENAI_API_KEY=
OPENAI_MODEL=gpt-4o-mini
GEMINI_API_KEY=
GEMINI_MODEL=gemini-2.0-flash

SANJAYA_ENABLE_LLM_STORYBOARD=0
SANJAYA_ENABLE_LLM_ADVISOR=0
SANJAYA_ENABLE_LLM_JOB_EXTRACTOR=0
```

Recommended default for judging: keep all `SANJAYA_ENABLE_*` toggles at `0` to demonstrate deterministic behavior (no dependency on external LLMs). Turn them on only if you want to show narrative/storyboard enrichment.

Common optional variables used in code:

- `SANJAYA_BACKEND_URL`
- `SANJAYA_ADMIN_TOKEN`, `SANJAYA_ADMIN_USER`
- `SANJAYA_OPS_DB_PATH` (default: `data/ops/sanjaya_ops.db`)
- `SANJAYA_CHROMA_DIR` (default: `data/chroma/`)
- `SANJAYA_ANALYTICS_DIR` (default: `data/analytics/`)

### Frontend (`frontend/.env.local`)
```env
NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000
```

## API overview (backend)
### Core

- `GET /health`
- `GET /roles`
- `GET /catalog/course/{course_id}`
- `POST /plan`
- `POST /chat`
- `POST /advisor/ask`
- `POST /plan/storyboard`
- `POST /job/match`

### Admin (governance)

- `GET /admin/insights/summary`
- `GET /admin/role-requests`
- `GET /admin/role-requests/{role_request_id}`
- `POST /admin/role-requests/{role_request_id}/ignore`
- `POST /admin/role-requests/{role_request_id}/map`
- `POST /admin/role-requests/{role_request_id}/create-role`
- `POST /admin/drafts`
- `GET /admin/drafts/{draft_id}/roles`
- `GET /admin/drafts/{draft_id}/roles/readiness`
- `POST /admin/drafts/{draft_id}/roles`
- `PUT /admin/drafts/{draft_id}/roles/{role_id}`
- `DELETE /admin/drafts/{draft_id}/roles/{role_id}`
- `POST /admin/drafts/{draft_id}/publish`

### Integration (MyUD posture)

- `POST /integration/myud/launch`
- `GET /integration/myud/plan/{plan_id}/summary`

## Reproducible judge demo (90 seconds)

This is the fastest way to validate the system end-to-end.

### Step A — Confirm backend + data are loaded

Open:

`GET http://127.0.0.1:8000/health`

✅ Expect a JSON response (ideally including dataset/version info).  
(Suggested improvement: include counts for courses/roles/skills and the data_version hash.)

### Step B — Generate a plan (`POST /plan`)

Sample request:

```json
{
  "student_profile": {
    "level": "UG",
    "mode": "CORE",
    "goal_type": "select_role",
    "confidence_level": "medium",
    "hours_per_week": 6,
    "current_semester": 1,
    "start_term": "Fall",
    "include_optional_terms": false,
    "completed_courses": [],
    "min_credits": 12,
    "target_credits": 15,
    "max_credits": 17,
    "interests": ["ai", "data"]
  },
  "preferred_role_id": "ROLE_AI_ENGINEER"
}
```

Response shape (high level):

```json
{
  "plan_id": "hex-id",
  "data_version": "hash",
  "selected_role_title": "AI Engineer",
  "skill_coverage": [{"required_skill_id":"SK_PYTHON","covered":true,"matched_courses":["CISC-108"]}],
  "semesters": [{"term":"Fall","courses":["CISC-108"],"total_credits":3,"warnings":[]}],
  "validation_errors": [],
  "evidence_panel": []
}
```

### Step C — Prove verification works (break something on purpose)

Try a profile or constraint that should cause an invalid plan (e.g., unrealistic credit bounds or missing prereqs).  
✅ The correct behavior is: structured validation errors (not a hallucinated explanation).

### Step D — Ask the advisor endpoint (grounded explanation)

Call `POST /advisor/ask` and confirm:

- it references plan context
- it produces evidence/citations when available
- it does not override verifier constraints

## Data (where “truth” lives)

All primary datasets live under `data/processed/` (JSON/CSV), with `data/raw/` reserved for scraped catalogs.

Key files:

- `courses.json` — normalized course catalog
- `roles_market.json` — market-grounded roles
- `roles_market_calibrated.json` — calibrated role set (auto-used if present)
- `skills_market.json` — skill taxonomy
- `course_skills.json` — course-skill mappings
- `course_skills_curated.json` — curated overrides
- `role_skill_evidence.json` — evidence links for role-skill claims
- `market_sources.json` — metadata for evidence sources
- `role_reality_usa.json` — tasks + salary bands
- `project_templates.json` — projects for closing missing skill clusters
- `fusion_roles.json`, `fusion_packs_usa.json` — interdisciplinary fusion mode

Other stores:

- `data/analytics/events.jsonl` — analytics/event logs
- `data/ops/sanjaya_ops.db` — ops/admin sqlite database
- `data/chroma/` — vector index (e.g., `chroma.sqlite3` + embeddings files)

## What makes this trustworthy (not “just a chatbot”)

Most systems can produce plausible advice. Sanjaya AI is designed to be safe, auditable, and maintainable:

- Deterministic planner + verifier enforce academic constraints explicitly.
- Structured errors explain why a plan fails and how to fix it.
- Evidence panel ties role/skill claims to sources for transparency.
- Advisor governance ensures role/skill mappings can be reviewed and updated over time.

## Running tests (recommended)

Backend includes a test suite in `backend/tests/`.
Run:

```powershell
cd backend
pytest -q
```

(If tests require environment variables or seeded data, document it in `backend/docs/`.)

## Admin governance flow (high level)

- Role requests appear in `/admin/role-requests`
- Advisor/admin maps or creates roles
- Work happens in drafts (`/admin/drafts`)
- Readiness is checked (`/admin/drafts/{draft_id}/roles/readiness`)
- Publish promotes drafts into calibrated market mappings

This is the mechanism that keeps the system accurate over time.

## Screenshots (recommended)

Add two images under `docs/images/` and link them here:

- Roadmap: “Your path in 5 steps” after plan generation
- Skill gaps + evidence panel visible (citations)

Example:

![Roadmap](docs/images/roadmap.png)
![Skill Gaps + Evidence](docs/images/skill_gaps_evidence.png)
