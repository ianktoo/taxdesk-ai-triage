"""Mock SpeechSynthesizer, generates a short placeholder tone instead of
real speech (stdlib only, no network calls, no extra dependencies), so
the "listen" UI is exercisable before an OpenAI key is configured.
"""
import io
import math
import struct
import wave

from api.integrations.speech_synthesis.base import SynthesizedSpeech

_SAMPLE_RATE = 22050


class MockSpeechSynthesizer:
    def synthesize(self, text: str) -> SynthesizedSpeech:
        duration_seconds = max(0.6, min(len(text) / 40, 2.5))
        num_samples = int(_SAMPLE_RATE * duration_seconds)

        buffer = io.BytesIO()
        with wave.open(buffer, "wb") as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(_SAMPLE_RATE)
            frames = bytearray()
            for i in range(num_samples):
                t = i / _SAMPLE_RATE
                value = int(6000 * math.sin(2 * math.pi * 440 * t) * math.exp(-3 * (t % 0.5)))
                frames.extend(struct.pack("<h", value))
            wav_file.writeframes(bytes(frames))

        return SynthesizedSpeech(audio_bytes=buffer.getvalue(), content_type="audio/wav")
