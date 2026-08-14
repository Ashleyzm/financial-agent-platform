"""Contracts implemented by every task persistence and queue backend."""

from typing import Protocol
from uuid import UUID

from packages.agent_runtime.state import AgentState


class TaskNotFoundError(LookupError):
    """Raised when a task identifier is not present in the store."""


class InvalidTaskTransitionError(RuntimeError):
    """Raised when a task cannot move to the requested state."""


class TaskStore(Protocol):
    def save(self, state: AgentState) -> None: ...

    def get(self, task_id: UUID) -> AgentState: ...

    def list(self) -> list[AgentState]: ...

    def claim_for_run(self, task_id: UUID) -> AgentState: ...

    def cancel_queued(self, task_id: UUID) -> AgentState: ...

    def close(self) -> None: ...


class TaskQueue(Protocol):
    def enqueue(self, task_id: UUID) -> None: ...

    def dequeue(self, timeout: float) -> UUID | None: ...

    def remove(self, task_id: UUID) -> None: ...

    def close(self) -> None: ...
