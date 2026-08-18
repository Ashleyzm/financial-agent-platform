from langgraph.checkpoint.memory import InMemorySaver

from packages.agent_runtime import LangGraphWorkflowRunner, create_initial_state, run_research_agent
from packages.contracts import AgentName, AgentStatus, EvidenceType, ForecastRequest, TaskStatus
from packages.model_provider import LLMTimeoutError, MockLLMProvider


def test_research_agent_merges_structured_output_into_state() -> None:
    state = create_initial_state(ForecastRequest(symbol="NVDA"))
    provider = MockLLMProvider(
        response={
            "summary": "芯片需求仍是主要研究变量。",
            "thesis": "需要结合估值与后续财报验证。",
            "catalysts": ["下一季度财报"],
            "risks": ["估值波动"],
            "confidence": 0.62,
            "evidence": [
                {
                    "title": "结构化研究记录",
                    "source": "mock-llm",
                    "excerpt": "此记录用于验证 Research Agent 输出映射。",
                    "relevance": 0.8,
                }
            ],
        }
    )

    run_research_agent(state, provider)

    assert state["research_summary"].startswith("芯片需求")
    assert state["evidence"][0].evidence_type is EvidenceType.RESEARCH
    assert state["evidence"][0].metadata["agent"] == "research"


def test_langgraph_uses_injected_research_provider() -> None:
    runner = LangGraphWorkflowRunner(InMemorySaver(), llm_provider=MockLLMProvider())
    state = create_initial_state(ForecastRequest(symbol="NVDA"))

    result = runner(state)

    assert result["status"] is TaskStatus.SUCCEEDED
    assert "Mock Research Agent" in result["research_summary"]
    assert any(item.source == "mock-llm" for item in result["evidence"])
    assert result["model_usage"].provider == "mock"
    assert result["model_usage"].total_tokens == 0


def test_research_timeout_is_traceable_and_retryable() -> None:
    provider = MockLLMProvider(fail_with=LLMTimeoutError("provider timed out"))
    runner = LangGraphWorkflowRunner(InMemorySaver(), llm_provider=provider)

    result = runner(create_initial_state(ForecastRequest(symbol="NVDA")))
    research_step = next(step for step in result["timeline"] if step.agent is AgentName.RESEARCH)

    assert result["status"] is TaskStatus.FAILED
    assert research_step.status is AgentStatus.FAILED
    assert research_step.error is not None
    assert research_step.error.code == "llm_timeout"
    assert research_step.error.module_code == "AGT-03"
    assert research_step.error.retryable is True
