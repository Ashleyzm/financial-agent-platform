"""Task lifecycle service shared by the API and worker."""

from uuid import UUID

from packages.agent_runtime import (
    WorkflowRunner,
    create_in_memory_runner,
    create_initial_state,
)
from packages.contracts import (
    CancelTaskResponse,
    ForecastRequest,
    TaskDetail,
    TaskReference,
)
from packages.task_store import (
    InMemoryTaskQueue,
    InMemoryTaskStore,
    InvalidTaskTransitionError,
    TaskNotFoundError,
    TaskQueue,
    TaskStore,
)


class TaskService:
    def __init__(
        self,
        store: TaskStore | None = None,
        queue: TaskQueue | None = None,
        runner: WorkflowRunner | None = None,
    ) -> None:
        self.store = store or InMemoryTaskStore()
        self.queue = queue or InMemoryTaskQueue()
        self.runner = runner or create_in_memory_runner()

    def set_runner(self, runner: WorkflowRunner) -> None:
        self.runner = runner

    def configure(self, store: TaskStore, queue: TaskQueue) -> None:
        self.store = store
        self.queue = queue

    def create(self, request: ForecastRequest) -> TaskReference:
        state = create_initial_state(request)
        self.store.save(state)
        self.queue.enqueue(state["task_id"])
        return _to_reference(state)

    def get(self, task_id: UUID) -> TaskDetail:
        return _to_detail(self.store.get(task_id))

    def list(self) -> list[TaskDetail]:
        return [_to_detail(state) for state in self.store.list()]

    def run(self, task_id: UUID) -> TaskDetail:
        self.queue.remove(task_id)
        state = self.store.claim_for_run(task_id)
        state = self.runner(state)
        self.store.save(state)
        return _to_detail(state)

    def cancel(self, task_id: UUID) -> CancelTaskResponse:
        state = self.store.cancel_queued(task_id)
        self.queue.remove(task_id)
        return CancelTaskResponse(task_id=task_id, cancelled_at=state["updated_at"])


def _to_reference(state) -> TaskReference:
    return TaskReference(
        task_id=state["task_id"],
        trace_id=state["trace_id"],
        status=state["status"],
        created_at=state["created_at"],
    )


def _to_detail(state) -> TaskDetail:
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
