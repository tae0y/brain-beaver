# Copilot instructions for BrainBeaver

This repo is a dockerized knowledge-graph toolkit. Vite/React UI visualizes networks; a Python FastAPI backend manages concepts/networks/references with PostgreSQL + pgvector; RabbitMQ is available for messaging; observability (Grafana/Loki/Tempo, OTEL, .NET Aspire AppHost) is scaffolded.

## Architecture
- UI: `src/Node.ViteUI` (Vite + React, Cosmograph). Calls backend HTTP APIs.
- Backend: `src/Python.FastAPI` with domain routers: concepts, networks, references, extract.
  - Pattern: `{domain}/{domain}handler.py` (APIRouter) → `{domain}service.py` → `{domain}repository.py` → DB via `common.db.DB` (SQLAlchemy).
  - Response contract: always return `ResponseDTO(status, message, data)` wrapped by `JSONResponse(status_code=..., content=dict(dto))`.
- Data: PostgreSQL with `pgvector` (embedding column `vector(4096)`). Init SQL lives in `docker/configs/initdb.d/`.
- Messaging: RabbitMQ container configured; extract/network flows are designed to publish/consume (see `docker/configs/mq.conf/`).
- Observability: OTEL instrumentation and Aspire host are present but mostly commented; enable as needed.

## Run and key endpoints
- Docker-first workflow (recommended): `docker/docker-compose.yml` brings up backend (8112→8111), UI (5173), Postgres (5432), RabbitMQ (5672/15672), pgAdmin (5050), Portainer (9000), backup (8080).
  - Backend Swagger: http://localhost:8112/docs (UVicorn listens on 8111 inside the container).
  - UI dev: http://localhost:5173 (hot reload via bind mounts).
- Local backend (optional): run UVicorn in `src/Python.FastAPI` on 8111; CORS allows `http://localhost:5173` and `http://bws_vite:5173`.

## Backend API patterns you must follow
- Router prefix/tag per domain: e.g., concepts at `/api/concepts` (`concepts/conceptshandler.py`). Keep filenames consistent (note: current repo uses `conceptsreposigory.py`).
- Convert ORM to dict before responding (see handlers using `obj.to_dict()` then `json.dumps(..., default=str)`).
- Use SQLAlchemy sessions from `common.db.DB`; handle commit/rollback/close explicitly in repositories.
- pgvector similarity: use `embedding.cosine_distance`, `max_inner_product`, `l1_distance` for ranking.
- Example requests:
  - POST `/api/extract/check-budget` body: `{ datasourcetype: "markdown", datasourcepath: "/path", options: { max_budget: 1000, reason_model_name, embed_model_name } }`.
  - POST `/api/networks/engage` body: `{ operation: "cosine_distance" }` to link related concepts by embeddings.

## Conventions, deps, and tests
- Shared response model: `common/models/responseDTO.py`; keep the status/message/data envelope.
- LLM/embeddings: default to Ollama via `OLLAMA_HOST` (see compose); OpenAI is optional and passed via env when used.
- Tests: `src/Python.FastAPI/tests/{unit,integration}`. DB state persists under `docker/volumes/postgresql_volume/`; init scripts run on first bootstrap.

## Gotchas
- Port mapping: outside 8112 → inside 8111 for backend; Swagger URL differs between docker and local.
- Compose mounts `src/Node.ViteUI` and `src/Python.FastAPI` for live dev; restart containers after dependency changes.
- Security: follow `.github/instructions/security-and-owasp.instructions.md`. Do not hardcode secrets; prefer env/secrets.

If you need deeper details (enabling OTEL/Aspire, exact test commands, DB helper API), say which section to expand and I’ll refine this guide.
