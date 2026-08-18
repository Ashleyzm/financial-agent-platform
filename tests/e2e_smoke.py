"""Docker Compose smoke test for API -> Redis -> Worker -> Graph -> PostgreSQL."""

import json
import time
import urllib.request

API = "http://localhost:8000"


def request(path: str, *, method: str = "GET", payload: dict | None = None) -> dict:
    body = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(
        f"{API}{path}", data=body, method=method, headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req, timeout=15) as response:
        return json.load(response)


def main() -> None:
    assert request("/health")["status"] == "ok"
    created = request(
        "/api/v1/tasks",
        method="POST",
        payload={"symbol": "NVDA", "market": "US", "horizon_days": 5},
    )
    task_id = created["task_id"]
    task = None
    for _ in range(60):
        task = request(f"/api/v1/tasks/{task_id}")
        if task["status"] in {"succeeded", "failed", "cancelled"}:
            break
        time.sleep(1)

    assert task is not None
    assert task["status"] == "succeeded", task
    assert task["report"] is not None
    assert [step["status"] for step in task["timeline"]] == ["succeeded"] * 6
    assert all(step["module_code"] for step in task["timeline"])
    assert task["model_usage"]["provider"] == "mock"
    print(json.dumps({"task_id": task_id, "status": task["status"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
