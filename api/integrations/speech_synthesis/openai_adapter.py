"""OpenAI adapter for the SpeechSynthesizer capability, using the
text-to-speech API to read a customer's message aloud.
"""
import httpx

from api.config import settings
from api.integrations.speech_synthesis.base import (
    SpeechSynthesisError,
    SynthesizedSpeech,
)


class OpenAISpeechSynthesizer:
    def __init__(self, api_key: str | None = None, model: str | None = None, voice: str | None = None):
        self._api_key = api_key or settings.OPENAI_API_KEY
        self._model = model or settings.OPENAI_TTS_MODEL
        self._voice = voice or settings.OPENAI_TTS_VOICE
        if not self._api_key:
            raise SpeechSynthesisError("OPENAI_API_KEY is not set, cannot use the OpenAI adapter")

    def synthesize(self, text: str) -> SynthesizedSpeech:
        try:
            response = httpx.post(
                "https://api.openai.com/v1/audio/speech",
                headers={"Authorization": f"Bearer {self._api_key}"},
                json={
                    "model": self._model,
                    "voice": self._voice,
                    "input": text,
                    "response_format": "mp3",
                },
                timeout=30.0,
            )
            response.raise_for_status()
        except httpx.HTTPError as exc:
            raise SpeechSynthesisError(f"OpenAI TTS request failed: {exc}") from exc

        return SynthesizedSpeech(audio_bytes=response.content, content_type="audio/mpeg")
