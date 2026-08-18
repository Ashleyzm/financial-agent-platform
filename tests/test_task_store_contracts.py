"""Unit coverage for the new persistence and queue abstractions."""

from uuid import uuid4

from psycopg.types.json import Jsonb

from packages.agent_runtime import create_initial_state
from packages.contracts import ForecastRequest, Market, TaskStatus
from packages.task_store import InMemoryTaskQueue, InMemoryTaskStore, PostgresTaskStore
from packages.task_store.serialization import state_from_dict, state_to_dict


def test_state_roundtrip_preserves_agent_state() -> None:
    state = create_initial_state(ForecastRequest(symbol="NVDA", market=Market.US, horizon_days=5))
    state["research_summary"] = "mock summary"

    restored = state_from_dict(state_to_dict(state))

    assert restored["task_id"] == state["task_id"]
    assert restored["trace_id"] == state["trace_id"]
    assert restored["request"] == state["request"]
    assert restored["status"] is state["status"]
    assert restored["timeline"][0].agent == state["timeline"][0].agent
    assert restored["research_summary"] == "mock summary"


def test_in_memory_store_claims_and_cancels() -> None:
    store = InMemoryTaskStore()
    state = create_initial_state(ForecastRequest(symbol="AAPL", market=Market.US, horizon_days=5))
    store.save(state)

    claimed = store.claim_for_run(state["task_id"])
    assert claimed["status"] is TaskStatus.RUNNING
    assert store.get(state["task_id"])["status"] is TaskStatus.RUNNING


def test_in_memory_queue_fifo() -> None:
    queue = InMemoryTaskQueue()
    first = uuid4()
    second = uuid4()

    queue.enqueue(first)
    queue.enqueue(second)

    assert queue.dequeue(timeout=0) == first
    assert queue.dequeue(timeout=0) == second
    assert queue.dequeue(timeout=0) is None


class _FakeConnection:
    def __init__(self) -> None:
        self.calls: list[tuple[str, tuple[object, ...] | None]] = []

    def execute(self, query: str, params: tuple[object, ...] | None = None) -> None:
        self.calls.append((query, params))

    def __enter__(self) -> "_FakeConnection":
        return self

    def __exit__(self, *args: object) -> None:
        return None


class _FakePool:
    def __init__(self) -> None:
        self.connection_instance = _FakeConnection()

    def connection(self) -> _FakeConnection:
        return self.connection_instance


def test_postgres_store_adapts_payload_as_jsonb() -> None:
    pool = _FakePool()
    store = PostgresTaskStore("unused", pool=pool)  # type: ignore[arg-type]
    state = create_initial_state(ForecastRequest(symbol="NVDA"))

    store.save(state)

    _, params = pool.connection_instance.calls[-1]
    assert params is not None
    assert isinstance(params[3], Jsonb)
    assert params[3].obj["task_id"] == str(state["task_id"])
