# Multi-Agent Orchestration Platform

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
- Agent availability
- Task queue overview
- Activity monitoring

### Security
- JWT authentication
- Role-based access
- Secure API endpoints

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

### Create an Agent
```bash
curl -X POST http://localhost:8000/api/agents \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "DataAnalyst", "capabilities": ["analysis", "statistics"]}'
```

### Create a Task
```bash
curl -X POST http://localhost:8000/api/tasks \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "Analyze sales data", "priority": "high", "required_capabilities": ["analysis"]}'
```

### Auto-Assign Task
```bash
curl -X POST http://localhost:8000/api/tasks/1/auto-assign \
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
# Run tests
python tests/test_agents.py

# Run examples
python examples/simple_agents.py
python examples/research_team.py
```

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

## License

MIT
