import requests
from typing import Any, List, Mapping, Optional
from langchain_core.language_models.llms import LLM

from ..core.config import settings


def _extract_text(data: dict) -> str:
    content = data.get("content", [])
    if isinstance(content, list):
        # Collect text blocks
        parts = [block.get("text", "") for block in content if block.get("type") == "text"]
        text = "".join(parts).strip()
        # Collect thinking blocks
        thinking_parts = [block.get("thinking", "") for block in content if block.get("type") == "thinking"]
        thinking = "".join(thinking_parts).strip()

        # If we have text blocks, prefer them
        if text:
            return text
        # If only thinking blocks, try to extract JSON from thinking
        if thinking:
            return thinking
    return str(content)


def _extract_all_blocks(data: dict) -> tuple[str, str, list[dict]]:
    """Returns (text, thinking, tool_use_blocks) from response."""
    content = data.get("content", [])
    texts = []
    thinkings = []
    tool_uses = []
    if isinstance(content, list):
        for block in content:
            btype = block.get("type", "")
            if btype == "text":
                texts.append(block.get("text", ""))
            elif btype == "thinking":
                thinkings.append(block.get("thinking", ""))
            elif btype == "tool_use":
                tool_uses.append(block)
    return "".join(texts).strip(), "".join(thinkings).strip(), tool_uses


def _build_headers() -> dict:
    return {
        "x-api-key": settings.mimo_api_key,
        "anthropic-version": "2023-06-01",
        "Content-Type": "application/json",
    }


def _api_url() -> str:
    base = settings.mimo_api_url.rstrip("/")
    if base.endswith("/v1/messages"):
        return base
    return f"{base}/v1/messages"


class MiMoClient(LLM):
    @property
    def _llm_type(self) -> str:
        return "mimo"

    def _call(self, prompt: str, stop: Optional[List[str]] = None) -> str:
        if not settings.mimo_api_key:
            raise ValueError("MIMO_API_KEY is not configured")

        payload = {
            "model": settings.mimo_model,
            "max_tokens": 512,
            "messages": [{"role": "user", "content": prompt}],
        }
        response = requests.post(_api_url(), json=payload, headers=_build_headers(), timeout=30)
        response.raise_for_status()
        return _extract_text(response.json())

    def chat_completion(
        self,
        messages: list[dict],
        max_tokens: int = 512,
        temperature: float = 0.1,
    ) -> str:
        if not settings.mimo_api_key:
            raise ValueError("MIMO_API_KEY is not configured")

        system_msg = ""
        filtered = []
        for msg in messages:
            if msg.get("role") == "system":
                system_msg = msg["content"]
            else:
                filtered.append(msg)

        payload = {
            "model": settings.mimo_model,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": filtered,
        }
        if system_msg:
            payload["system"] = system_msg

        response = requests.post(_api_url(), json=payload, headers=_build_headers(), timeout=60)
        response.raise_for_status()
        return _extract_text(response.json())

    def chat_completion_raw(
        self,
        messages: list[dict],
        max_tokens: int = 1024,
        temperature: float = 0.3,
        tools: list[dict] | None = None,
    ) -> dict:
        if not settings.mimo_api_key:
            raise ValueError("MIMO_API_KEY is not configured")

        system_msg = ""
        filtered = []
        for msg in messages:
            if msg.get("role") == "system":
                system_msg = msg["content"]
            else:
                filtered.append(msg)

        payload = {
            "model": settings.mimo_model,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": filtered,
        }
        if system_msg:
            payload["system"] = system_msg
        if tools:
            payload["tools"] = tools

        response = requests.post(_api_url(), json=payload, headers=_build_headers(), timeout=90)
        response.raise_for_status()
        return response.json()

    def _identifying_params(self) -> Mapping[str, Any]:
        return {
            "model": settings.mimo_model,
            "mimo_api_url": settings.mimo_api_url,
        }


def load_mimo() -> MiMoClient:
    return MiMoClient()
