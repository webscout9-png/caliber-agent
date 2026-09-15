from __future__ import annotations

import os
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional

from rich.console import Console

console = Console()

# Working directory for tools (project root)
_cwd = Path.cwd()

def set_cwd(path: Path) -> None:
    global _cwd
    _cwd = path.resolve()

def get_cwd() -> Path:
    return _cwd

def tool_list_dir(path: str = ".") -> str:
    """List files and directories."""
    target = (_cwd / path).resolve()
    if not str(target).startswith(str(_cwd)):
        return "Error: path outside project"
    if not target.exists():
        return f"Error: {path} does not exist"
    if not target.is_dir():
        return f"Error: {path} is not a directory"
    entries = []
    for p in sorted(target.iterdir()):
        kind = "dir" if p.is_dir() else "file"
        entries.append(f"{kind:4} {p.name}")
    return "\n".join(entries) if entries else "(empty)"

def tool_read_file(path: str, max_lines: int = 400) -> str:
    """Read a file (truncated for safety)."""
    target = (_cwd / path).resolve()
    if not str(target).startswith(str(_cwd)):
        return "Error: path outside project"
    if not target.exists():
        return f"Error: {path} does not exist"
    if not target.is_file():
        return f"Error: {path} is not a file"
    try:
        text = target.read_text(encoding="utf-8", errors="replace")
        lines = text.splitlines()
        if len(lines) > max_lines:
            return "\n".join(lines[:max_lines]) + f"\n\n... truncated ({len(lines)} total lines)"
        return text
    except Exception as e:
        return f"Error reading file: {e}"

def tool_write_file(path: str, content: str) -> str:
    """Write / create a file."""
    target = (_cwd / path).resolve()
    if not str(target).startswith(str(_cwd)):
        return "Error: path outside project"
    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        return f"Wrote {len(content)} chars to {path}"
    except Exception as e:
        return f"Error writing file: {e}"

def tool_grep(pattern: str, path: str = ".", max_matches: int = 40) -> str:
    """Simple recursive grep."""
    target = (_cwd / path).resolve()
    if not str(target).startswith(str(_cwd)):
        return "Error: path outside project"
    matches: List[str] = []
    try:
        for root, dirs, files in os.walk(target):
            # skip common noise
            dirs[:] = [d for d in dirs if d not in {".git", "node_modules", "__pycache__", ".venv", "venv", "dist", "build"}]
            for fname in files:
                fp = Path(root) / fname
                try:
                    text = fp.read_text(encoding="utf-8", errors="ignore")
                    for i, line in enumerate(text.splitlines(), 1):
                        if pattern.lower() in line.lower():
                            rel = fp.relative_to(_cwd)
                            matches.append(f"{rel}:{i}: {line.strip()[:200]}")
                            if len(matches) >= max_matches:
                                return "\n".join(matches) + "\n... (truncated)"
                except Exception:
                    continue
        return "\n".join(matches) if matches else "No matches"
    except Exception as e:
        return f"Error: {e}"

def tool_bash(command: str, timeout: int = 60, allow: bool = False) -> str:
    """Run a shell command. Requires allow=True in build mode or user confirmation."""
    if not allow:
        return "Error: bash not allowed in current mode (use Build mode or confirm)"
    try:
        result = subprocess.run(
            command,
            shell=True,
            cwd=str(_cwd),
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        out = (result.stdout or "") + (result.stderr or "")
        if len(out) > 8000:
            out = out[:8000] + "\n... (truncated)"
        return f"exit={result.returncode}\n{out}" if out else f"exit={result.returncode}"
    except subprocess.TimeoutExpired:
        return "Error: command timed out"
    except Exception as e:
        return f"Error: {e}"

TOOL_SPECS = [
    {
        "type": "function",
        "function": {
            "name": "list_dir",
            "description": "List files and directories in a path relative to project root",
            "parameters": {
                "type": "object",
                "properties": {"path": {"type": "string", "description": "Relative path (default .)"}},
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Read the contents of a file",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string"},
                    "max_lines": {"type": "integer", "description": "Max lines to return"},
                },
                "required": ["path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "write_file",
            "description": "Create or overwrite a file with the given content",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string"},
                    "content": {"type": "string"},
                },
                "required": ["path", "content"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "grep",
            "description": "Search for a pattern across project files",
            "parameters": {
                "type": "object",
                "properties": {
                    "pattern": {"type": "string"},
                    "path": {"type": "string", "description": "Subdirectory to search"},
                },
                "required": ["pattern"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "bash",
            "description": "Run a shell command in the project directory",
            "parameters": {
                "type": "object",
                "properties": {"command": {"type": "string"}},
                "required": ["command"],
            },
        },
    },
]

def execute_tool(name: str, args: Dict[str, Any], allow_bash: bool = False) -> str:
    if name == "list_dir":
        return tool_list_dir(args.get("path", "."))
    if name == "read_file":
        return tool_read_file(args.get("path", ""), args.get("max_lines", 400))
    if name == "write_file":
        return tool_write_file(args.get("path", ""), args.get("content", ""))
    if name == "grep":
        return tool_grep(args.get("pattern", ""), args.get("path", "."))
    if name == "bash":
        return tool_bash(args.get("command", ""), allow=allow_bash)
    return f"Unknown tool: {name}"
