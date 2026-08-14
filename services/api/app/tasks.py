"""Task lifecycle HTTP endpoints."""

from uuid import UUID

from fastapi import APIRouter, HTTPException, status

from packages.contracts import CancelTaskResponse, ForecastRequest, TaskDetail, TaskReference
from packages.task_store import InvalidTaskTransitionError, TaskNotFoundError
from services.api.app.task_service import task_service

router = APIRouter(prefix="/api/v1/tasks", tags=["tasks"])


@router.post("", response_model=TaskReference, status_code=status.HTTP_202_ACCEPTED)
def create_task(request: ForecastRequest) -> TaskReference:
    return task_service.create(request)


@router.get("", response_model=list[TaskDetail])
def list_tasks() -> list[TaskDetail]:
    return task_service.list()


@router.get("/{task_id}", response_model=TaskDetail)
def get_task(task_id: UUID) -> TaskDetail:
    try:
        return task_service.get(task_id)
    except TaskNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="任务不存在") from exc


@router.post("/{task_id}/run", response_model=TaskDetail)
def run_task(task_id: UUID) -> TaskDetail:
    try:
        return task_service.run(task_id)
    except TaskNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="任务不存在") from exc
    except InvalidTaskTransitionError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc


@router.delete("/{task_id}", response_model=CancelTaskResponse)
def cancel_task(task_id: UUID) -> CancelTaskResponse:
    try:
        return task_service.cancel(task_id)
    except TaskNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="任务不存在") from exc
    except InvalidTaskTransitionError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
