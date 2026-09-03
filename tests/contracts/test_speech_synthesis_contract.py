from api.integrations.speech_synthesis.mock_adapter import MockSpeechSynthesizer


def test_mock_synthesizer_satisfies_speech_synthesis_contract():
    synthesizer = MockSpeechSynthesizer()
    result = synthesizer.synthesize("Hello, this is a test message.")

    assert result.audio_bytes
    assert result.content_type == "audio/wav"
