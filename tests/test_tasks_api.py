from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from services.api.app.main import app
from services.api.app.task_service import task_service

client = TestClient(app)


@pytest.fixture(autouse=True)
def clear_task_store() -> None:
    task_service.store.clear()


def create_task(symbol: str = "NVDA") -> dict:
    response = client.post(
        "/api/v1/tasks",
        json={"symbol": symbol, "market": "US", "horizon_days": 5},
    )
    assert response.status_code == 202
    return response.json()


def test_create_and_query_task() -> None:
    created = create_task(" nvda ")

    response = client.get(f"/api/v1/tasks/{created['task_id']}")

    assert response.status_code == 200
    task = response.json()
    assert task["status"] == "queued"
    assert task["request"]["symbol"] == "NVDA"
    assert task["trace_id"] == created["trace_id"]
    assert len(task["timeline"]) == 6


def test_list_tasks_returns_newest_first() -> None:
    first = create_task("AAPL")
    second = create_task("NVDA")

    response = client.get("/api/v1/tasks")

    assert response.status_code == 200
    tasks = response.json()
    assert [task["task_id"] for task in tasks] == [second["task_id"], first["task_id"]]


def test_run_task_returns_explainable_mock_report() -> None:
    created = create_task()

    response = client.post(f"/api/v1/tasks/{created['task_id']}/run")

    assert response.status_code == 200
    task = response.json()
    assert task["status"] == "succeeded"
    assert [step["status"] for step in task["timeline"]] == ["succeeded"] * 6
    assert task["report"]["prediction"]["model_name"] == "mock-rule-model-v0.1"
    assert task["report"]["evidence"][0]["metadata"]["mock"] is True
    assert "不构成投资建议" in task["report"]["disclaimer"]


def test_completed_task_cannot_run_twice() -> None:
    created = create_task()
    client.post(f"/api/v1/tasks/{created['task_id']}/run")

    response = client.post(f"/api/v1/tasks/{created['task_id']}/run")

    assert response.status_code == 409


def test_cancel_queued_task_and_block_execution() -> None:
    created = create_task()

    cancelled = client.delete(f"/api/v1/tasks/{created['task_id']}")
    run_response = client.post(f"/api/v1/tasks/{created['task_id']}/run")

    assert cancelled.status_code == 200
    assert cancelled.json()["status"] == "cancelled"
    assert run_response.status_code == 409


def test_unknown_task_returns_404() -> None:
    response = client.get(f"/api/v1/tasks/{uuid4()}")

    assert response.status_code == 404
    payload = response.json()["error"]
    assert payload["code"] == "task_not_found"
    assert payload["module_code"] == "PLT-03"
    assert payload["trace_id"]


def test_invalid_request_returns_422() -> None:
    response = client.post(
        "/api/v1/tasks",
        json={"symbol": "invalid symbol!", "market": "US", "horizon_days": 0},
    )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "request_validation_failed"
