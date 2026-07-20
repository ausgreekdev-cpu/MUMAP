import asyncio
import sys
import time

from .base import Tool, ToolResult


class CodeExecutorTool(Tool):
    name = "code_executor"
    description = "Execute Python code in a sandboxed subprocess with timeout. No file system or network access."
    parameters = {
        "type": "object",
        "properties": {
            "code": {
                "type": "string",
                "description": "The Python code to execute",
            },
            "language": {
                "type": "string",
                "description": "Programming language (currently only python supported)",
                "default": "python",
            },
        },
        "required": ["code"],
    }

    MAX_EXECUTION_TIME = 30
    BLOCKED_BUILTINS = [
        "open",
        "exec",
        "eval",
        "__import__",
        "compile",
        "breakpoint",
        "exit",
        "quit",
        "globals",
        "locals",
        "vars",
        "dir",
        "type",
        "super",
    ]
    BLOCKED_MODULES = [
        "os",
        "sys",
        "subprocess",
        "shutil",
        "pathlib",
        "socket",
        "http",
        "urllib",
        "requests",
        "httpx",
        "aiohttp",
        "ftplib",
        "smtplib",
        "pickle",
        "shelve",
        "dbm",
        "sqlite3",
        "importlib",
        "ctypes",
        "signal",
        "multiprocessing",
        "threading",
    ]

    async def execute(self, code: str, language: str = "python", **kwargs) -> ToolResult:
        start = time.monotonic()
        try:
            if not code.strip():
                return ToolResult(
                    success=False,
                    output=None,
                    error="Code cannot be empty",
                    duration_ms=int((time.monotonic() - start) * 1000),
                )

            if language.lower() != "python":
                return ToolResult(
                    success=False,
                    output=None,
                    error=f"Unsupported language: {language}. Only Python is supported.",
                    duration_ms=int((time.monotonic() - start) * 1000),
                )

            if len(code) > 10000:
                return ToolResult(
                    success=False,
                    output=None,
                    error="Code exceeds maximum length of 10000 characters",
                    duration_ms=int((time.monotonic() - start) * 1000),
                )

            sandboxed_code = self._create_sandboxed_code(code)

            process = await asyncio.create_subprocess_exec(
                sys.executable,
                "-c",
                sandboxed_code,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=self.MAX_EXECUTION_TIME,
                )
            except asyncio.TimeoutError:
                process.kill()
                await process.communicate()
                return ToolResult(
                    success=False,
                    output=None,
                    error=f"Code execution timed out after {self.MAX_EXECUTION_TIME}s",
                    duration_ms=int((time.monotonic() - start) * 1000),
                )

            stdout_str = stdout.decode("utf-8", errors="replace").strip()
            stderr_str = stderr.decode("utf-8", errors="replace").strip()
            return_code = process.returncode

            duration = int((time.monotonic() - start) * 1000)

            if return_code != 0:
                return ToolResult(
                    success=False,
                    output=stdout_str if stdout_str else None,
                    error=stderr_str or f"Process exited with code {return_code}",
                    duration_ms=duration,
                    metadata={"return_code": return_code},
                )

            output = stdout_str if stdout_str else "(no output)"
            return ToolResult(
                success=True,
                output=output,
                duration_ms=duration,
                metadata={"return_code": return_code},
            )
        except Exception as e:
            return ToolResult(
                success=False,
                output=None,
                error=str(e),
                duration_ms=int((time.monotonic() - start) * 1000),
            )

    def _create_sandboxed_code(self, code: str) -> str:
        blocked_list = repr(self.BLOCKED_BUILTINS)
        return (
            f"import builtins as _builtins\n"
            f"_blocked = {blocked_list}\n"
            f"_safe = {{k: v for k, v in vars(_builtins).items() if k not in _blocked}}\n"
            f"__builtins__ = _safe\n"
            f"import sys as _sys\n"
            f"for _m in ('os', 'subprocess', 'socket', 'http', 'urllib', 'requests', 'httpx', 'aiohttp', 'ftplib', 'smtplib', 'shutil', 'pathlib', 'ctypes', 'signal', 'multiprocessing', 'threading', 'importlib', 'sqlite3'):\n"
            f"    _sys.modules[_m] = None\n"
            f"{code}"
        )


code_executor_tool = CodeExecutorTool()
