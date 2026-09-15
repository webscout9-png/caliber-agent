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

def _usage_from(resp: Any) -> Dict[str, int]:
    u = getattr(resp, "usage", None)
    return {
        "prompt_tokens": getattr(u, "prompt_tokens", 0) or 0,
        "completion_tokens": getattr(u, "completion_tokens", 0) or 0,
        "total_tokens": getattr(u, "total_tokens", 0) or 0,
    }

def chat(
    model: str,
    messages: List[Dict[str, Any]],
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

    try:
        resp = client.chat.completions.create(**kwargs)
    except Exception as e:
        raise RuntimeError(f"OpenRouter chat failed ({model}): {e}") from e

    choice = resp.choices[0]
    return {
        "content": choice.message.content or "",
        "model": resp.model or model,
        "usage": _usage_from(resp),
        "tool_calls": None,
    }

def chat_with_tools(
    model: str,
    messages: List[Dict[str, Any]],
    tools: List[Dict[str, Any]],
    temperature: float = 0.3,
) -> Dict[str, Any]:
    """Chat with tools. Falls back to plain chat if the model rejects tools."""
    client = get_client()
    try:
        resp = client.chat.completions.create(
            model=model,
            messages=messages,
            tools=tools,
            temperature=temperature,
        )
    except Exception as e:
        err = str(e).lower()
        # Many free / small models don't support tools — fall back
        if any(x in err for x in ("tool", "function", "not supported", "unsupported", "400", "invalid")):
            # strip tool role messages for plain fallback
            plain_msgs = []
            for m in messages:
                role = m.get("role")
                if role == "tool":
                    plain_msgs.append({
                        "role": "user",
                        "content": f"[tool result]\n{m.get('content', '')}",
                    })
                elif role == "assistant" and m.get("tool_calls"):
                    plain_msgs.append({
                        "role": "assistant",
                        "content": m.get("content") or "[called tools]",
                    })
                else:
                    plain_msgs.append({"role": role, "content": m.get("content") or ""})
            return chat(model, plain_msgs, temperature=temperature)
        raise RuntimeError(f"OpenRouter tools call failed ({model}): {e}") from e

    choice = resp.choices[0]
    msg = choice.message

    tool_calls = None
    if getattr(msg, "tool_calls", None):
        tool_calls = []
        for tc in msg.tool_calls:
            tool_calls.append({
                "id": getattr(tc, "id", "call") or "call",
                "type": "function",
                "function": {
                    "name": tc.function.name,
                    "arguments": tc.function.arguments or "{}",
                },
            })

    return {
        "content": msg.content or "",
        "model": resp.model or model,
        "usage": _usage_from(resp),
        "tool_calls": tool_calls,
    }
