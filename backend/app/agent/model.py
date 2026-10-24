"""Bounded Ollama transport. Fixed loopback host; no proxies, redirects or pulls."""
import asyncio

import httpx

from app.agent.contracts import AgentRejected, Limits, decode, encode

MODELS = ("llama3.2:3b", "qwen3.5:4b-q4_K_M")


class OllamaClient:
    def __init__(self, model="llama3.2:3b", *, limits=Limits()):
        if model not in MODELS:
            raise ValueError("Only the two preinstalled benchmark models are permitted")
        self.model, self.limits = model, limits

    async def request(self, path, payload=None):
        if path not in {"/api/chat", "/api/tags", "/api/ps"}:
            raise AgentRejected("forbidden_model_endpoint")
        body = None if payload is None else encode(payload, self.limits.max_prompt_bytes)
        async with asyncio.timeout(self.limits.model_timeout):
            async with httpx.AsyncClient(trust_env=False, follow_redirects=False,
                                         timeout=self.limits.model_timeout) as client:
                async with client.stream("GET" if payload is None else "POST",
                        "http://127.0.0.1:11434" + path, content=body,
                        headers={"Content-Type": "application/json"}) as response:
                    if response.status_code != 200:
                        raise AgentRejected("model_unavailable")
                    data = bytearray()
                    async for chunk in response.aiter_bytes():
                        data.extend(chunk)
                        if len(data) > self.limits.max_response_bytes:
                            raise AgentRejected("response_too_large")
        return decode(bytes(data), self.limits.max_response_bytes)

    async def chat(self, messages, tools):
        return await self.request("/api/chat", {"model": self.model, "messages": messages,
            "tools": tools, "stream": False, "think": False, "keep_alive": "5m",
            "options": {"temperature": 0, "seed": 7, "num_ctx": self.limits.context_tokens,
                        "num_predict": self.limits.prediction_tokens}})

    async def synthesize(self, messages):
        # No tools and no model provisioning; same fixed local transport/limits.
        from app.agent.synthesis import Selection
        return await self.request("/api/chat", {"model": self.model, "messages": messages,
            "format": Selection.model_json_schema(), "stream": False, "think": False, "keep_alive": "5m",
            "options": {"temperature": 0, "seed": 7, "num_ctx": self.limits.context_tokens,
                        "num_predict": self.limits.prediction_tokens}})
