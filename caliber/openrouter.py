from __future__ import annotations

from typing import Any, Dict, List, Optional

from openai import OpenAI

from .config import get_api_key

BASE_URL = "https://openrouter.ai/api/v1"

def get_client() -> OpenAI:
    key = get_api_key()
    if not key:
        raise RuntimeError("No OpenRouter API key set. Use /provider to add one.")
    return OpenAI(
        base_url=BASE_URL,
        api_key=key,
        default_headers={
            "HTTP-Referer": "https://github.com/webscout9-png/caliber-agent",
            "X-Title": "Caliber Agent",
        },
    )

def chat(
    model: str,
    messages: List[Dict[str, str]],
    temperature: float = 0.4,
    max_tokens: Optional[int] = None,
) -> Dict[str, Any]:
    client = get_client()
    kwargs: Dict[str, Any] = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
    }
    if max_tokens is not None:
        kwargs["max_tokens"] = max_tokens

    resp = client.chat.completions.create(**kwargs)
    choice = resp.choices[0]
    usage = {
        "prompt_tokens": getattr(resp.usage, "prompt_tokens", 0) or 0,
        "completion_tokens": getattr(resp.usage, "completion_tokens", 0) or 0,
        "total_tokens": getattr(resp.usage, "total_tokens", 0) or 0,
    }
    return {
        "content": choice.message.content or "",
        "model": resp.model or model,
        "usage": usage,
        "tool_calls": None,
    }

def chat_with_tools(
    model: str,
    messages: List[Dict[str, Any]],
    tools: List[Dict[str, Any]],
    temperature: float = 0.3,
) -> Dict[str, Any]:
    """Chat with tool calling support."""
    client = get_client()
    resp = client.chat.completions.create(
        model=model,
        messages=messages,
        tools=tools,
        temperature=temperature,
    )
    choice = resp.choices[0]
    msg = choice.message

    tool_calls = None
    if getattr(msg, "tool_calls", None):
        tool_calls = []
        for tc in msg.tool_calls:
            tool_calls.append({
                "id": tc.id,
                "type": "function",
                "function": {
                    "name": tc.function.name,
                    "arguments": tc.function.arguments or "{}",
                },
            })

    usage = {
        "prompt_tokens": getattr(resp.usage, "prompt_tokens", 0) or 0,
        "completion_tokens": getattr(resp.usage, "completion_tokens", 0) or 0,
        "total_tokens": getattr(resp.usage, "total_tokens", 0) or 0,
    }
    return {
        "content": msg.content or "",
        "model": resp.model or model,
        "usage": usage,
        "tool_calls": tool_calls,
    }
