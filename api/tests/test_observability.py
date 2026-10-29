from unittest.mock import Mock
from uuid import uuid4

import pytest
from dbos import DBOSClient
from fastapi import FastAPI
from fastapi.testclient import TestClient
from logfire.testing import CaptureLogfire
from pydantic import SecretStr
from pytest import MonkeyPatch
from sqlalchemy.exc import OperationalError

from agora_api.api.deps import get_workflow_client
from agora_api.config import settings


def test_request_bodies_and_credentials_are_not_recorded(
    app: FastAPI, capfire: CaptureLogfire, monkeypatch: MonkeyPatch
) -> None:
    secret = "controlled-server-secret"
    body_marker = "controlled-request-body-marker"
    monkeypatch.setattr(settings, "postgres_password", SecretStr(secret))
    client = Mock(spec=DBOSClient)
    app.dependency_overrides[get_workflow_client] = lambda: client

    response = TestClient(app).post(
        "/workflows",
        json={
            "operation": "add_then_scale",
            "inputs": {"left": 1, "right": 2, "credential": body_marker},
        },
    )
    assert response.status_code == 422
    client.enqueue.assert_not_called()
    assert secret not in response.text
    spans = capfire.exporter.exported_spans_as_dict()
    assert any(span["attributes"].get("http.status_code") == 422 for span in spans)
    assert secret not in str(spans)
    assert body_marker not in str(spans)


@pytest.mark.parametrize("method", ["POST", "GET"])
def test_storage_error_details_are_not_exported(
    method: str, app: FastAPI, capfire: CaptureLogfire, monkeypatch: MonkeyPatch
) -> None:
    secret = "controlled-database-error-detail"
    client = Mock(spec=DBOSClient)
    storage_error = OperationalError("private connection", {}, Exception(secret))
    client.enqueue.side_effect = storage_error
    client.retrieve_workflow.return_value.get_status.side_effect = storage_error
    monkeypatch.setattr("agora_api.api.deps.DBOSClient", Mock(return_value=client))

    http = TestClient(app)
    response = (
        http.post(
            "/workflows", json={"operation": "add_then_scale", "inputs": {"left": 1, "right": 2}}
        )
        if method == "POST"
        else http.get(f"/workflows/{uuid4()}")
    )
    assert response.status_code == 503
    assert secret not in response.text
    spans = capfire.exporter.exported_spans_as_dict()
    assert any(span["attributes"].get("http.status_code") == 503 for span in spans)
    assert secret not in str(spans)
