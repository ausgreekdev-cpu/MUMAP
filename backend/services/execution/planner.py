from __future__ import annotations

import json
import logging
from typing import Any, Optional

from sqlalchemy.orm import Session

from ...config import settings
from ...models.task import Task, TaskStatus, TaskLog
from ..llm.adapter import LLMAdapter

logger = logging.getLogger(__name__)


class TaskPlanner:
    def __init__(self, db: Session):
        self.db = db

    def _log_step(self, task_id: int, event: str, message: str, data: dict | None = None):
        try:
            log = TaskLog(
                task_id=task_id,
                event=event,
                message=message,
                data=data or {},
                level="INFO",
            )
            self.db.add(log)
            self.db.flush()
        except Exception as e:
            logger.error("Failed to create planner log: %s", e)

    async def decompose(
        self, task: Task, llm_provider: str | None = None, llm_model: str | None = None
    ) -> list[dict[str, Any]]:
        llm = LLMAdapter(
            provider=llm_provider,
            model=llm_model,
            temperature=0.3,
            max_tokens=2048,
        )

        input_summary = json.dumps(task.input_data or {}, indent=2)[:2000]
        capabilities = ", ".join(task.required_capabilities or [])

        system_prompt = (
            "You are a task decomposition planner. Break down complex tasks into "
            "smaller, independent subtasks that can be executed sequentially or in parallel.\n\n"
            "Return a JSON array of subtasks. Each subtask must be an object with:\n"
            "- name: string (short descriptive name)\n"
            "- description: string (detailed description)\n"
            "- required_capabilities: array of strings\n"
            "- input_data: object with input for this subtask\n"
            "- dependencies: array of subtask names this depends on (empty if none)\n\n"
            "Return ONLY the JSON array, no other text."
        )

        user_prompt = (
            f"Task: {task.name}\n"
            f"Description: {task.description}\n"
            f"Required capabilities: {capabilities}\n"
            f"Input data:\n{input_summary}\n\n"
            "Decompose this into subtasks:"
        )

        self._log_step(task.id, "decomposition_started", "Starting task decomposition", {
            "task_name": task.name,
        })

        try:
            response = await llm.complete(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                tools=None,
            )
        except Exception as e:
            self._log_step(task.id, "decomposition_failed", f"LLM call failed: {e}")
            return self._fallback_decompose(task)

        try:
            text = response.content.strip()
            if text.startswith("```"):
                text = text.split("\n", 1)[1] if "\n" in text else text[3:]
                if text.endswith("```"):
                    text = text[:-3]
                text = text.strip()

            subtasks = json.loads(text)

            if not isinstance(subtasks, list):
                raise ValueError("Expected a JSON array")

            validated = []
            for st in subtasks:
                validated.append({
                    "name": st.get("name", f"subtask_{len(validated)+1}"),
                    "description": st.get("description", ""),
                    "required_capabilities": st.get("required_capabilities", []),
                    "input_data": st.get("input_data", {}),
                    "dependencies": st.get("dependencies", []),
                })

            self._log_step(task.id, "decomposition_completed", f"Decomposed into {len(validated)} subtasks", {
                "subtask_count": len(validated),
                "subtask_names": [s["name"] for s in validated],
            })

            return validated

        except (json.JSONDecodeError, ValueError) as e:
            self._log_step(task.id, "decomposition_parse_error", f"Failed to parse LLM output: {e}", {
                "raw_output": response.content[:500],
            })
            return self._fallback_decompose(task)

    def _fallback_decompose(self, task: Task) -> list[dict[str, Any]]:
        return [
            {
                "name": task.name,
                "description": task.description,
                "required_capabilities": task.required_capabilities or [],
                "input_data": task.input_data or {},
                "dependencies": [],
            }
        ]

    async def estimate_difficulty(
        self, task: Task, llm_provider: str | None = None, llm_model: str | None = None
    ) -> str:
        llm = LLMAdapter(
            provider=llm_provider,
            model=llm_model,
            temperature=0.1,
            max_tokens=100,
        )

        input_summary = json.dumps(task.input_data or {}, indent=2)[:1000]
        capabilities = ", ".join(task.required_capabilities or [])

        system_prompt = (
            "You are a task difficulty estimator. Analyze the given task and return "
            "exactly one word: 'easy', 'medium', or 'hard'.\n\n"
            "Considerations:\n"
            "- easy: single-step, well-defined, no special tools needed\n"
            "- medium: multi-step, requires some reasoning or tool use\n"
            "- hard: complex reasoning, multiple tools, extensive analysis\n\n"
            "Return ONLY the difficulty word, nothing else."
        )

        user_prompt = (
            f"Task: {task.name}\n"
            f"Description: {task.description}\n"
            f"Required capabilities: {capabilities}\n"
            f"Input data preview: {input_summary}\n\n"
            "Difficulty:"
        )

        try:
            response = await llm.complete(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                tools=None,
            )

            difficulty = response.content.strip().lower().strip('"').strip("'")
            if difficulty in ("easy", "medium", "hard"):
                self._log_step(task.id, "difficulty_estimated", f"Difficulty: {difficulty}", {
                    "difficulty": difficulty,
                })
                return difficulty

            return "medium"

        except Exception as e:
            self._log_step(task.id, "difficulty_estimation_failed", f"LLM call failed: {e}")
            return "medium"
