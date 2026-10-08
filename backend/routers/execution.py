from __future__ import annotations

import asyncio
import logging
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends, HTTPException

from ..database import get_db
from ..models.agent import Agent, AgentStatus
from ..models.task import Task, TaskLog
from ..services.auth import get_current_user
from ..services.websocket import manager
from ..config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/execution", tags=["execution"])


class ExecuteRequest(BaseModel):
    task_id: int


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = None
    history: Optional[list[ChatMessage]] = None


def _resolve_provider(agent: Agent) -> str:
    return agent.model_provider or settings.LLM_DEFAULT_PROVIDER


def _require_llm_configured(provider: str) -> None:
    """Raise a clear 503 when the selected provider has no credentials."""
    if provider == "openai" and not settings.OPENAI_API_KEY:
        raise HTTPException(
            status_code=503,
            detail="OPENAI_API_KEY is not configured. Set it in the environment to use this agent.",
        )
    if provider == "anthropic" and not settings.ANTHROPIC_API_KEY:
        raise HTTPException(
            status_code=503,
            detail="ANTHROPIC_API_KEY is not configured. Set it in the environment to use this agent.",
        )
    if provider not in ("openai", "anthropic", "ollama"):
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported model provider: {provider}",
        )


class ExecutionResponse(BaseModel):
    status: str
    task_id: int
    answer: str
    error: Optional[str] = None
    tokens_used: int
    duration_ms: int
    iterations: int
    tool_calls_made: int


class ChatResponse(BaseModel):
    response: str
    conversation_id: str
    tokens_used: int
    duration_ms: int


class LogEntry(BaseModel):
    id: int
    event: str
    message: str
    level: str
    data: dict
    duration_ms: Optional[int] = None
    created_at: Optional[str] = None


class ExecutionLogResponse(BaseModel):
    task: dict
    logs: list[LogEntry]
    total_logs: int


@router.post("/agents/{agent_id}/execute", response_model=ExecutionResponse)
async def execute_task(
    agent_id: int,
    body: ExecuteRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    agent = db.query(Agent).filter(Agent.id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    task = db.query(Task).filter(Task.id == body.task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    if agent.status == AgentStatus.OFFLINE.value:
        raise HTTPException(status_code=400, detail="Agent is offline")

    if not agent.model_provider and not agent.system_prompt:
        raise HTTPException(
            status_code=400,
            detail="Agent has no LLM configuration (model_provider or system_prompt required)",
        )

    _require_llm_configured(_resolve_provider(agent))

    from ..services.execution.engine import AgentExecutionEngine
    engine = AgentExecutionEngine(db=db, agent=agent, task=task)

    try:
        result = await asyncio.wait_for(
            engine.run(),
            timeout=task.timeout_seconds or settings.LLM_REQUEST_TIMEOUT + 30,
        )
    except asyncio.TimeoutError:
        raise HTTPException(status_code=504, detail="Task execution timed out")

    try:
        await manager.notify_task_update({
            "id": task.id,
            "name": task.name,
            "status": "completed" if result["status"] == "completed" else "failed",
            "event": "execution_finished",
        })
    except Exception:
        logger.debug("WebSocket notification failed")

    return ExecutionResponse(
        status=result["status"],
        task_id=task.id,
        answer=result.get("answer", ""),
        error=result.get("error"),
        tokens_used=result.get("tokens_used", 0),
        duration_ms=result.get("duration_ms", 0),
        iterations=result.get("iterations", 0),
        tool_calls_made=result.get("tool_calls_made", 0),
    )


@router.post("/agents/{agent_id}/chat", response_model=ChatResponse)
async def chat_with_agent(
    agent_id: int,
    body: ChatRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    agent = db.query(Agent).filter(Agent.id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    if agent.status == AgentStatus.OFFLINE.value:
        raise HTTPException(status_code=400, detail="Agent is offline")

    if not agent.model_provider and not agent.system_prompt:
        raise HTTPException(
            status_code=400,
            detail="Agent has no LLM configuration (model_provider or system_prompt required)",
        )

    provider = _resolve_provider(agent)
    _require_llm_configured(provider)

    conversation_id = body.conversation_id or f"conv_{agent_id}_{current_user.id}"

    from ..services.llm.adapter import LLMAdapter

    llm = LLMAdapter(
        provider=provider,
        model=agent.model_name or settings.LLM_DEFAULT_MODEL,
        temperature=agent.temperature or 0.7,
        max_tokens=agent.max_tokens or 2048,
        timeout=agent.timeout_seconds or settings.LLM_REQUEST_TIMEOUT,
    )

    system_parts = []
    if agent.system_prompt:
        system_parts.append(agent.system_prompt)
    else:
        system_parts.append(
            f"You are {agent.name}, a {agent.role} agent. "
            f"Respond helpfully and accurately."
        )
    if agent.description:
        system_parts.append(f"\nAbout you: {agent.description}")

    messages = [{"role": "system", "content": "\n".join(system_parts)}]
    if body.history:
        for entry in body.history[-20:]:
            if entry.role in ("user", "assistant") and entry.content:
                messages.append({"role": entry.role, "content": entry.content})
    messages.append({"role": "user", "content": body.message})

    try:
        response = await asyncio.wait_for(
            llm.complete(messages=messages, tools=None),
            timeout=agent.timeout_seconds or settings.LLM_REQUEST_TIMEOUT,
        )
    except asyncio.TimeoutError:
        raise HTTPException(status_code=504, detail="Agent response timed out")
    except Exception as e:
        logger.exception("Chat with agent %s failed", agent_id)
        raise HTTPException(status_code=500, detail=f"Agent error: {str(e)}")

    try:
        from ..models.usage import UsageType
        from ..services.usage import UsageTracker, MODEL_PRICING

        model = agent.model_name or settings.LLM_DEFAULT_MODEL
        UsageTracker(db).record_usage(
            user_id=current_user.id,
            usage_type=UsageType.TOKEN_OUTPUT,
            quantity=float(response.tokens_used),
            unit_cost=MODEL_PRICING.get(model, {}).get("output", 0.0),
            org_id=agent.organization_id,
            resource_type="agent",
            resource_id=agent.id,
            model=model,
            metadata={"conversation_id": conversation_id},
        )
    except Exception:
        logger.debug("Failed to record chat usage for agent %s", agent_id, exc_info=True)

    return ChatResponse(
        response=response.content or "",
        conversation_id=conversation_id,
        tokens_used=response.tokens_used,
        duration_ms=int(response.latency_ms),
    )


@router.get("/tasks/{task_id}/execution-log", response_model=ExecutionLogResponse)
async def get_execution_log(
    task_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    logs = (
        db.query(TaskLog)
        .filter(TaskLog.task_id == task_id)
        .order_by(TaskLog.created_at.asc())
        .all()
    )

    task_dict = task.to_dict()
    if task.started_at:
        task_dict["started_at"] = task.started_at.isoformat()
    if task.completed_at:
        task_dict["completed_at"] = task.completed_at.isoformat()

    log_entries = []
    for log in logs:
        log_entries.append(LogEntry(
            id=log.id,
            event=log.event,
            message=log.message,
            level=log.level,
            data=log.data or {},
            duration_ms=log.duration_ms,
            created_at=log.created_at.isoformat() if log.created_at else None,
        ))

    return ExecutionLogResponse(
        task=task_dict,
        logs=log_entries,
        total_logs=len(log_entries),
    )
