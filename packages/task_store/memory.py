"""Thread-safe in-memory task store and queue, used by tests and as a fallback."""

from collections import deque
from copy import deepcopy
from threading import RLock
from uuid import UUID

from packages.agent_runtime.state import AgentState
from packages.contracts import TaskStatus, utc_now
from packages.task_store.base import (
    InvalidTaskTransitionError,
    TaskNotFoundError,
)


class InMemoryTaskStore:
    def __init__(self) -> None:
        self._states: dict[UUID, AgentState] = {}
        self._lock = RLock()

    def save(self, state: AgentState) -> None:
        with self._lock:
            self._states[state["task_id"]] = deepcopy(state)

    def get(self, task_id: UUID) -> AgentState:
        with self._lock:
            return deepcopy(self._get_existing(task_id))

    def list(self) -> list[AgentState]:
        with self._lock:
            states = sorted(
                self._states.values(),
                key=lambda state: state["created_at"],
                reverse=True,
            )
            return deepcopy(states)

    def claim_for_run(self, task_id: UUID) -> AgentState:
        with self._lock:
            state = self._get_existing(task_id)
            if state["status"] is not TaskStatus.QUEUED:
                raise InvalidTaskTransitionError(
                    f"task status {state['status']} does not allow execution"
                )
            state["status"] = TaskStatus.RUNNING
            state["updated_at"] = utc_now()
            return deepcopy(state)

    def cancel_queued(self, task_id: UUID) -> AgentState:
        with self._lock:
            state = self._get_existing(task_id)
            if state["status"] is TaskStatus.CANCELLED:
                return deepcopy(state)
            if state["status"] is not TaskStatus.QUEUED:
                raise InvalidTaskTransitionError(
                    f"task status {state['status']} does not allow cancellation"
                )
            state["status"] = TaskStatus.CANCELLED
            state["current_agent"] = None
            state["updated_at"] = utc_now()
            return deepcopy(state)

    def clear(self) -> None:
        with self._lock:
            self._states.clear()

    def close(self) -> None:
        self.clear()

    def _get_existing(self, task_id: UUID) -> AgentState:
        state = self._states.get(task_id)
        if state is None:
            raise TaskNotFoundError(str(task_id))
        return state


class InMemoryTaskQueue:
    def __init__(self) -> None:
        self._items: deque[UUID] = deque()
        self._lock = RLock()

    def enqueue(self, task_id: UUID) -> None:
        with self._lock:
            self._items.append(task_id)

    def dequeue(self, timeout: float) -> UUID | None:
        with self._lock:
            if not self._items:
                return None
            return self._items.popleft()

    def remove(self, task_id: UUID) -> None:
        with self._lock:
            self._items = deque(item for item in self._items if item != task_id)

    def close(self) -> None:
        with self._lock:
            self._items.clear()
