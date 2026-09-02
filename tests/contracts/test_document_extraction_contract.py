from api.integrations.document_extraction.mock_adapter import MockDocumentExtractor


def test_mock_adapter_satisfies_extraction_contract():
    extractor = MockDocumentExtractor()
    result = extractor.extract("unused/path", "change_of_address_form.pdf")

    assert result.document_type == "change_of_address_form"
    assert 0.0 <= result.document_type_confidence <= 1.0
    assert result.fields
    for f in result.fields:
        assert 0.0 <= f.confidence <= 1.0
        assert f.name and f.value
