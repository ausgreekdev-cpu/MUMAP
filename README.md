# Multi-Agent Orchestration Platform

[![CI](https://github.com/ausgreekdev-cpu/MUMAP/actions/workflows/ci.yml/badge.svg)](https://github.com/ausgreekdev-cpu/MUMAP/actions/workflows/ci.yml)

A modern, full-stack platform for building and coordinating AI agents that work together.

## Quick Install

### Option 1: Docker (Recommended)
```bash
# One command to install and run
docker run -d \
  --name multi-agent \
  -p 8000:8000 \
  -v multi-agent-data:/data \
  multi-agent-platform:latest
```

### Option 2: Docker Compose
```bash
git clone https://github.com/yourrepo/multi-agent-platform.git
cd multi-agent-platform
docker-compose up -d
```

### Option 3: Install Script
```bash
curl -sSL https://raw.githubusercontent.com/yourrepo/install.sh | bash
```

### Option 4: Manual Setup
```bash
# Backend
pip install -r backend/requirements.txt
python -m uvicorn backend.main:app --reload

# Frontend (optional)
cd frontend
npm install
npm run dev
```

## Access the Platform

| Service | URL |
|---------|-----|
| API | http://localhost:8000 |
| API Docs | http://localhost:8000/docs |
| Frontend | http://localhost:5173 |

## Features

### Agent Management
- Create and configure AI agents
- Define capabilities (skills)
- Monitor status in real-time
- Load balancing across agents

### Task Orchestration
- Create tasks with priorities
- Auto-assign to best agent
- Track task progress
- View execution history

### Dashboard
- Real-time statistics
- Live platform health card (API/DB/Redis/WebSocket)
- Task queue overview
- WebSocket-driven live refresh

### Marketplace
- Install agent templates with one click
- Category browsing and search
- Pre-configured agent blueprints

### Settings
- Profile and password management
- Notification preferences (persisted per user)
- API key management (generate/revoke, shown once)
- Activity log with filters

### Security
- JWT authentication
- API-key authentication via `X-API-Key` header
- Audit logging of auth, agent, and task actions
- Role-based access

## Authentication

Every endpoint accepts either a JWT bearer token or an API key:

```bash
# JWT (POST /auth/login to obtain)
curl http://localhost:8000/agents \
  -H "Authorization: Bearer YOUR_TOKEN"

# API key (create at Settings → Security, or POST /auth/api-keys)
curl http://localhost:8000/agents \
  -H "X-API-Key: ma_your_key_here"

# Your own activity trail
curl http://localhost:8000/audit/logs \
  -H "X-API-Key: ma_your_key_here"
```

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                  React Frontend                      │
│    Dashboard │ Agents │ Tasks │ Real-time Updates    │
└───────────────────────┬─────────────────────────────┘
                        │ REST + WebSocket
┌───────────────────────┴─────────────────────────────┐
│                  FastAPI Backend                      │
│    Auth │ Agents │ Tasks │ Orchestrator │ WebSocket  │
└───────────────────────┬─────────────────────────────┘
                        │
              ┌─────────┴─────────┐
              │      SQLite       │
              │   Persistent DB   │
              └───────────────────┘
```

## API Examples

> Backend routes have **no** `/api` prefix when talking to uvicorn directly;
> the production nginx strips it (`location /api/` proxies to the backend).

### Create an Agent
```bash
curl -X POST http://localhost:8000/agents \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "DataAnalyst", "capabilities": ["analysis", "statistics"]}'
```

### Create a Task
```bash
curl -X POST http://localhost:8000/tasks \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "Analyze sales data", "priority": "high", "required_capabilities": ["analysis"]}'
```

### Auto-Assign Task
```bash
curl -X POST http://localhost:8000/tasks/1/auto-assign \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## Configuration

Environment variables (set in `.env` or Docker):

```bash
SECRET_KEY=your-secret-key
DATABASE_URL=sqlite:///./data/multi_agent.db
CORS_ORIGINS=http://localhost:5173,http://localhost:3000
```

## Development

```bash
# Backend tests (pytest suite — runs against a temp SQLite DB)
python -m pytest backend/tests -q

# Legacy core-framework tests
python tests/test_agents.py

# Frontend typecheck + build
cd frontend
npx tsc --noEmit
npm run build

# Run examples
python examples/simple_agents.py
python examples/research_team.py
```

CI runs the pytest suite, legacy tests, and frontend typecheck/build on every
push and pull request to `main` (`.github/workflows/ci.yml`).

### Database migrations (Alembic)

Schema changes are tracked with Alembic (`alembic/` at the repo root). The
baseline revision covers the full schema; fresh dev databases are still
created automatically on startup (`create_all`), and existing `create_all`-era
databases should be stamped **once**:

```bash
make migrate           # alembic upgrade head
make revision msg="add thing"   # autogenerate from model changes
make db-stamp          # mark an existing DB as migrated (no data changes)
```

When you change models: edit the model, `make revision msg="..."`, review the
generated file in `alembic/versions/`, then `make migrate`.

## Project Structure

```
├── backend/          # FastAPI API server
├── frontend/         # React + TypeScript UI
├── src/              # Core agent framework
├── examples/         # Usage examples
├── tests/            # Unit tests
├── installer/        # Linux installer
├── docker/           # Docker configuration
└── install.sh        # Quick install script
```

## PWA & Microsoft Store

The frontend is an installable PWA (manifest + service worker). Users can also
run the packaged client from the Microsoft Store — a paid, one-time-purchase
client that talks to a backend you (or they) self-host. Full submission steps:
[MICROSOFT_STORE_GUIDE.md](./MICROSOFT_STORE_GUIDE.md).

- **Live PWA**: every push to `main` auto-deploys to GitHub Pages at
  `https://ausgreekdev-cpu.github.io/MUMAP/` (built with `BASE_PATH=/MUMAP/`);
  that URL is the PWABuilder input for Store packaging
- **First-run server setup**: the `/setup` screen validates and stores a
  server URL (`GET {url}/health`) in `localStorage` (`mumap_api_url`); the app
  then talks to `{server}/api/...` over HTTPS (visitors with no server
  configured are redirected there automatically)
- **Privacy policy**: live at `/privacy` (also required by Partner Center)
- **Store listing copy**: paste-ready fields in
  [store/STORE_LISTING.md](./store/STORE_LISTING.md)
- **CI**: every green build uploads a ready-to-host `pwa-dist` artifact
  (GitHub Actions run → Artifacts), built at root base `/` for generic hosting

## License

MIT
