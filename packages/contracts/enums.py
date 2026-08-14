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
