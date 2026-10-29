import pytest
from pydantic import ValidationError

from agora_worker.models import WorkflowResult


@pytest.mark.parametrize("value", ["credential-shaped-value", float("nan"), float("inf")])
def test_workflow_result_rejects_invalid_values(value: object) -> None:
    with pytest.raises(ValidationError):
        WorkflowResult.model_validate({"value": value, "branch": "unchanged"})
