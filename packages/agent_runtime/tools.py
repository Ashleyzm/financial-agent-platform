"""Minimal versioned Tool protocol used by Agent Runtime extensions."""

from typing import Any, Protocol
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ToolContext(BaseModel):
    model_config = ConfigDict(extra="forbid")

    task_id: UUID
    trace_id: UUID
    module_code: str = Field(pattern=r"^[A-Z]{3}-\d{2}$")


class ToolResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    data: dict[str, Any] = Field(default_factory=dict)
    source: str = Field(min_length=1, max_length=120)
    metadata: dict[str, Any] = Field(default_factory=dict)


class AgentTool(Protocol):
    name: str
    version: str

    def invoke(self, arguments: dict[str, Any], context: ToolContext) -> ToolResult: ...


class ToolRegistry:
    """Small deterministic registry; duplicate names require an explicit version change."""

    def __init__(self) -> None:
        self._tools: dict[str, AgentTool] = {}

    def register(self, tool: AgentTool) -> None:
        key = f"{tool.name}@{tool.version}"
        if key in self._tools:
            raise ValueError(f"Tool 已注册: {key}")
        self._tools[key] = tool

    def get(self, name: str, version: str) -> AgentTool:
        key = f"{name}@{version}"
        try:
            return self._tools[key]
        except KeyError as exc:
            raise KeyError(f"Tool 不存在: {key}") from exc

    def list(self) -> list[str]:
        return sorted(self._tools)
