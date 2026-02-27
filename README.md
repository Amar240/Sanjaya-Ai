# Sanjaya AI

Grounded, explainable advising platform:
- role -> skills -> courses -> semester roadmap
- prerequisite-safe planning
- evidence-backed skill rationale
- Fusion mode (domain + tech readiness with unlock skills)
- conversational intake chat (Groq-backed when configured)
- advisor Q&A with defended answers and citations

## Project Structure

- `backend/` FastAPI + LangGraph + validators
- `frontend/` Next.js UI
- `data/processed/` curated datasets and mappings
- `scripts/` data preparation and mapping tools
- `docs/` notes and handoff docs

## Run Backend

```powershell
cd backend
python -m pip install -r requirements.txt
uvicorn app.main:app --reload
```

Optional for LLM conversational intake:

```powershell
$env:GROQ_API_KEY="your_key_here"
$env:GROQ_MODEL="llama-3.3-70b-versatile"
uvicorn app.main:app --reload
```

Backend:
- API docs: `http://127.0.0.1:8000/docs`
- Health: `http://127.0.0.1:8000/health`

## Run Frontend

```powershell
cd frontend
copy .env.local.example .env.local
npm install
npm run dev
```

Frontend:
- `http://127.0.0.1:3000`

## Run With Docker

```bash
docker compose up --build
```

Endpoints:
- Frontend: `http://localhost:3000`
- Backend health: `http://localhost:8000/health`

Notes:
- Persistent data is mounted via `./data:/app/data` (processed JSON, Chroma, ops DB).
- Default admin token in compose: `dev-admin-token` (`SANJAYA_ADMIN_TOKEN`).

## Demo Flow

1. Open frontend.
2. Fill intake fields and select a role.
3. Generate plan.
4. Review:
   - skill coverage
   - semester roadmap
   - course purpose cards
   - evidence panel
   - agent trace
