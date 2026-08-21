"""Produce a stable, owner-routable Agent failure without external services."""

from __future__ import annotations

import json
import logging

from langgraph.checkpoint.memory import InMemorySaver

from packages.agent_runtime import LangGraphWorkflowRunner, create_initial_state
from packages.contracts import AgentName, AgentStatus, ForecastRequest, TaskStatus
from packages.model_provider import LLMTimeoutError, MockLLMProvider


def run_demo() -> dict[str, object]:
    provider = MockLLMProvider(
        fail_with=LLMTimeoutError("simulated provider timeout for F0 handover")
    )
    runner = LangGraphWorkflowRunner(InMemorySaver(), llm_provider=provider)
    logging.disable(logging.CRITICAL)
    try:
        result = runner(create_initial_state(ForecastRequest(symbol="NVDA")))
    finally:
        logging.disable(logging.NOTSET)
    research_step = next(step for step in result["timeline"] if step.agent is AgentName.RESEARCH)
    error = research_step.error

    assert result["status"] is TaskStatus.FAILED
    assert research_step.status is AgentStatus.FAILED
    assert error is not None
    assert error.code == "llm_timeout"
    assert error.module_code == "AGT-03"
    assert error.retryable is True
    return {
        "gate": "F0-08",
        "status": "passed",
        "task_status": result["status"].value,
        "agent": research_step.agent.value,
        "module_code": error.module_code,
        "error_code": error.code,
        "retryable": error.retryable,
    }


def main() -> None:
    print(json.dumps(run_demo(), ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
