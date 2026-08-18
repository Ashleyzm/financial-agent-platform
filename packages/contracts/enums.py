"""Shared enum values for the v0.1 public contract."""

from enum import StrEnum


class Market(StrEnum):
    US = "US"
    CN = "CN"
    HK = "HK"


class TaskStatus(StrEnum):
    QUEUED = "queued"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"


class AgentName(StrEnum):
    SUPERVISOR = "supervisor"
    DATA = "data"
    RESEARCH = "research"
    PREDICTION = "prediction"
    RISK = "risk"
    REPORT = "report"


AGENT_MODULE_CODES: dict[AgentName, str] = {
    AgentName.SUPERVISOR: "AGT-01",
    AgentName.DATA: "FIN-02",
    AgentName.RESEARCH: "AGT-03",
    AgentName.PREDICTION: "AGT-03",
    AgentName.RISK: "AGT-03",
    AgentName.REPORT: "FIN-06",
}


def module_code_for_agent(agent: AgentName) -> str:
    """Return the stable owner-routing code for an Agent node."""

    return AGENT_MODULE_CODES[agent]


class AgentStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    SKIPPED = "skipped"


class EvidenceType(StrEnum):
    MARKET = "market"
    FINANCIAL = "financial"
    NEWS = "news"
    FILING = "filing"
    RESEARCH = "research"


class ForecastDirection(StrEnum):
    BULLISH = "bullish"
    NEUTRAL = "neutral"
    BEARISH = "bearish"


class RiskLevel(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class ConfidenceLevel(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
