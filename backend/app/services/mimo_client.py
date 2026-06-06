"""
MiMo LLM 客户端 — 封装与 MiMo API 的交互

使用 Anthropic Messages API 格式与 MiMo 大模型通信。
支持普通对话、工具调用等能力。
"""

import requests
from flask import current_app


def _extract_text(data: dict) -> str:
    """从响应中提取文本内容"""
    content = data.get("content", [])
    if isinstance(content, list):
        parts = [block.get("text", "") for block in content if block.get("type") == "text"]
        text = "".join(parts).strip()
        thinking_parts = [block.get("thinking", "") for block in content if block.get("type") == "thinking"]
        thinking = "".join(thinking_parts).strip()
        if text:
            return text
        if thinking:
            return thinking
    return str(content)


def _extract_all_blocks(data: dict) -> tuple[str, str, list[dict]]:
    """从响应中提取所有内容块：(text, thinking, tool_use_blocks)"""
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


def _build_headers(api_key: str) -> dict:
    return {
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
        "Content-Type": "application/json",
    }


def _api_url(base_url: str) -> str:
    base = base_url.rstrip("/")
    if base.endswith("/v1/messages"):
        return base
    return f"{base}/v1/messages"


class MiMoClient:
    """MiMo LLM 客户端"""

    def __init__(self, api_key: str, api_url: str, model: str):
        self.api_key = api_key
        self.api_url = api_url
        self.model = model

    def chat_completion(self, messages: list[dict], max_tokens: int = 512, temperature: float = 0.1) -> str:
        """普通对话补全"""
        system_msg = ""
        filtered = []
        for msg in messages:
            if msg.get("role") == "system":
                system_msg = msg["content"]
            else:
                filtered.append(msg)

        payload = {
            "model": self.model,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": filtered,
        }
        if system_msg:
            payload["system"] = system_msg

        response = requests.post(
            _api_url(self.api_url), json=payload,
            headers=_build_headers(self.api_key), timeout=60,
        )
        response.raise_for_status()
        return _extract_text(response.json())

    def chat_completion_raw(
        self, messages: list[dict], max_tokens: int = 1024,
        temperature: float = 0.3, tools: list[dict] | None = None,
    ) -> dict:
        """带工具调用的对话补全，返回原始响应"""
        system_msg = ""
        filtered = []
        for msg in messages:
            if msg.get("role") == "system":
                system_msg = msg["content"]
            else:
                filtered.append(msg)

        payload = {
            "model": self.model,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": filtered,
        }
        if system_msg:
            payload["system"] = system_msg
        if tools:
            payload["tools"] = tools

        response = requests.post(
            _api_url(self.api_url), json=payload,
            headers=_build_headers(self.api_key), timeout=90,
        )
        response.raise_for_status()
        return response.json()


def load_mimo() -> MiMoClient:
    """从 Flask 配置加载 MiMo 客户端"""
    return MiMoClient(
        api_key=current_app.config["MIMO_API_KEY"],
        api_url=current_app.config["MIMO_API_URL"],
        model=current_app.config["MIMO_MODEL"],
    )
