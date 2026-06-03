from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Protocol

import httpx


class LLMProviderError(RuntimeError):
    pass


@dataclass(frozen=True)
class LLMProviderResponse:
    text: str
    provider: str
    model: str


class AssistantLLMProvider(Protocol):
    async def generate_answer(self, *, system_prompt: str, user_prompt: str) -> LLMProviderResponse:
        ...


class MockLLMProvider:
    async def generate_answer(self, *, system_prompt: str, user_prompt: str) -> LLMProviderResponse:
        return LLMProviderResponse(
            text=(
                "Here is a short public-data review summary based only on the DAV AI "
                "context provided. Use the source details, audit ID, and limitations to "
                "verify the result in the official public source."
            ),
            provider="mock",
            model="mock-assistant-v0.1",
        )


class OpenAILLMProvider:
    def __init__(self, *, api_key: str, model: str):
        self.api_key = api_key
        self.model = model

    async def generate_answer(self, *, system_prompt: str, user_prompt: str) -> LLMProviderResponse:
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": 0.1,
            "max_tokens": 350,
        }

        try:
            async with httpx.AsyncClient(timeout=20.0) as client:
                response = await client.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                    },
                    json=payload,
                )
        except httpx.HTTPError as exc:
            raise LLMProviderError("OpenAI assistant provider request failed.") from exc

        if response.status_code >= 400:
            raise LLMProviderError("OpenAI assistant provider request failed.")

        try:
            body = response.json()
        except ValueError as exc:
            raise LLMProviderError("OpenAI assistant provider returned invalid JSON.") from exc
        text = body.get("choices", [{}])[0].get("message", {}).get("content", "")

        if not text.strip():
            raise LLMProviderError("OpenAI assistant provider returned an empty answer.")

        return LLMProviderResponse(text=text.strip(), provider="openai", model=self.model)


class GeminiLLMProvider:
    def __init__(self, *, api_key: str, model: str):
        self.api_key = api_key
        self.model = model

    async def generate_answer(self, *, system_prompt: str, user_prompt: str) -> LLMProviderResponse:
        url = (
            f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:"
            f"generateContent?key={self.api_key}"
        )
        payload = {
            "systemInstruction": {
                "parts": [{"text": system_prompt}],
            },
            "contents": [
                {
                    "role": "user",
                    "parts": [{"text": user_prompt}],
                }
            ],
            "generationConfig": {
                "temperature": 0.1,
                "maxOutputTokens": 350,
            },
        }

        try:
            async with httpx.AsyncClient(timeout=20.0) as client:
                response = await client.post(url, json=payload)
        except httpx.HTTPError as exc:
            raise LLMProviderError("Gemini assistant provider request failed.") from exc

        if response.status_code >= 400:
            raise LLMProviderError("Gemini assistant provider request failed.")

        try:
            body = response.json()
        except ValueError as exc:
            raise LLMProviderError("Gemini assistant provider returned invalid JSON.") from exc
        text = (
            body.get("candidates", [{}])[0]
            .get("content", {})
            .get("parts", [{}])[0]
            .get("text", "")
        )

        if not text.strip():
            raise LLMProviderError("Gemini assistant provider returned an empty answer.")

        return LLMProviderResponse(text=text.strip(), provider="gemini", model=self.model)


def assistant_llm_enabled() -> bool:
    return os.getenv("ASSISTANT_LLM_ENABLED", "false").strip().lower() == "true"


def get_assistant_provider() -> AssistantLLMProvider:
    if not assistant_llm_enabled():
        return MockLLMProvider()

    provider = os.getenv("ASSISTANT_LLM_PROVIDER", "openai").strip().lower()
    model = os.getenv("ASSISTANT_LLM_MODEL", "").strip()
    api_key = os.getenv("ASSISTANT_LLM_API_KEY", "").strip()

    if not model or not api_key:
        raise LLMProviderError("Assistant LLM provider is not configured.")

    if provider == "openai":
        return OpenAILLMProvider(api_key=api_key, model=model)

    if provider == "gemini":
        return GeminiLLMProvider(api_key=api_key, model=model)

    raise LLMProviderError("Unsupported assistant LLM provider.")
