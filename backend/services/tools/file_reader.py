import os
import time
from pathlib import Path

from .base import Tool, ToolResult


class FileReaderTool(Tool):
    name = "file_reader"
    description = "Read files from a designated workspace directory with path traversal protection."
    parameters = {
        "type": "object",
        "properties": {
            "path": {
                "type": "string",
                "description": "Relative path to the file within the workspace",
            },
            "encoding": {
                "type": "string",
                "description": "File encoding (default: utf-8)",
                "default": "utf-8",
            },
        },
        "required": ["path"],
    }

    WORKSPACE_DIR = os.environ.get("TOOL_WORKSPACE_DIR", "/tmp/tool_workspace")
    MAX_FILE_SIZE = 1 * 1024 * 1024
    BLOCKED_EXTENSIONS = [
        ".pyc",
        ".pyo",
        ".so",
        ".dll",
        ".exe",
        ".bin",
        ".sh",
        ".bash",
        ".key",
        ".pem",
        ".env",
    ]

    async def execute(self, path: str, encoding: str = "utf-8", **kwargs) -> ToolResult:
        start = time.monotonic()
        try:
            if not path.strip():
                return ToolResult(
                    success=False,
                    output=None,
                    error="Path cannot be empty",
                    duration_ms=int((time.monotonic() - start) * 1000),
                )

            workspace = Path(self.WORKSPACE_DIR).resolve()
            target = (workspace / path).resolve()

            if not str(target).startswith(str(workspace)):
                return ToolResult(
                    success=False,
                    output=None,
                    error="Path traversal detected: access denied",
                    duration_ms=int((time.monotonic() - start) * 1000),
                )

            if not target.exists():
                return ToolResult(
                    success=False,
                    output=None,
                    error=f"File not found: {path}",
                    duration_ms=int((time.monotonic() - start) * 1000),
                )

            if not target.is_file():
                return ToolResult(
                    success=False,
                    output=None,
                    error=f"Path is not a file: {path}",
                    duration_ms=int((time.monotonic() - start) * 1000),
                )

            if target.suffix.lower() in self.BLOCKED_EXTENSIONS:
                return ToolResult(
                    success=False,
                    output=None,
                    error=f"File type not allowed: {target.suffix}",
                    duration_ms=int((time.monotonic() - start) * 1000),
                )

            file_size = target.stat().st_size
            if file_size > self.MAX_FILE_SIZE:
                return ToolResult(
                    success=False,
                    output=None,
                    error=f"File too large: {file_size} bytes (max: {self.MAX_FILE_SIZE})",
                    duration_ms=int((time.monotonic() - start) * 1000),
                )

            try:
                content = target.read_text(encoding=encoding)
            except UnicodeDecodeError:
                return ToolResult(
                    success=False,
                    output=None,
                    error=f"Cannot decode file with encoding: {encoding}",
                    duration_ms=int((time.monotonic() - start) * 1000),
                )

            duration = int((time.monotonic() - start) * 1000)
            return ToolResult(
                success=True,
                output=content,
                duration_ms=duration,
                metadata={
                    "path": str(target.relative_to(workspace)),
                    "size_bytes": file_size,
                    "encoding": encoding,
                },
            )
        except PermissionError:
            return ToolResult(
                success=False,
                output=None,
                error="Permission denied",
                duration_ms=int((time.monotonic() - start) * 1000),
            )
        except Exception as e:
            return ToolResult(
                success=False,
                output=None,
                error=str(e),
                duration_ms=int((time.monotonic() - start) * 1000),
            )


file_reader_tool = FileReaderTool()
