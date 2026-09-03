"""OpenAI adapter for the Reasoning capability.

Uses Chat Completions in JSON mode. Every vendor error, transport
error, and malformed-response case is normalized to ReasoningError so
agents never see an httpx or OpenAI exception.
"""
import json

import httpx

from api.config import settings
from api.integrations.reasoning.base import (
    ReasoningError,
    ReasoningRequest,
    ReasoningResult,
)

# Applies to every agent on top of its own instructions. The last two
# sentences matter more than they look: agents run on real extraction
# output, and a model that invents a field value or a confidence score
# would silently corrupt the audit trail the whole product rests on.
_BASE_SYSTEM_PROMPT = (
    "You are one specialist agent inside a document triage pipeline for a "
    "tax-preparation firm. You are given a structured JSON payload and must "
    "return a single JSON object matching the requested schema, with no "
    "commentary and no markdown fences.\n"
    "Work only from the payload. Never invent a field value, a document, or a "
    "confidence score that is not present in it. If the payload does not "
    "support an answer, say so in the designated field rather than guessing."
)


class OpenAIReasoner:
    def __init__(self, api_key: str | None = None, model: str | None = None):
        self._api_key = api_key or settings.OPENAI_API_KEY
        self._model = model or settings.OPENAI_REASONING_MODEL
        if not self._api_key:
            raise ReasoningError("OPENAI_API_KEY is not set, cannot use the OpenAI reasoner")

    def reason(self, request: ReasoningRequest) -> ReasoningResult:
        user_content = (
            f"Task: {request.task}\n\n"
            f"{request.instructions}\n\n"
            f"Return JSON matching this shape:\n{request.schema_hint}\n\n"
            f"Payload:\n{json.dumps(request.payload, ensure_ascii=False)}"
        )

        try:
            response = httpx.post(
                "https://api.openai.com/v1/chat/completions",
                headers={"Authorization": f"Bearer {self._api_key}"},
                json={
                    "model": self._model,
                    "messages": [
                        {"role": "system", "content": _BASE_SYSTEM_PROMPT},
                        {"role": "user", "content": user_content},
                    ],
                    "response_format": {"type": "json_object"},
                    # Low but non-zero: these are judgement tasks with a
                    # single defensible answer, not creative writing.
                    "temperature": 0.2,
                },
                timeout=settings.REASONING_TIMEOUT_SECONDS,
            )
            response.raise_for_status()
        except httpx.HTTPError as exc:
            raise ReasoningError(f"OpenAI reasoning request failed: {exc}") from exc

        try:
            payload = response.json()
            content = payload["choices"][0]["message"]["content"]
            data = json.loads(content)
        except (KeyError, IndexError, ValueError) as exc:
            raise ReasoningError(f"Unexpected OpenAI response shape: {exc}") from exc

        if not isinstance(data, dict):
            raise ReasoningError("Reasoner returned JSON that is not an object")

        return ReasoningResult(data=data, model=self._model)
