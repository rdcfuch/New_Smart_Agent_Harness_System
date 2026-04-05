import os
import subprocess
import re
from pathlib import Path
from typing import Optional


WORKDIR = Path("/Users/jackyfox/New_Smart_Agent_Harness_System/backend")


def safe_path(p: str) -> Path:
    """Resolve path and ensure it's within WORKDIR."""
    path = (WORKDIR / p).resolve()
    if not str(path).startswith(str(WORKDIR)):
        raise ValueError(f"Path escapes workspace: {p}")
    return path


class ToolResult:
    def __init__(self, success: bool, output: str = "", error: str = ""):
        self.success = success
        self.output = output
        self.error = error

    def to_dict(self):
        return {
            "success": self.success,
            "output": self.output,
            "error": self.error,
        }


class ToolRegistry:
    """Registry of tools that agents can use."""

    def __init__(self):
        self.tools = {
            "bash": self.run_bash,
            "read_file": self.read_file,
            "write_file": self.write_file,
            "edit_file": self.edit_file,
        }
        self.dangerous_patterns = ["rm -rf /", "sudo", "shutdown", "reboot", "> /dev/"]

    def execute(self, tool_name: str, **kwargs) -> ToolResult:
        """Execute a tool by name with given arguments."""
        if tool_name not in self.tools:
            return ToolResult(False, error=f"Unknown tool: {tool_name}")

        try:
            result = self.tools[tool_name](**kwargs)
            return result
        except Exception as e:
            return ToolResult(False, error=str(e))

    def run_bash(self, command: str, cwd: str = None, timeout: int = 120) -> ToolResult:
        """Execute a bash command."""
        if any(d in command for d in self.dangerous_patterns):
            return ToolResult(False, error="Dangerous command blocked")

        try:
            result = subprocess.run(
                command,
                shell=True,
                cwd=cwd or str(WORKDIR),
                capture_output=True,
                text=True,
                timeout=timeout,
            )
            output = (result.stdout + result.stderr).strip()[:50000] or "(no output)"
            return ToolResult(True, output=output)
        except subprocess.TimeoutExpired:
            return ToolResult(False, error=f"Timeout ({timeout}s)")
        except Exception as e:
            return ToolResult(False, error=str(e))

    def read_file(self, path: str, limit: int = None) -> ToolResult:
        """Read file contents."""
        try:
            fp = safe_path(path)
            lines = fp.read_text().splitlines()
            if limit and limit < len(lines):
                lines = lines[:limit] + [f"... ({len(lines) - limit} more)"]
            return ToolResult(True, output="\n".join(lines))
        except Exception as e:
            return ToolResult(False, error=str(e))

    def write_file(self, path: str, content: str) -> ToolResult:
        """Write content to file."""
        try:
            fp = safe_path(path)
            fp.parent.mkdir(parents=True, exist_ok=True)
            fp.write_text(content)
            return ToolResult(True, output=f"Wrote {len(content)} bytes to {path}")
        except Exception as e:
            return ToolResult(False, error=str(e))

    def edit_file(self, path: str, old_text: str, new_text: str) -> ToolResult:
        """Replace text in a file."""
        try:
            fp = safe_path(path)
            content = fp.read_text()
            if old_text not in content:
                return ToolResult(False, error=f"Text not found in {path}")
            fp.write_text(content.replace(old_text, new_text, 1))
            return ToolResult(True, output=f"Edited {path}")
        except Exception as e:
            return ToolResult(False, error=str(e))

    def list_tools(self) -> list:
        """List all available tools."""
        return [
            {
                "name": "bash",
                "description": "Execute a bash command in the workspace",
                "params": {
                    "command": {"type": "string", "required": True},
                    "cwd": {"type": "string", "required": False},
                    "timeout": {"type": "integer", "required": False},
                },
            },
            {
                "name": "read_file",
                "description": "Read file contents",
                "params": {
                    "path": {"type": "string", "required": True},
                    "limit": {"type": "integer", "required": False},
                },
            },
            {
                "name": "write_file",
                "description": "Write content to file",
                "params": {
                    "path": {"type": "string", "required": True},
                    "content": {"type": "string", "required": True},
                },
            },
            {
                "name": "edit_file",
                "description": "Replace text in a file",
                "params": {
                    "path": {"type": "string", "required": True},
                    "old_text": {"type": "string", "required": True},
                    "new_text": {"type": "string", "required": True},
                },
            },
        ]


def get_tool_registry() -> ToolRegistry:
    return ToolRegistry()