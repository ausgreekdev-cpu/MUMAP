from __future__ import annotations

import json
import time
import asyncio
import logging
from dataclasses import dataclass, field
from typing import Any, Optional

from ..llm.adapter import LLMAdapter, ToolCall, ToolDefinition, LLMToolResponse

logger = logging.getLogger(__name__)


@dataclass
class HistoryEntry:
    iteration: int
    reasoning: str
    action: Any | None
    observation: str | None


@dataclass
class ExecutionResult:
    answer: str
    tool_calls_made: int
    total_tokens: int
    iterations: int
    history: list[HistoryEntry]
    error: str | None = None
    duration_ms: int = 0


class ReActLoop:
    REACT_SYSTEM_SUFFIX = (
        "\n\nYou must follow the ReAct pattern:\n"
        "1. Reason: Analyze the current state and decide what to do next.\n"
        "2. Act: Use a tool to take action, or provide the final answer.\n"
        "3. Observe: Review the tool result and continue reasoning.\n"
        "When you have the final answer, respond with it directly without tool calls."
    )

    def __init__(self, llm: LLMAdapter, tools: list[ToolDefinition] | None = None):
        self.llm = llm
        self.tools = tools or []

    async def run(
        self,
        system_prompt: str,
        initial_message: str,
        max_iterations: int = 10,
        timeout: int = 120,
    ) -> ExecutionResult:
        start = time.monotonic()
        total_tokens = 0
        tool_calls_made = 0
        history: list[HistoryEntry] = []

        messages: list[dict[str, str]] = [
            {"role": "system", "content": system_prompt + self.REACT_SYSTEM_SUFFIX},
            {"role": "user", "content": initial_message},
        ]

        answer = ""
        error = None

        for iteration in range(1, max_iterations + 1):
            try:
                response: LLMToolResponse = await asyncio.wait_for(
                    self.llm.complete(messages=messages, tools=self.tools if self.tools else None),
                    timeout=timeout,
                )
            except asyncio.TimeoutError:
                error = f"LLM call timed out after {timeout}s on iteration {iteration}"
                logger.warning("react_timeout", extra={"iteration": iteration})
                break
            except Exception as e:
                error = f"LLM call failed on iteration {iteration}: {str(e)}"
                logger.error("react_llm_error", extra={"iteration": iteration, "error": str(e)})
                break

            total_tokens += response.tokens_used

            if response.content and not response.tool_calls:
                answer = response.content
                history.append(HistoryEntry(
                    iteration=iteration,
                    reasoning=response.content,
                    action=None,
                    observation=None,
                ))
                break

            if response.tool_calls:
                assistant_content = response.content or ""
                if assistant_content:
                    messages.append({"role": "assistant", "content": assistant_content})

                observations = []
                for tc in response.tool_calls:
                    tool_calls_made += 1
                    try:
                        result = await asyncio.wait_for(
                            asyncio.get_event_loop().run_in_executor(
                                None, self._execute_tool, tc
                            ),
                            timeout=30,
                        )
                    except asyncio.TimeoutError:
                        result = json.dumps({"error": f"Tool {tc.name} timed out"})
                    except Exception as e:
                        result = json.dumps({"error": str(e)})

                    observations.append({"tool": tc.name, "result": result})

                    messages.append({
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
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tc.id,
                        "content": result,
                    })

                history.append(HistoryEntry(
                    iteration=iteration,
                    reasoning=assistant_content,
                    action=[{"tool": tc.name, "arguments": tc.arguments} for tc in response.tool_calls],
                    observation=observations,
                ))
            else:
                if response.content:
                    answer = response.content
                break

        if not answer and not error:
            error = f"Max iterations ({max_iterations}) reached without final answer"

        duration_ms = int((time.monotonic() - start) * 1000)

        return ExecutionResult(
            answer=answer,
            tool_calls_made=tool_calls_made,
            total_tokens=total_tokens,
            iterations=len(history),
            history=history,
            error=error,
            duration_ms=duration_ms,
        )

    def _execute_tool(self, tool_call: ToolCall) -> str:
        from ..execution.engine import _execute_tool_sync, TOOL_REGISTRY

        if tool_call.name not in TOOL_REGISTRY:
            return json.dumps({"error": f"Unknown tool: {tool_call.name}"})

        return _execute_tool_sync(tool_call.name, tool_call.arguments)
