"""In-memory task lifecycle service for the W1-03 runnable demo."""

from copy import deepcopy
from threading import RLock
from uuid import UUID

from packages.agent_runtime import (
    AgentState,
    WorkflowRunner,
    create_in_memory_runner,
    create_initial_state,
)
from packages.contracts import (
    CancelTaskResponse,
    ForecastRequest,
    TaskDetail,
    TaskReference,
    TaskStatus,
    utc_now,
)


class TaskNotFoundError(LookupError):
    pass


class InvalidTaskTransitionError(RuntimeError):
    pass


class InMemoryTaskStore:
    """Thread-safe temporary store; PostgreSQL replaces it in a later milestone."""

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
                self._states.values(), key=lambda state: state["created_at"], reverse=True
            )
            return deepcopy(states)

    def claim_for_run(self, task_id: UUID) -> AgentState:
        with self._lock:
            state = self._get_existing(task_id)
            if state["status"] is not TaskStatus.QUEUED:
                raise InvalidTaskTransitionError(
                    f"任务状态 {state['status']} 不允许执行，只有 queued 任务可以执行"
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
                    f"任务状态 {state['status']} 不允许取消，只有 queued 任务可以取消"
                )
            state["status"] = TaskStatus.CANCELLED
            state["current_agent"] = None
            state["updated_at"] = utc_now()
            return deepcopy(state)

    def _get_existing(self, task_id: UUID) -> AgentState:
        state = self._states.get(task_id)
        if state is None:
            raise TaskNotFoundError(str(task_id))
        return state

    def clear(self) -> None:
        with self._lock:
            self._states.clear()


class TaskService:
    def __init__(
        self,
        store: InMemoryTaskStore | None = None,
        runner: WorkflowRunner | None = None,
    ) -> None:
        self.store = store or InMemoryTaskStore()
        self.runner = runner or create_in_memory_runner()

    def set_runner(self, runner: WorkflowRunner) -> None:
        self.runner = runner

    def create(self, request: ForecastRequest) -> TaskReference:
        state = create_initial_state(request)
        self.store.save(state)
        return _to_reference(state)

    def get(self, task_id: UUID) -> TaskDetail:
        return _to_detail(self.store.get(task_id))

    def list(self) -> list[TaskDetail]:
        return [_to_detail(state) for state in self.store.list()]

    def run(self, task_id: UUID) -> TaskDetail:
        state = self.store.claim_for_run(task_id)
        state = self.runner(state)
        self.store.save(state)
        return _to_detail(state)

    def cancel(self, task_id: UUID) -> CancelTaskResponse:
        state = self.store.cancel_queued(task_id)
        return CancelTaskResponse(task_id=task_id, cancelled_at=state["updated_at"])


def _to_reference(state: AgentState) -> TaskReference:
    return TaskReference(
        task_id=state["task_id"],
        trace_id=state["trace_id"],
        status=state["status"],
        created_at=state["created_at"],
    )


def _to_detail(state: AgentState) -> TaskDetail:
    return TaskDetail(
        task_id=state["task_id"],
        trace_id=state["trace_id"],
        status=state["status"],
        created_at=state["created_at"],
        request=state["request"],
        updated_at=state["updated_at"],
        timeline=state["timeline"],
        report=state["report"],
        error=state["errors"][-1] if state["errors"] else None,
    )


task_service = TaskService()
