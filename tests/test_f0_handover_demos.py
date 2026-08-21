from scripts.failure_demo import run_demo as run_failure_demo
from scripts.provider_replacement_demo import run_demo as run_provider_demo


def test_provider_replacement_demo_uses_both_sample_providers() -> None:
    result = run_provider_demo()

    assert result["status"] == "passed"
    assert result["market_provider"] == "sample-market"
    assert result["llm_provider"] == "sample-llm"


def test_failure_demo_returns_owner_routable_timeout() -> None:
    result = run_failure_demo()

    assert result["status"] == "passed"
    assert result["module_code"] == "AGT-03"
    assert result["error_code"] == "llm_timeout"
    assert result["retryable"] is True
