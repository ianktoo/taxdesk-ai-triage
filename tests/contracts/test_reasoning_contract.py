import pytest

from api.integrations.reasoning.base import ReasoningError, ReasoningRequest
from api.integrations.reasoning.mock_adapter import MockReasoner

TASKS = ["classify", "compare", "validate", "summarize", "respond"]


def _request(task: str, payload: dict) -> ReasoningRequest:
    return ReasoningRequest(task=task, instructions="", payload=payload, schema_hint="")


@pytest.mark.parametrize("task", TASKS)
def test_mock_reasoner_answers_every_task_the_agents_use(task):
    # The mock is the fallback every agent degrades to, so a task with
    # no handler would turn one flaky model call into a failed request.
    result = MockReasoner().reason(_request(task, {}))

    assert isinstance(result.data, dict)
    assert result.model


def test_mock_reasoner_rejects_an_unknown_task():
    with pytest.raises(ReasoningError):
        MockReasoner().reason(_request("not-a-real-task", {}))


def test_mock_reasoner_classifies_from_document_type():
    result = MockReasoner().reason(
        _request(
            "classify",
            {
                "message": "I moved house",
                "documents": [
                    {"filename": "change_of_address_form.pdf", "document_type": "change_of_address_form"}
                ],
            },
        )
    )

    assert result.data["category"] == "change_of_address"
    assert result.data["evidence_filenames"] == ["change_of_address_form.pdf"]


def test_mock_reasoner_treats_unjudged_differences_as_conflicts():
    result = MockReasoner().reason(
        _request("compare", {"groups": [{"field": "address", "observations": []}]})
    )

    assert result.data["verdicts"][0]["equivalent"] is False
