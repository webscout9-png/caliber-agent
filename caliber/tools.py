from __future__ import annotations

import os
import re
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional

import httpx
from rich.console import Console

console = Console()

_cwd = Path.cwd()

def set_cwd(path: Path) -> None:
    global _cwd
    _cwd = path.resolve()

def get_cwd() -> Path:
    return _cwd

def _safe(path: str) -> Path:
    target = (_cwd / path).resolve()
    if not str(target).startswith(str(_cwd)):
        raise PermissionError("path outside project")
    return target

def tool_list_dir(path: str = ".") -> str:
    try:
        target = _safe(path)
    except PermissionError as e:
        return f"Error: {e}"
    if not target.exists():
        return f"Error: {path} does not exist"
    if not target.is_dir():
        return f"Error: {path} is not a directory"
    entries = []
    for p in sorted(target.iterdir()):
        kind = "dir " if p.is_dir() else "file"
        entries.append(f"{kind}  {p.name}")
    return "\n".join(entries) if entries else "(empty)"

def tool_glob(pattern: str, path: str = ".") -> str:
    """Find files by glob pattern."""
    try:
        root = _safe(path)
    except PermissionError as e:
        return f"Error: {e}"
    matches = sorted(root.glob(pattern))
    # also recursive if ** not present
    if "**" not in pattern:
        matches = sorted(set(matches) | set(root.rglob(pattern)))
    rels = []
    for m in matches[:80]:
        try:
            rels.append(str(m.relative_to(_cwd)))
        except Exception:
            rels.append(str(m))
    if not rels:
        return "No matches"
    out = "\n".join(rels)
    if len(matches) > 80:
        out += f"\n... ({len(matches)} total)"
    return out

def tool_read_file(path: str, offset: int = 1, limit: int = 200) -> str:
    try:
        target = _safe(path)
    except PermissionError as e:
        return f"Error: {e}"
    if not target.exists():
        return f"Error: {path} does not exist"
    if not target.is_file():
        return f"Error: {path} is not a file"
    try:
        lines = target.read_text(encoding="utf-8", errors="replace").splitlines()
        start = max(0, offset - 1)
        end = start + limit
        chunk = lines[start:end]
        numbered = [f"{i+start+1}: {line}" for i, line in enumerate(chunk)]
        header = f"# {path} lines {start+1}-{min(end, len(lines))} of {len(lines)}\n"
        return header + "\n".join(numbered)
    except Exception as e:
        return f"Error reading file: {e}"

def tool_write_file(path: str, content: str) -> str:
    try:
        target = _safe(path)
    except PermissionError as e:
        return f"Error: {e}"
    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        return f"Wrote {len(content)} chars → {path}"
    except Exception as e:
        return f"Error writing file: {e}"

def tool_edit(path: str, old_string: str, new_string: str) -> str:
    """Precise search-replace edit (OpenCode-style)."""
    try:
        target = _safe(path)
    except PermissionError as e:
        return f"Error: {e}"
    if not target.exists():
        return f"Error: {path} does not exist"
    try:
        text = target.read_text(encoding="utf-8")
        if old_string not in text:
            return "Error: old_string not found in file"
        count = text.count(old_string)
        if count > 1:
            return f"Error: old_string found {count} times — make it unique"
        new_text = text.replace(old_string, new_string, 1)
        target.write_text(new_text, encoding="utf-8")
        return f"Edited {path} (1 occurrence)"
    except Exception as e:
        return f"Error editing: {e}"

def tool_grep(pattern: str, path: str = ".", max_matches: int = 40) -> str:
    try:
        target = _safe(path)
    except PermissionError as e:
        return f"Error: {e}"
    matches: List[str] = []
    skip = {".git", "node_modules", "__pycache__", ".venv", "venv", "dist", "build", ".next"}
    try:
        for root, dirs, files in os.walk(target):
            dirs[:] = [d for d in dirs if d not in skip]
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

def tool_bash(command: str, timeout: int = 90, allow: bool = False) -> str:
    if not allow:
        return "Error: bash denied in current mode (switch to /build or approve)"
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
        if len(out) > 10000:
            out = out[:10000] + "\n... (truncated)"
        return f"exit={result.returncode}\n{out}" if out.strip() else f"exit={result.returncode}"
    except subprocess.TimeoutExpired:
        return "Error: command timed out"
    except Exception as e:
        return f"Error: {e}"

def tool_webfetch(url: str) -> str:
    """Fetch a URL as text (for docs / research)."""
    try:
        with httpx.Client(timeout=20.0, follow_redirects=True) as client:
            r = client.get(url)
            r.raise_for_status()
            text = r.text
            if len(text) > 15000:
                text = text[:15000] + "\n... (truncated)"
            return text
    except Exception as e:
        return f"Error fetching URL: {e}"

# Tool definitions for the model
TOOL_SPECS = [
    {
        "type": "function",
        "function": {
            "name": "list_dir",
            "description": "List files and directories relative to project root",
            "parameters": {"type": "object", "properties": {"path": {"type": "string"}}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "glob",
            "description": "Find files by glob pattern (e.g. **/*.py, src/**/*.ts)",
            "parameters": {
                "type": "object",
                "properties": {
                    "pattern": {"type": "string"},
                    "path": {"type": "string"},
                },
                "required": ["pattern"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Read a file with line numbers. Use offset/limit for large files.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string"},
                    "offset": {"type": "integer", "description": "1-based start line"},
                    "limit": {"type": "integer", "description": "max lines"},
                },
                "required": ["path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "write_file",
            "description": "Create or overwrite a file",
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
            "name": "edit",
            "description": "Precise edit: replace exact old_string with new_string (must be unique)",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string"},
                    "old_string": {"type": "string"},
                    "new_string": {"type": "string"},
                },
                "required": ["path", "old_string", "new_string"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "grep",
            "description": "Search file contents for a pattern",
            "parameters": {
                "type": "object",
                "properties": {
                    "pattern": {"type": "string"},
                    "path": {"type": "string"},
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
    {
        "type": "function",
        "function": {
            "name": "webfetch",
            "description": "Fetch a URL and return text content (docs, APIs, pages)",
            "parameters": {
                "type": "object",
                "properties": {"url": {"type": "string"}},
                "required": ["url"],
            },
        },
    },
]

def execute_tool(name: str, args: Dict[str, Any], allow_write: bool = True, allow_bash: bool = True) -> str:
    if name == "list_dir":
        return tool_list_dir(args.get("path", "."))
    if name == "glob":
        return tool_glob(args.get("pattern", "*"), args.get("path", "."))
    if name == "read_file":
        return tool_read_file(args.get("path", ""), args.get("offset", 1), args.get("limit", 200))
    if name == "write_file":
        if not allow_write:
            return "Error: write denied in Plan mode"
        return tool_write_file(args.get("path", ""), args.get("content", ""))
    if name == "edit":
        if not allow_write:
            return "Error: edit denied in Plan mode"
        return tool_edit(args.get("path", ""), args.get("old_string", ""), args.get("new_string", ""))
    if name == "grep":
        return tool_grep(args.get("pattern", ""), args.get("path", "."))
    if name == "bash":
        return tool_bash(args.get("command", ""), allow=allow_bash)
    if name == "webfetch":
        return tool_webfetch(args.get("url", ""))
    return f"Unknown tool: {name}"
