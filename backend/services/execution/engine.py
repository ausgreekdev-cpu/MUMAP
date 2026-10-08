from __future__ import annotations

import json
import time
import asyncio
import logging
from datetime import datetime, timezone
from dataclasses import dataclass, field
from typing import Any, Optional

from sqlalchemy.orm import Session

from ...config import settings
from ...models.agent import Agent, AgentStatus
from ...models.task import Task, TaskStatus, TaskLog
from ...models.usage import UsageType
from ..llm.adapter import LLMAdapter, ToolCall, ToolDefinition, LLMToolResponse
from ..usage import UsageTracker, MODEL_PRICING, TASK_RUN_COST

logger = logging.getLogger(__name__)

TOOL_REGISTRY: dict[str, dict[str, Any]] = {}


def register_tool(
    name: str, description: str, parameters: dict[str, Any], handler: Any = None
):
    TOOL_REGISTRY[name] = {
        "definition": ToolDefinition(name=name, description=description, parameters=parameters),
        "handler": handler,
    }


register_tool(
    name="search_knowledge_base",
    description="Search the knowledge base for information relevant to a query.",
    parameters={
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "The search query"},
        },
        "required": ["query"],
    },
)

register_tool(
    name="calculate",
    description="Perform a mathematical calculation.",
    parameters={
        "type": "object",
        "properties": {
            "expression": {"type": "string", "description": "Math expression to evaluate"},
        },
        "required": ["expression"],
    },
)

register_tool(
    name="format_output",
    description="Format the final answer in a structured format.",
    parameters={
        "type": "object",
        "properties": {
            "format": {"type": "string", "enum": ["text", "json", "markdown"], "description": "Output format"},
            "content": {"type": "string", "description": "Content to format"},
        },
        "required": ["format", "content"],
    },
)


def _execute_tool_sync(tool_name: str, arguments: dict[str, Any]) -> str:
    if tool_name not in TOOL_REGISTRY:
        return json.dumps({"error": f"Unknown tool: {tool_name}"})

    tool = TOOL_REGISTRY[tool_name]
    handler = tool.get("handler")

    if handler is not None:
        try:
            result = handler(**arguments)
            return json.dumps({"result": result}) if not isinstance(result, str) else result
        except Exception as e:
            return json.dumps({"error": str(e)})

    if tool_name == "search_knowledge_base":
        query = arguments.get("query", "")
        return json.dumps({"results": [], "query": query, "note": "Knowledge base not connected"})

    if tool_name == "calculate":
        expr = arguments.get("expression", "")
        try:
            allowed = set("0123456789+-*/().% ")
            if not all(c in allowed for c in expr):
                return json.dumps({"error": "Invalid characters in expression"})
            result = eval(expr)
            return json.dumps({"result": result})
        except Exception as e:
            return json.dumps({"error": str(e)})

    if tool_name == "format_output":
        fmt = arguments.get("format", "text")
        content = arguments.get("content", "")
        return json.dumps({"formatted": content, "format": fmt})

    return json.dumps({"error": f"No handler for tool: {tool_name}"})


@dataclass
class ExecutionState:
    task_id: int
    agent_id: int
    messages: list[dict[str, str]] = field(default_factory=list)
    total_tokens: int = 0
    tool_calls_made: int = 0
    iterations: int = 0
    history: list[dict[str, Any]] = field(default_factory=list)
    answer: str = ""
    error: str | None = None
    start_time: float = field(default_factory=time.monotonic)


class AgentExecutionEngine:
    def __init__(self, db: Session, agent: Agent, task: Task):
        self.db = db
        self.agent = agent
        self.task = task
        self.max_iterations = settings.LLM_MAX_ITERATIONS
        self._llm: LLMAdapter | None = None

    def _get_llm(self) -> LLMAdapter:
        if self._llm is None:
            provider = self.agent.model_provider or settings.LLM_DEFAULT_PROVIDER
            model = self.agent.model_name or settings.LLM_DEFAULT_MODEL
            self._llm = LLMAdapter(
                provider=provider,
                model=model,
                temperature=self.agent.temperature or 0.7,
                max_tokens=self.agent.max_tokens or 2048,
                timeout=self.agent.timeout_seconds or settings.LLM_REQUEST_TIMEOUT,
            )
        return self._llm

    def _build_system_prompt(self) -> str:
        parts = []
        if self.agent.system_prompt:
            parts.append(self.agent.system_prompt)
        else:
            parts.append(
                f"You are {self.agent.name}, a {self.agent.role} agent. "
                f"Complete the assigned task accurately and thoroughly."
            )

        if self.agent.description:
            parts.append(f"\nDescription: {self.agent.description}")

        tool_defs = self._get_available_tools()
        if tool_defs:
            tool_descriptions = []
            for td in tool_defs:
                tool_descriptions.append(f"- {td.name}: {td.description}")
            parts.append("\nAvailable tools:")
            parts.append("\n".join(tool_descriptions))
            parts.append(
                "\nYou may use tools by returning tool_calls. "
                "After receiving tool results, continue reasoning and provide a final answer."
            )

        parts.append(
            "\nWhen you have the final answer, provide it directly as text content "
            "without using a tool call."
        )

        return "\n".join(parts)

    def _get_available_tools(self) -> list[ToolDefinition]:
        tools = []
        agent_tools = (self.agent.config or {}).get("tools", [])
        if agent_tools:
            for tool_name in agent_tools:
                if tool_name in TOOL_REGISTRY:
                    tools.append(TOOL_REGISTRY[tool_name]["definition"])
        else:
            for tool_def in TOOL_REGISTRY.values():
                tools.append(tool_def["definition"])
        return tools

    def _build_initial_messages(self) -> list[dict[str, str]]:
        system_prompt = self._build_system_prompt()
        messages = [{"role": "system", "content": system_prompt}]

        input_data = self.task.input_data or {}
        user_content = ""
        if isinstance(input_data, dict):
            if "message" in input_data:
                user_content = input_data["message"]
            elif "prompt" in input_data:
                user_content = input_data["prompt"]
            elif "query" in input_data:
                user_content = input_data["query"]
            else:
                user_content = json.dumps(input_data)
        else:
            user_content = str(input_data)

        if not user_content and self.task.description:
            user_content = self.task.description

        if not user_content:
            user_content = "Please complete this task."

        messages.append({"role": "user", "content": user_content})
        return messages

    def _log_step(self, event: str, message: str, data: dict[str, Any] | None = None):
        try:
            log = TaskLog(
                task_id=self.task.id,
                agent_id=self.agent.id,
                event=event,
                message=message,
                data=data or {},
                level="INFO",
            )
            self.db.add(log)
            self.db.flush()
        except Exception as e:
            logger.error("Failed to create task log: %s", e)

    def _record_usage(self, state: ExecutionState):
        """Meter task runs and LLM tokens. Failures here must never break execution."""
        try:
            user_id = self.task.creator_id or self.agent.owner_id
            if not user_id:
                return
            model = self.agent.model_name or settings.LLM_DEFAULT_MODEL
            org_id = self.agent.organization_id
            tracker = UsageTracker(self.db)
            tracker.record_usage(
                user_id=user_id,
                usage_type=UsageType.TASK_RUN,
                quantity=1,
                unit_cost=TASK_RUN_COST,
                org_id=org_id,
                resource_type="task",
                resource_id=self.task.id,
                metadata={"agent_id": self.agent.id, "status": self.task.status},
            )
            if state.total_tokens > 0:
                # Adapter reports combined input+output tokens; metered at output rate.
                pricing = MODEL_PRICING.get(model, {})
                tracker.record_usage(
                    user_id=user_id,
                    usage_type=UsageType.TOKEN_OUTPUT,
                    quantity=float(state.total_tokens),
                    unit_cost=pricing.get("output", 0.0),
                    org_id=org_id,
                    resource_type="task",
                    resource_id=self.task.id,
                    model=model,
                    metadata={"agent_id": self.agent.id, "combined_tokens": True},
                )
        except Exception:
            logger.exception("Failed to record usage for task %s", self.task.id)

    def _update_task(self, status: TaskStatus, output: dict | None = None, error: str | None = None):
        try:
            self.task.status = status.value
            self.task.started_at = self.task.started_at or datetime.now(timezone.utc)
            if status == TaskStatus.COMPLETED:
                self.task.completed_at = datetime.now(timezone.utc)
                self.task.output_data = output or {}
            elif status == TaskStatus.FAILED:
                self.task.completed_at = datetime.now(timezone.utc)
                self.task.error_message = error
            elif status == TaskStatus.IN_PROGRESS:
                self.task.started_at = datetime.now(timezone.utc)
            self.db.flush()
        except Exception as e:
            logger.error("Failed to update task: %s", e)

    def _update_agent(self, status: AgentStatus):
        try:
            self.agent.status = status.value
            if status == AgentStatus.IDLE:
                self.agent.current_task_id = None
                self.agent.completed_tasks_count = (self.agent.completed_tasks_count or 0) + 1
            elif status == AgentStatus.ERROR:
                self.agent.current_task_id = None
                self.agent.failed_tasks_count = (self.agent.failed_tasks_count or 0) + 1
            self.db.flush()
        except Exception as e:
            logger.error("Failed to update agent: %s", e)

    def _compute_tokens(self, state: ExecutionState) -> int:
        return state.total_tokens

    def _compute_duration_ms(self, state: ExecutionState) -> int:
        return int((time.monotonic() - state.start_time) * 1000)

    async def run(self) -> dict:
        state = ExecutionState(task_id=self.task.id, agent_id=self.agent.id)

        try:
            self._update_task(TaskStatus.IN_PROGRESS)
            self._update_agent(AgentStatus.BUSY)
            self._log_step("execution_started", "Agent execution started", {
                "agent": self.agent.name,
                "task": self.task.name,
            })
            self.db.commit()

            state.messages = self._build_initial_messages()
            tools = self._get_available_tools()
            llm = self._get_llm()

            for iteration in range(1, self.max_iterations + 1):
                state.iterations = iteration
                self._log_step("llm_call", f"LLM call iteration {iteration}/{self.max_iterations}", {
                    "iteration": iteration,
                    "message_count": len(state.messages),
                })

                try:
                    response: LLMToolResponse = await asyncio.wait_for(
                        llm.complete(messages=state.messages, tools=tools if tools else None),
                        timeout=self.agent.timeout_seconds or settings.LLM_REQUEST_TIMEOUT,
                    )
                except asyncio.TimeoutError:
                    state.error = f"LLM call timed out after {self.agent.timeout_seconds}s"
                    self._log_step("timeout", state.error, {"iteration": iteration})
                    break
                except Exception as e:
                    state.error = f"LLM call failed: {str(e)}"
                    self._log_step("llm_error", state.error, {"iteration": iteration})
                    break

                state.total_tokens += response.tokens_used

                if response.content and not response.tool_calls:
                    state.answer = response.content
                    state.history.append({
                        "iteration": iteration,
                        "reasoning": response.content,
                        "action": None,
                        "observation": None,
                    })
                    self._log_step("final_answer", "Agent produced final answer", {
                        "iteration": iteration,
                        "tokens": response.tokens_used,
                    })
                    break

                if response.tool_calls:
                    state.tool_calls_made += len(response.tool_calls)
                    assistant_content = response.content or ""

                    if assistant_content:
                        state.messages.append({"role": "assistant", "content": assistant_content})

                    for tc in response.tool_calls:
                        self._log_step(
                            "tool_call",
                            f"Calling tool: {tc.name}",
                            {"tool": tc.name, "arguments": tc.arguments, "iteration": iteration},
                        )

                        try:
                            result = await asyncio.wait_for(
                                asyncio.get_event_loop().run_in_executor(
                                    None, _execute_tool_sync, tc.name, tc.arguments
                                ),
                                timeout=30,
                            )
                        except asyncio.TimeoutError:
                            result = json.dumps({"error": "Tool execution timed out"})
                        except Exception as e:
                            result = json.dumps({"error": str(e)})

                        self._log_step(
                            "tool_result",
                            f"Tool {tc.name} returned result",
                            {"tool": tc.name, "result_length": len(result), "iteration": iteration},
                        )

                        state.messages.append({
                            "role": "assistant",
                            "content": None,
                            "tool_calls": [
                                {
                                    "id": tc.id,
                                    "type": "function",
                                    "function": {"name": tc.name, "arguments": json.dumps(tc.arguments)},
                                }
                            ],
                        })
                        state.messages.append({
                            "role": "tool",
                            "tool_call_id": tc.id,
                            "content": result,
                        })

                    state.history.append({
                        "iteration": iteration,
                        "reasoning": assistant_content,
                        "action": [
                            {"tool": tc.name, "arguments": tc.arguments}
                            for tc in response.tool_calls
                        ],
                        "observation": None,
                    })
                else:
                    if response.content:
                        state.answer = response.content
                    break

            if not state.answer and not state.error:
                state.error = "Max iterations reached without final answer"
                self._log_step("max_iterations", state.error, {"max": self.max_iterations})

            if state.error:
                self._update_task(TaskStatus.FAILED, error=state.error)
                self._update_agent(AgentStatus.ERROR)
                self._log_step("execution_failed", state.error, {
                    "duration_ms": self._compute_duration_ms(state),
                    "tokens": state.total_tokens,
                })
            else:
                output_data = {"answer": state.answer}
                if self.task.output_data and isinstance(self.task.output_data, dict):
                    output_data.update(self.task.output_data)
                self._update_task(TaskStatus.COMPLETED, output=output_data)
                self._update_agent(AgentStatus.IDLE)
                self._log_step("execution_completed", "Task completed successfully", {
                    "duration_ms": self._compute_duration_ms(state),
                    "tokens": state.total_tokens,
                    "tool_calls": state.tool_calls_made,
                    "iterations": state.iterations,
                })

            self.task.tokens_used = state.total_tokens
            self._record_usage(state)
            self.db.commit()

            return {
                "status": "completed" if not state.error else "failed",
                "answer": state.answer,
                "error": state.error,
                "tokens_used": state.total_tokens,
                "tool_calls_made": state.tool_calls_made,
                "iterations": state.iterations,
                "duration_ms": self._compute_duration_ms(state),
                "history": state.history,
            }

        except Exception as e:
            logger.exception("Execution engine error")
            try:
                self._update_task(TaskStatus.FAILED, error=str(e))
                self._update_agent(AgentStatus.ERROR)
                self._log_step("execution_error", f"Unexpected error: {str(e)}", {})
                self.db.commit()
            except Exception:
                logger.exception("Failed to record execution error")

            return {
                "status": "failed",
                "answer": "",
                "error": str(e),
                "tokens_used": state.total_tokens,
                "tool_calls_made": state.tool_calls_made,
                "iterations": state.iterations,
                "duration_ms": self._compute_duration_ms(state),
                "history": state.history,
            }
