# W1-B 技术风控 Agent 与三因子融合

本分支实现负责人/研发 B 的 W1 交付：`M1-B01` 和 `M1-B02`。代码不依赖外部 LLM，也不直接接入生产任务链，便于 A/C 在契约冻结后接入。

## 交付范围

- `packages/contracts/risk.py`：RiskDecision v0.2、技术风控输入/输出、人工复核状态
- `packages/agent_runtime/risk_engine.py`：技术风险 Agent（AGT-03）和三因子融合（AGT-06）
- `tests/test_risk_engine.py`：固定输入、降级、硬否决、缺失因子归一化、冲突复核和边界校验

## 规则口径

技术风险得分由趋势、回撤、波动、流动性、数据质量五个子因子按 `0.30/0.25/0.25/0.10/0.10` 加权。三因子融合使用技术/事件/产业 `0.45/0.30/0.25` 权重；缺失因子会重新归一化，不能伪造为 0。

硬否决先于加权：技术风险 `>=90`、事件风险 `>=80` 或产业风险 `>=80` 时直接输出 `stage_avoid`，并进入人工复核。任意已提供因子之间相差 `>=40` 分时标记冲突并要求复核。

这些规则只输出研究和风险辅助结论，不构成投资建议、仓位指令或交易指令。

## 本地验收

```text
pytest -q tests/test_risk_engine.py
ruff check packages/contracts/risk.py packages/agent_runtime/risk_engine.py tests/test_risk_engine.py
```

待 A/C 完成公共 API、行情特征和 Web 映射后，再由 D 组织端到端集成；B 负责解释规则和黄金用例，根因仍按 `AGT-03/AGT-06` 路由。
