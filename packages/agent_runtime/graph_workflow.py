"""LangGraph orchestration for the six-agent financial workflow."""

from collections.abc import Callable
from typing import Any, Protocol, cast

from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph

from packages.agent_runtime.mock_workflow import WORKFLOW, run_mock_node
from packages.agent_runtime.state import AgentState
from packages.contracts import AgentName, TaskStatus


class WorkflowRunner(Protocol):
    def __call__(self, state: AgentState) -> AgentState: ...


def _node_for(agent: AgentName) -> Callable[[AgentState], AgentState]:
    def run(state: AgentState) -> AgentState:
        return run_mock_node(state, agent)

    return run


def _next_after(agent: AgentName) -> Callable[[AgentState], str]:
    agents = [item[0] for item in WORKFLOW]
    index = agents.index(agent)
    next_node = END if index == len(agents) - 1 else agents[index + 1].value

    def route(state: AgentState) -> str:
        return END if state["status"] is TaskStatus.FAILED else next_node

    return route


def build_workflow(checkpointer: BaseCheckpointSaver[Any] | None = None):
    """Compile the deterministic nodes as a checkpointable LangGraph graph."""

    builder = StateGraph(AgentState)
    agents = [agent for agent, _ in WORKFLOW]
    for agent in agents:
        builder.add_node(agent.value, _node_for(agent))
    builder.add_edge(START, agents[0].value)
    for index, agent in enumerate(agents):
        next_nodes = {END: END}
        route = _next_after(agent)
        if index < len(agents) - 1:
            next_name = agents[index + 1].value
            next_nodes[next_name] = next_name
        builder.add_conditional_edges(agent.value, route, next_nodes)
    return builder.compile(checkpointer=checkpointer)


class LangGraphWorkflowRunner:
    """Invoke one isolated LangGraph thread per financial task."""

    def __init__(self, checkpointer: BaseCheckpointSaver[Any] | None = None) -> None:
        self.graph = build_workflow(checkpointer)

    def __call__(self, state: AgentState) -> AgentState:
        config = {"configurable": {"thread_id": str(state["task_id"])}}
        result = self.graph.invoke(state, config=config)
        return cast(AgentState, result)


def create_in_memory_runner() -> LangGraphWorkflowRunner:
    return LangGraphWorkflowRunner(InMemorySaver())
