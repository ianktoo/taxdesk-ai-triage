"""OpenAI adapter for the TextGenerator capability.

Uses the Chat Completions API with JSON-mode output to turn a short
scenario prompt into a customer name + message for a new demo persona.
"""
import json

import httpx

from api.config import settings
from api.integrations.text_generation.base import (
    GeneratedPersonaText,
    TextGenerationError,
)

_SYSTEM_PROMPT = (
    "You invent short, realistic customer-support scenarios for a tax-prep "
    "business demo. Given a one-line scenario from the agent, invent a "
    "plausible customer name and write the message that customer would send "
    "in, as if emailing in a request. Keep it under 80 words, first person, "
    "casual but clear. No real people, no real PII. Respond with JSON only: "
    '{"display_name": "...", "message": "..."}'
)


class OpenAITextGenerator:
    def __init__(self, api_key: str | None = None, model: str | None = None):
        self._api_key = api_key or settings.OPENAI_API_KEY
        self._model = model or settings.OPENAI_TEXT_MODEL
        if not self._api_key:
            raise TextGenerationError("OPENAI_API_KEY is not set, cannot use the OpenAI adapter")

    def generate_persona(self, scenario: str) -> GeneratedPersonaText:
        try:
            response = httpx.post(
                "https://api.openai.com/v1/chat/completions",
                headers={"Authorization": f"Bearer {self._api_key}"},
                json={
                    "model": self._model,
                    "messages": [
                        {"role": "system", "content": _SYSTEM_PROMPT},
                        {"role": "user", "content": scenario},
                    ],
                    "response_format": {"type": "json_object"},
                    "temperature": 0.9,
                },
                timeout=30.0,
            )
            response.raise_for_status()
        except httpx.HTTPError as exc:
            raise TextGenerationError(f"OpenAI request failed: {exc}") from exc

        try:
            payload = response.json()
            content = payload["choices"][0]["message"]["content"]
            parsed = json.loads(content)
            return GeneratedPersonaText(
                display_name=str(parsed["display_name"]),
                message=str(parsed["message"]),
            )
        except (KeyError, IndexError, ValueError) as exc:
            raise TextGenerationError(f"Unexpected OpenAI response shape: {exc}") from exc
