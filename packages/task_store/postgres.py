"""PostgreSQL-backed task store."""

from uuid import UUID

from psycopg.types.json import Jsonb
from psycopg_pool import ConnectionPool

from packages.agent_runtime.state import AgentState
from packages.contracts import TaskStatus, utc_now
from packages.task_store.base import (
    InvalidTaskTransitionError,
    TaskNotFoundError,
)
from packages.task_store.serialization import state_from_dict, state_to_dict


class PostgresTaskStore:
    def __init__(self, dsn: str, *, pool: ConnectionPool | None = None) -> None:
        self._pool = pool or ConnectionPool(
            dsn,
            min_size=1,
            max_size=5,
            open=True,
        )
        self._ensure_schema()

    def save(self, state: AgentState) -> None:
        payload = state_to_dict(state)
        with self._pool.connection() as conn:
            conn.execute(
                """
                INSERT INTO tasks (
                    task_id, trace_id, status, payload, created_at, updated_at
                )
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (task_id) DO UPDATE SET
                    trace_id = EXCLUDED.trace_id,
                    status = EXCLUDED.status,
                    payload = EXCLUDED.payload,
                    updated_at = EXCLUDED.updated_at
                """,
                (
                    state["task_id"],
                    state["trace_id"],
                    state["status"].value,
                    Jsonb(payload),
                    state["created_at"],
                    state["updated_at"],
                ),
            )

    def get(self, task_id: UUID) -> AgentState:
        with self._pool.connection() as conn:
            row = conn.execute(
                "SELECT payload FROM tasks WHERE task_id = %s",
                (task_id,),
            ).fetchone()
        if row is None:
            raise TaskNotFoundError(str(task_id))
        return state_from_dict(row[0])

    def list(self) -> list[AgentState]:
        with self._pool.connection() as conn:
            rows = conn.execute("SELECT payload FROM tasks ORDER BY created_at DESC").fetchall()
        return [state_from_dict(row[0]) for row in rows]

    def claim_for_run(self, task_id: UUID) -> AgentState:
        now = utc_now()
        with self._pool.connection() as conn:
            row = conn.execute(
                """
                UPDATE tasks
                SET status = %s, updated_at = %s
                WHERE task_id = %s AND status = %s
                RETURNING payload
                """,
                (
                    TaskStatus.RUNNING.value,
                    now,
                    task_id,
                    TaskStatus.QUEUED.value,
                ),
            ).fetchone()
            if row is None:
                existing = conn.execute(
                    "SELECT status FROM tasks WHERE task_id = %s",
                    (task_id,),
                ).fetchone()
                if existing is None:
                    raise TaskNotFoundError(str(task_id))
                raise InvalidTaskTransitionError(
                    f"task status {existing[0]} does not allow execution"
                )

        state = state_from_dict(row[0])
        state["status"] = TaskStatus.RUNNING
        state["updated_at"] = now
        return state

    def cancel_queued(self, task_id: UUID) -> AgentState:
        now = utc_now()
        with self._pool.connection() as conn:
            row = conn.execute(
                """
                UPDATE tasks
                SET status = %s, updated_at = %s
                WHERE task_id = %s AND status = %s
                RETURNING payload
                """,
                (
                    TaskStatus.CANCELLED.value,
                    now,
                    task_id,
                    TaskStatus.QUEUED.value,
                ),
            ).fetchone()
            if row is None:
                existing = conn.execute(
                    "SELECT status FROM tasks WHERE task_id = %s",
                    (task_id,),
                ).fetchone()
                if existing is None:
                    raise TaskNotFoundError(str(task_id))
                if existing[0] == TaskStatus.CANCELLED.value:
                    payload = conn.execute(
                        "SELECT payload FROM tasks WHERE task_id = %s",
                        (task_id,),
                    ).fetchone()[0]
                    return state_from_dict(payload)
                raise InvalidTaskTransitionError(
                    f"task status {existing[0]} does not allow cancellation"
                )

        state = state_from_dict(row[0])
        state["status"] = TaskStatus.CANCELLED
        state["current_agent"] = None
        state["updated_at"] = now
        return state

    def close(self) -> None:
        self._pool.close()

    def _ensure_schema(self) -> None:
        with self._pool.connection() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS tasks (
                    task_id UUID PRIMARY KEY,
                    trace_id UUID NOT NULL,
                    status TEXT NOT NULL,
                    payload JSONB NOT NULL,
                    created_at TIMESTAMPTZ NOT NULL,
                    updated_at TIMESTAMPTZ NOT NULL
                )
                """
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_tasks_created_at ON tasks (created_at DESC)"
            )
            conn.execute("CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks (status)")
