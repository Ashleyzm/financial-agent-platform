from langgraph.checkpoint.memory import InMemorySaver

from packages.agent_runtime import LangGraphWorkflowRunner, create_initial_state
from packages.contracts import AgentStatus, ForecastRequest, TaskStatus


def test_langgraph_runs_all_nodes_and_creates_checkpoints() -> None:
    checkpointer = InMemorySaver()
    runner = LangGraphWorkflowRunner(checkpointer)
    initial = create_initial_state(ForecastRequest(symbol="NVDA"))

    result = runner(initial)
    config = {"configurable": {"thread_id": str(initial["task_id"])}}
    saved = runner.graph.get_state(config)
    history = list(runner.graph.get_state_history(config))

    assert result["status"] is TaskStatus.SUCCEEDED
    assert all(step.status is AgentStatus.SUCCEEDED for step in result["timeline"])
    assert saved.values["task_id"] == initial["task_id"]
    assert saved.values["report"] is not None
    assert len(history) >= 7


def test_langgraph_uses_task_id_as_isolated_thread() -> None:
    checkpointer = InMemorySaver()
    runner = LangGraphWorkflowRunner(checkpointer)
    first = create_initial_state(ForecastRequest(symbol="NVDA"))
    second = create_initial_state(ForecastRequest(symbol="AAPL"))

    runner(first)
    runner(second)

    first_config = {"configurable": {"thread_id": str(first["task_id"])}}
    second_config = {"configurable": {"thread_id": str(second["task_id"])}}
    assert runner.graph.get_state(first_config).values["request"].symbol == "NVDA"
    assert runner.graph.get_state(second_config).values["request"].symbol == "AAPL"
