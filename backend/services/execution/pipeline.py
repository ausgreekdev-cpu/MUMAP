from __future__ import annotations

import json
import time
import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional

from sqlalchemy.orm import Session

from ...config import settings
from ...models.task import Task, TaskStatus, TaskLog
from ...models.agent import Agent

logger = logging.getLogger(__name__)


@dataclass
class StageResult:
    task_id: int
    agent_id: int | None
    input_data: dict
    output_data: dict
    duration_ms: int
    success: bool
    error: str | None = None

    def to_dict(self) -> dict:
        return {
            "task_id": self.task_id,
            "agent_id": self.agent_id,
            "input_data": self.input_data,
            "output_data": self.output_data,
            "duration_ms": self.duration_ms,
            "success": self.success,
            "error": self.error,
        }


@dataclass
class PipelineResult:
    stages: list[StageResult]
    total_time_ms: int
    total_tokens: int
    success: bool

    def to_dict(self) -> dict:
        return {
            "stages": [s.to_dict() for s in self.stages],
            "total_time_ms": self.total_time_ms,
            "total_tokens": self.total_tokens,
            "success": self.success,
        }


class PipelineExecutor:
    def __init__(self, db: Session):
        self.db = db

    def _log_step(self, task_id: int, agent_id: int | None, event: str, message: str, data: dict | None = None):
        try:
            log = TaskLog(
                task_id=task_id,
                agent_id=agent_id,
                event=event,
                message=message,
                data=data or {},
                level="INFO",
            )
            self.db.add(log)
            self.db.flush()
        except Exception as e:
            logger.error("Failed to create pipeline log: %s", e)

    async def execute_pipeline(self, tasks: list[Task], db: Session | None = None) -> PipelineResult:
        db = db or self.db
        pipeline_start = time.monotonic()
        stages: list[StageResult] = []
        total_tokens = 0
        accumulated_output: dict[str, Any] = {}

        for idx, task in enumerate(tasks):
            stage_start = time.monotonic()
            agent = None
            if task.assigned_to:
                agent = db.query(Agent).filter(Agent.id == task.assigned_to).first()

            stage_input = dict(task.input_data or {})
            if accumulated_output:
                stage_input["pipeline_context"] = accumulated_output

            self._log_step(
                task.id,
                task.assigned_to,
                "pipeline_stage_start",
                f"Pipeline stage {idx + 1}/{len(tasks)} starting",
                {"stage": idx + 1, "task_name": task.name},
            )

            try:
                task.status = TaskStatus.IN_PROGRESS.value
                task.started_at = datetime.now(timezone.utc)
                db.flush()

                if agent:
                    from .engine import AgentExecutionEngine
                    engine = AgentExecutionEngine(db=db, agent=agent, task=task)
                    result = await engine.run()
                    total_tokens += result.get("tokens_used", 0)

                    stage_result = StageResult(
                        task_id=task.id,
                        agent_id=agent.id,
                        input_data=stage_input,
                        output_data=result.get("answer", ""),
                        duration_ms=result.get("duration_ms", 0),
                        success=result.get("status") == "completed",
                        error=result.get("error"),
                    )

                    if result.get("status") == "completed":
                        accumulated_output = result.get("output_data", {"answer": result.get("answer", "")})
                    else:
                        accumulated_output = {"error": result.get("error", "Stage failed")}
                else:
                    task.status = TaskStatus.FAILED.value
                    task.error_message = "No agent assigned"
                    task.completed_at = datetime.now(timezone.utc)
                    db.flush()

                    stage_result = StageResult(
                        task_id=task.id,
                        agent_id=None,
                        input_data=stage_input,
                        output_data={},
                        duration_ms=int((time.monotonic() - stage_start) * 1000),
                        success=False,
                        error="No agent assigned",
                    )

            except Exception as e:
                logger.exception("Pipeline stage %d failed", idx + 1)
                duration_ms = int((time.monotonic() - stage_start) * 1000)

                task.status = TaskStatus.FAILED.value
                task.error_message = str(e)
                task.completed_at = datetime.now(timezone.utc)
                db.flush()

                stage_result = StageResult(
                    task_id=task.id,
                    agent_id=task.assigned_to,
                    input_data=stage_input,
                    output_data={},
                    duration_ms=duration_ms,
                    success=False,
                    error=str(e),
                )

                accumulated_output = {"error": str(e)}

            stages.append(stage_result)

            self._log_step(
                task.id,
                task.assigned_to,
                "pipeline_stage_complete" if stage_result.success else "pipeline_stage_failed",
                f"Pipeline stage {idx + 1} {'completed' if stage_result.success else 'failed'}",
                {
                    "stage": idx + 1,
                    "duration_ms": stage_result.duration_ms,
                    "success": stage_result.success,
                },
            )

            if not stage_result.success:
                for remaining_task in tasks[idx + 1 :]:
                    remaining_task.status = TaskStatus.CANCELLED.value
                    remaining_task.error_message = f"Pipeline cancelled: stage {idx + 1} failed"
                    db.flush()
                break

        total_time_ms = int((time.monotonic() - pipeline_start) * 1000)
        all_success = all(s.success for s in stages)

        return PipelineResult(
            stages=stages,
            total_time_ms=total_time_ms,
            total_tokens=total_tokens,
            success=all_success,
        )

    async def execute_sequential(
        self, tasks: list[Task], concurrency_limit: int | None = None
    ) -> list[dict]:
        limit = concurrency_limit or settings.EXECUTION_MAX_CONCURRENT
        semaphore = asyncio.Semaphore(limit)
        results = []

        async def _run_with_semaphore(task: Task) -> dict:
            async with semaphore:
                agent = None
                if task.assigned_to:
                    agent = self.db.query(Agent).filter(Agent.id == task.assigned_to).first()
                if not agent:
                    return {"task_id": task.id, "success": False, "error": "No agent assigned"}

                from .engine import AgentExecutionEngine
                engine = AgentExecutionEngine(db=self.db, agent=agent, task=task)
                return await engine.run()

        gathered = await asyncio.gather(
            *[_run_with_semaphore(t) for t in tasks],
            return_exceptions=True,
        )

        for idx, result in enumerate(gathered):
            if isinstance(result, Exception):
                results.append({"task_id": tasks[idx].id, "success": False, "error": str(result)})
            else:
                results.append(result)

        return results
