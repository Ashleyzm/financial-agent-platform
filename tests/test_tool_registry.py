from uuid import uuid4

import pytest

from packages.agent_runtime import ToolContext, ToolRegistry, ToolResult


class EchoTool:
    name = "echo"
    version = "0.1"

    def invoke(self, arguments, context: ToolContext) -> ToolResult:
        return ToolResult(
            data=arguments,
            source=self.name,
            metadata={"trace_id": str(context.trace_id)},
        )


def test_tool_registry_registers_versioned_tool() -> None:
    registry = ToolRegistry()
    tool = EchoTool()
    registry.register(tool)
    context = ToolContext(task_id=uuid4(), trace_id=uuid4(), module_code="AGT-02")

    result = registry.get("echo", "0.1").invoke({"value": 42}, context)

    assert registry.list() == ["echo@0.1"]
    assert result.data == {"value": 42}


def test_tool_registry_rejects_duplicate_version() -> None:
    registry = ToolRegistry()
    registry.register(EchoTool())

    with pytest.raises(ValueError, match="Tool 已注册"):
        registry.register(EchoTool())
