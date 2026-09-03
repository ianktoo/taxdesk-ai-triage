from api.integrations.text_generation.mock_adapter import MockTextGenerator


def test_mock_generator_satisfies_text_generation_contract():
    generator = MockTextGenerator()
    result = generator.generate_persona("Lost my W-2 and need a replacement")

    assert result.display_name
    assert result.message
