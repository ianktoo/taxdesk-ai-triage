"""Business logic: text-to-speech with caching.

Talks to the SpeechSynthesizer and KeyValueCache capabilities only
through their contracts. No vendor SDK imports here.
"""
import base64
import hashlib

from api.integrations.cache.base import KeyValueCache
from api.integrations.speech_synthesis.base import SpeechSynthesizer, SynthesizedSpeech

MAX_TEXT_LENGTH = 600
CACHE_TTL_SECONDS = 30 * 24 * 60 * 60  # 30 days, generated speech for demo text never changes


def _cache_key(text: str) -> str:
    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
    return f"speech:{digest}"


def synthesize_with_cache(text: str, synthesizer: SpeechSynthesizer, cache: KeyValueCache) -> SynthesizedSpeech:
    text = text.strip()[:MAX_TEXT_LENGTH]
    if not text:
        raise ValueError("Text cannot be empty")

    key = _cache_key(text)
    cached = cache.get(key)
    if cached:
        content_type, _, encoded = cached.partition("|")
        return SynthesizedSpeech(audio_bytes=base64.b64decode(encoded), content_type=content_type)

    result = synthesizer.synthesize(text)

    encoded_value = f"{result.content_type}|{base64.b64encode(result.audio_bytes).decode('ascii')}"
    cache.set(key, encoded_value, CACHE_TTL_SECONDS)

    return result
