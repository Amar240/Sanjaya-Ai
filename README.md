# Sanjaya AI – Explainable Career Roadmaps

Sanjaya AI connects a student’s course plan to concrete roles in the job market (for example, **AI Engineer**), with a planner that respects credits and prerequisites and an advisor surface for universities.
This repo is set up so a judge can unzip, follow one short section in this README, and run the full demo.

---

## Quick start for judges

From the unzipped folder (`SanjayaAi/`), choose **either Option A or Option B**.

### Option A – Local run (Python + Node)

**1. Start the backend (FastAPI)**

Windows (PowerShell):

```powershell
cd backend
python -m pip install -r requirements.txt
copy .env.example .env
uvicorn app.main:app --reload --port 8000
```

macOS / Linux:

```bash
cd backend
python3 -m pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload --port 8000
```

Check: `http://127.0.0.1:8000/health` should return `{"status":"ok"}`.

**2. Start the frontend (Next.js)**

Open a **second** terminal in the project root:

Windows (PowerShell):

```powershell
cd frontend
copy .env.local.example .env.local
npm install
npm run dev
```

macOS / Linux:

```bash
cd frontend
cp .env.local.example .env.local
npm install
npm run dev
```

Then open `http://127.0.0.1:3000/` in a browser.

### Option B – Run with Docker Compose

From the project root (`SanjayaAi/`):

```bash
docker compose up --build
```

Then open:

- App: `http://localhost:3000`  
- Backend health: `http://localhost:8000/health`

> LLM features are optional. With the default `.env.example` / `.env.local.example` the planner, validation, and course‑wise roadmap work without any API keys.

---

## One‑click helper scripts (optional)

If you prefer, you can use the helper scripts in the project root instead of typing the individual commands:

- Windows (PowerShell):

  ```powershell
  ./run_local.ps1
  ```

- macOS / Linux:

  ```bash
  chmod +x run_local.sh   # first time only
  ./run_local.sh
  ```

These scripts install dependencies if needed, copy example env files, and open two terminals: one for the backend and one for the frontend.

---

## 90‑second demo checklist

If you only have a minute or two, you can skim this flow:

1. **Generate a roadmap**
   - On `http://127.0.0.1:3000/`, click **“Build my roadmap”**.
   - Fill intake for an **Undergraduate, Core, AI Engineer** plan (degree total credits = 128).
   - Click **“Generate my roadmap”** to see the dashboard.

2. **Inspect the course‑wise plan and validation**
   - Scroll through the semesters to see course titles, credits, and total credits per term.
   - Look at the validation summary and open the full list to see codes such as `TOTAL_CREDITS_UNDER_DEGREE` or `PREREQ_ORDER`.

3. **Use Job Match and Advisor Q&A**
   - In **“Your path in 5 steps”**, open **“Reality Check (Job Posting)”**, load the AI/Data preset, and click **“Extract & Match”**.
   - Switch to **“Advisor Q&A”** and ask “Why did you recommend this role?” to see an explanation tied back to skills/courses.

The rest of this README goes into more detail if you need it.

---

## Why not just ChatGPT?

> **Why Sanjaya instead of “just a chatbot?”**

- **Chatbots can explain but can’t reliably verify prereqs/credits/catalog**  
  A generic LLM doesn’t know your official catalog, offerings, or degree total rules.
- **Sanjaya outputs structured plans + validation codes + resolvable citations**  
  Each plan has machine‑checkable `PlanError` codes and evidence IDs that can be traced back to sources.
- **Sanjaya includes governance: advisor dashboard + publish gates**  
  Admin views show usage, unknown roles, and readiness gates before a role goes live.

---

## Project structure

- `backend/` – FastAPI backend, planning/validation pipeline, advisor and job‑match endpoints.
- `frontend/` – Next.js + React UI for students, advisors, and admins.
- `data/processed/` – curated datasets (courses, roles, skills, evidence, projects, role reality).
- `scripts/` – data preparation and mapping tools.
- `docs/` – project documentation (for judges, handoff notes, etc.).

For deeper backend details, see [`backend/README.md`](backend/README.md).

---

## Access for evaluation (run instructions)

Sanjaya can be evaluated either via **local Python + Node** or with **Docker Compose**. Both routes expose the same URLs and behavior.

### Option A – Local run (Python + Node)

#### Backend (FastAPI)

**Windows PowerShell**

```powershell
cd backend
python -m pip install -r requirements.txt

# optional: enable LLM features
copy .env.example .env   # or: cp .env.example .env (Git Bash)
# edit .env to add OPENAI_API_KEY / GROQ_API_KEY / GEMINI_API_KEY if desired

uvicorn app.main:app --reload --port 8000
```

**macOS / Linux (bash/zsh)**

```bash
cd backend
python3 -m pip install -r requirements.txt

cp .env.example .env
# edit .env to add OPENAI_API_KEY / GROQ_API_KEY / GEMINI_API_KEY if desired

uvicorn app.main:app --reload --port 8000
```

Backend endpoints:

- Health: `http://127.0.0.1:8000/health`
- API docs: `http://127.0.0.1:8000/docs`

#### Frontend (Next.js)

**Windows PowerShell**

```powershell
cd frontend
copy .env.local.example .env.local   # or: cp .env.local.example .env.local
npm install
npm run dev
```

**macOS / Linux**

```bash
cd frontend
cp .env.local.example .env.local
npm install
npm run dev
```

Frontend:

- App: `http://127.0.0.1:3000/`

Environment variables:

- `frontend/.env.local`:
  - `NEXT_PUBLIC_API_BASE_URL` – backend base URL (defaults to `http://127.0.0.1:8000`).
  - `SANJAYA_ADMIN_TOKEN` – token for accessing `/admin/*` routes in the UI (e.g. `dev-admin-token`).

Backend `.env` (copied from `.env.example`):

- `LLM_PROVIDER` (e.g. `auto`, `openai`, `groq`, `gemini`).
- Provider keys: `OPENAI_API_KEY`, `GROQ_API_KEY`, `GEMINI_API_KEY`.
- Feature flags: `SANJAYA_ENABLE_LLM_STORYBOARD`, `SANJAYA_ENABLE_LLM_ADVISOR`, `SANJAYA_ENABLE_LLM_JOB_EXTRACTOR`.
- `SANJAYA_ADMIN_TOKEN` – must match the token used by the frontend for `/admin/*`.

> **Admin URLs** (require matching `SANJAYA_ADMIN_TOKEN`):
>
> - `http://127.0.0.1:3000/admin/insights`
> - `http://127.0.0.1:3000/admin/role-requests`
> - `http://127.0.0.1:3000/admin/drafts/[draftId]`

### Option B – Run with Docker Compose

If you prefer Docker, you can use the existing compose file from the repo root:

```bash
docker compose up --build
```

Exposed endpoints:

- Frontend: `http://localhost:3000`
- Backend health: `http://localhost:8000/health`
- Backend docs: `http://localhost:8000/docs`

Docker notes:

- Persistent data is mounted via `./data:/app/data` (processed JSON, vector store, ops DB).
- Default admin token in compose: `dev-admin-token` (`SANJAYA_ADMIN_TOKEN` for both backend and frontend).
- Compose already sets `NEXT_PUBLIC_API_BASE_URL=http://backend:8000` for the frontend container.

---

## AI Engineer demo path (recommended flow)

This is the path we recommend judges follow for a 2–3 minute demo.

1. **Landing page (`/`)**
   - Open `http://127.0.0.1:3000/`.
   - Read the hero: “See how your courses lead to a real job.”
   - Click **“Build my roadmap”** to jump to the intake form.

2. **Build your plan – intake**
   - Level: **Undergraduate**.
   - Mode: **Core – single career focus**.
   - Degree total credits: **128**.
   - Reasonable min/target/max credits and hours per week.
   - Interests: include **AI / Machine Learning** and **Software Engineering**.
   - Goal: **Pick a role** and choose **AI Engineer** from the list.
   - Click **“Generate my roadmap”**.

3. **Plan dashboard – “Your path in 5 steps”**
   - The page scrolls to the **Plan dashboard** for AI Engineer.
   - At the top you will see:
     - **Selected Role**: AI Engineer.
     - **Skill Coverage %**.
     - A short validation summary (including any warnings such as being below 128 total credits).
   - In the `"Your path"` section, use the tabs in the 5‑step “brain picture”:
     - **Target Reality** – USA tasks and salary band with source links.
     - **Skill Gaps** – which skills are covered vs missing, plus project ideas.
     - **Fusion Opportunities** – optional fusion data when available.
     - **Career Storyboard** – generate a plain‑English narrative of the path.
     - **Reality Check (Job Posting)** – paste or load a job posting.

4. **Job Match (Reality Check)**

   - On the **Reality Check (Job Posting)** tab:
     - Click **“Load AI / Data job”** (Preset 1, AI Engineer‑style posting).
     - Click **“Extract & Match”**.
   - The UI shows:
     - How many skills from the job posting were mapped.
     - Which are already **covered** by the roadmap.
     - Which are **missing** or **out‑of‑scope**.
     - Recommended **projects** to close missing skills.

5. **Advisor Q&A**
   - Switch to the **“Advisor Q&A”** section in the dashboard tabs.
   - Ask: **“Why did you recommend this role?”** or **“Is this plan feasible?”**.
   - The advisor responds with an answer, reasoning points, and citations back to skills/courses/evidence.

6. **Advisor/admin dashboard**
   - `http://127.0.0.1:3000/admin/insights` – Advisor Insights:
     - Top roles selected, top error codes, advisor intents, unknown role requests.
   - `http://127.0.0.1:3000/admin/role-requests` – Role Requests Inbox:
     - Aggregated unknown role queries and candidate role mappings.
   - `http://127.0.0.1:3000/admin/drafts/[draftId]` – Draft Roles & Readiness Gates:
     - Create roles and see publish gates (skills evidence, role reality, project coverage).

---

## How to read the course‑wise plan and validation

When I walk through the demo, I usually highlight two things: **how courses are structured semester‑by‑semester**, and **how validation explains problems in the plan**.

### Course‑wise structure (semester view)

- The roadmap is grouped by **semester**, with each card showing the courses the planner scheduled in that term.  
- Inside a semester you can see:
  - Course code and title.
  - Credits per course and the **total credits** for that semester.
  - A short note about what the course contributes (for example, which skills it supports).
- Across all semesters, the total credits add up to the **degree total credits** you set in the intake (e.g., 128 for undergraduate, 33 for graduate), unless you intentionally keep it lower for flexibility.

In the demo, I usually scroll down the semesters and point out:

- How introductory courses appear earlier, and advanced / capstone courses appear later.  
- Where AI‑related or security‑related courses show up relative to core math / CS foundations.  
- That the plan still looks like a normal university degree plan, not a random list of courses.

### Validation panel and messages

On the same dashboard, there is a **validation / warnings section** that explains whether the plan is academically sound. It shows:

- **Green / OK** when prerequisites, credit limits, and degree totals are respected.  
- **Warnings** when there are soft issues (for example, being a bit under the total degree credits).  
- **Errors** when there are hard issues (for example, a course is taken before its prerequisite).

Some of the important validation codes we use:

- `TOTAL_CREDITS_OVER_DEGREE` – the sum of all planned credits is higher than the degree total (e.g., above 128 for UG).  
- `TOTAL_CREDITS_UNDER_DEGREE` – the plan is below the degree total; this is usually shown as a warning so the student can add electives.  
- `CREDIT_OVER_MAX` – a single semester exceeds the maximum credit load the student said they can handle.  
- `PREREQ_ORDER` – a course appears before its prerequisite.

In a typical walkthrough I:

1. Show the **top‑level summary** (selected role, skill coverage, and a short validation sentence).  
2. Open the **full validation list** to show the exact codes and human‑readable explanations.  
3. Scroll down to a specific semester or course that is referenced by a validation message, so it is clear how the planner arrived at that decision.

The key point for reviewers is that the **validation is deterministic and explainable**: every warning or error code can be traced back to course data, credit rules, and the student’s own inputs, not to a free‑form LLM decision.

---

## Creating the zip for submission

To create the zip you will upload:

- Make sure you are one level **above** the project folder (so you see `SanjayaAi/`).
- Include:
  - `SanjayaAi/backend/`
  - `SanjayaAi/frontend/`
  - `SanjayaAi/data/`
  - `SanjayaAi/docs/`
  - `SanjayaAi/README.md`
  - `SanjayaAi/run_local.ps1`, `SanjayaAi/run_local.sh`
- Exclude local environments like `.venv/`, `node_modules/`, and any `.env` files (they are already covered by the `*.example` templates).

Examples:

- Windows Explorer: right‑click the `SanjayaAi` folder → **Send to → Compressed (zipped) folder**.  
- macOS / Linux (from one directory up):

  ```bash
  zip -r sanjaya-ai.zip SanjayaAi -x "*/.venv/*" "*/node_modules/*" "*/.env" "*/.env.*"
  ```

The resulting zip (`sanjaya-ai.zip`) is what the judge can download, unzip, and run using the Quick start section at the top of this README.

## What is deterministic vs what uses LLM?

Sanjaya is designed so that **critical academic decisions are deterministic**, and LLMs are limited to text‑level tasks.

- **Deterministic (no LLM)**
  - Planner: semester scheduling, prerequisite enforcement, credit limits, degree total checks.
  - Verifier: `PlanError` codes (e.g., `PREREQ_ORDER`, `CREDIT_OVER_MAX`, `TOTAL_CREDITS_OVER_DEGREE`).
  - Evidence linking and citation IDs: mapping plan elements to evidence and sources.
  - Advisor governance: which roles are available, readiness gates, error aggregation.

- **RAG‑only (retrieval, not generation deciding courses)**
  - Role retrieval from calibrated market data (roles_market*).
  - Evidence retrieval: which sources support which role‑skill pairs.
  - Course‑purpose linking: which course supports which skill, with citations.

- **LLM‑optional (text only; strictly constrained)**
  - **Storyboard:** rewrite‑only; LLM turns a structured plan into a human‑readable narrative, with section titles and citations supplied by the system.
  - **Job text extraction:** LLM (or deterministic fallback) parses pasted job descriptions into a strict JSON schema (required skills, preferred skills, tools). Matching to skills and courses is deterministic.

> **Important:**  
> - The LLM **never decides which courses are in the plan** or whether a plan is feasible.  
> - The LLM **never bypasses validation or degree rules**.  
> - The system explicitly states that **there are no job guarantees**; job match is guidance only.

---

## Data & sources

Core curated data is under `data/processed/`. Key files:

| File                                      | Purpose                                                                                  |
|-------------------------------------------|------------------------------------------------------------------------------------------|
| `courses.json`                            | Catalog of courses, IDs, titles, credits, and metadata used by the planner.             |
| `course_skills.json` / `course_skills_curated.json` | Mapping of courses to skills; curated version is used first, with heuristics as fallback. |
| `roles_market.json` / `roles_market_calibrated.json` | Market‑grounded roles (e.g., AI Engineer, Cybersecurity Analyst) with calibrated weights. |
| `skills_market.json`                      | Canonical skill taxonomy (IDs, names, categories) used across roles, courses, and jobs. |
| `role_skill_evidence.json` + `market_sources.json` | Evidence snippets and source metadata linking roles/skills to labor/market sources.      |
| `role_reality_usa.json`                  | USA‑focused role “reality” data: tasks, salary percentiles, and evidence source IDs.    |
| `project_templates.json`                  | Project ideas keyed to skills, used for gap projects and job‑match recommendations.     |

These datasets are versioned in Git so judges can inspect and validate them.

---

## Environment & security

- Backend environment variables live in [`backend/.env.example`](backend/.env.example).
  - Copy to `backend/.env` and fill in your own keys:
    - `LLM_PROVIDER` (e.g. `auto`, `openai`, `groq`, `gemini`).
    - Provider keys such as `OPENAI_API_KEY`, `GROQ_API_KEY`, or `GEMINI_API_KEY`.
    - Feature flags like `SANJAYA_ENABLE_LLM_STORYBOARD`, `SANJAYA_ENABLE_LLM_ADVISOR`, `SANJAYA_ENABLE_LLM_JOB_EXTRACTOR`.
    - `SANJAYA_ADMIN_TOKEN` (must match the token used by the frontend for admin routes).
- Frontend environment variables (optional) live in `frontend/.env.local`:
  - `NEXT_PUBLIC_API_BASE_URL` – override backend URL (defaults to `http://127.0.0.1:8000`).
  - `SANJAYA_ADMIN_TOKEN` – token sent to `/admin/*` APIs.

**Important:** do **not** commit real API keys. Always:

1. Copy from `backend/.env.example` into `backend/.env`.
2. Keep `.env` files out of version control.

---

## Tests and quality checks

### Backend tests

From the project root:

```powershell
cd backend
python -m pip install -r requirements.txt
pytest
```

The test suite covers:

- Plan validation and error codes.
- Evidence integrity for skills and courses.
- Job match behavior for covered/missing/out‑of‑scope skills.
- Advisor behavior for “why this role” / “why not this alternative” questions.
- Role drafts, readiness gates, and integration smoke tests.

### Frontend checks (optional)

If you add or enable TypeScript/ESLint checks, you can expose them via npm scripts such as:

```powershell
cd frontend
npm run lint
npm run typecheck
```

Check `frontend/package.json` for the exact scripts configured in your environment.

---

## Troubleshooting (common issues)

- **Ports 8000 or 3000 already in use**
  - Symptom: backend or frontend fails to start with “address already in use”.
  - Fix: stop existing processes using those ports (or change `--port` in `uvicorn` / `npm run dev`).

- **CORS errors or frontend shows network failures**
  - Symptom: browser console shows CORS or network errors calling `http://127.0.0.1:8000`.
  - Fix: ensure `NEXT_PUBLIC_API_BASE_URL` in `frontend/.env.local` matches the running backend URL and restart `npm run dev`.

- **Admin pages return 401/403**
  - Symptom: `/admin/insights` or `/admin/role-requests` show unauthorized.
  - Fix: set `SANJAYA_ADMIN_TOKEN` in both backend `.env` and frontend `.env.local` (or rely on the default from `docker-compose.yml`, e.g. `dev-admin-token`) and restart services.

- **Startup validation fails or data missing**
  - Symptom: backend logs mention missing `data/processed` files or integrity checks.
  - Fix: ensure the `data/processed/*.json` files from the repo are present and readable; check `http://127.0.0.1:8000/health` and the backend console for detailed error messages.

- **Docker volume / permissions issues**
  - Symptom: Docker containers start but backend cannot read/write `./data`.
  - Fix: ensure the repo is on a filesystem Docker can mount, and that your user has read/write permissions on the `data/` directory; restart `docker compose up --build`.

---

## For judges and reviewers

- **High‑level overview and methodology** (including generative AI usage and access instructions) are documented in `docs/submission.md` and can be exported as a 2‑page PDF for submission.
- The recommended demo scenario is the **AI Engineer** path described above; it exercises:
  - Core planning and validation.
  - Skill coverage, gaps, and projects.
  - Job posting match.
  - Advisor Q&A and admin analytics.
