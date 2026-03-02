# Sanjaya AI – Explainable Career Roadmaps

Sanjaya AI helps students see how their **courses lead to a real job** (for example, **AI Engineer**) and gives universities an **advisor/admin surface** to govern roles, skills, and evidence.

Students get a **credit‑aware, prerequisite‑safe roadmap** plus explainable AI; advisors get analytics, unknown‑role requests, and publish gates for new roles.

---

## Project structure

- `backend/` – FastAPI backend, planning/validation pipeline, advisor and job‑match endpoints.
- `frontend/` – Next.js + React UI for students, advisors, and admins.
- `data/processed/` – curated datasets (courses, roles, skills, evidence, projects, role reality).
- `scripts/` – data preparation and mapping tools.
- `docs/` – project documentation (for judges, handoff notes, etc.).

For deeper backend details, see [`backend/README.md`](backend/README.md).

---

## Quickstart – run locally

### 1. Backend

From the project root:

```powershell
cd backend
python -m pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

Backend:
- API docs: `http://127.0.0.1:8000/docs`
- Health: `http://127.0.0.1:8000/health`

> On macOS/Linux you can use the same commands without `powershell` and with your default shell.

### 2. Frontend

From the project root:

```powershell
cd frontend
copy .env.local.example .env.local  # or: cp .env.local.example .env.local
npm install
npm run dev
```

Frontend:
- `http://127.0.0.1:3000`

By default the frontend talks to the backend at `http://127.0.0.1:8000`.  
You can override this by setting `NEXT_PUBLIC_API_BASE_URL` in `.env.local` if needed.

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
     - Click **“Load AI / Data job”** to use the AI Engineer Intern preset.
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

## Environment & security

- Backend environment variables live in [`backend/.env.example`](backend/.env.example).
  - Copy to `backend/.env` and fill in your own keys:
    - `LLM_PROVIDER` (e.g. `auto`, `openai`, `groq`, `gemini`).
    - Provider keys such as `OPENAI_API_KEY`, `GROQ_API_KEY`, or `GEMINI_API_KEY`.
    - Feature flags like `SANJAYA_ENABLE_LLM_STORYBOARD`, `SANJAYA_ENABLE_LLM_ADVISOR`, `SANJAYA_ENABLE_LLM_JOB_EXTRACTOR`.
- Frontend environment variables (optional) live in `frontend/.env.local`:
  - `NEXT_PUBLIC_API_BASE_URL` – override backend URL (defaults to `http://127.0.0.1:8000`).

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

### Frontend checks (optional)

If you add or enable TypeScript/ESLint checks, you can expose them via npm scripts such as:

```powershell
cd frontend
npm run lint
npm run typecheck
```

Check `frontend/package.json` for the exact scripts configured in your environment.

---

## For judges and reviewers

- **High‑level overview and methodology** (including generative AI usage and access instructions) are documented in `docs/submission.md` and can be exported as a 2‑page PDF for submission.
- The recommended demo scenario is the **AI Engineer** path described above; it exercises:
  - Core planning and validation.
  - Skill coverage, gaps, and projects.
  - Job posting match.
  - Advisor Q&A and admin analytics.

---

## Optional: run with Docker

If you prefer Docker, you can use the existing compose file:

```bash
docker compose up --build
```

Endpoints:
- Frontend: `http://localhost:3000`
- Backend health: `http://localhost:8000/health`

Notes:
- Persistent data is mounted via `./data:/app/data` (processed JSON, vector store, ops DB).
- Default admin token in compose: `dev-admin-token` (`SANJAYA_ADMIN_TOKEN`).
