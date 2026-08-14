# 公共数据契约 v0.1

W1-02 冻结 API、Worker、Agent 和 Web 共同使用的数据结构。目标不是一次定义所有金融字段，而是先保证任务可创建、过程可追踪、错误可定位、结果可解释。

## 1. 任务输入

`ForecastRequest` 记录：

- 股票代码与市场；
- 预测周期，当前允许 1–30 天；
- 用户问题；
- 是否包含新闻和财务信息。

股票代码会自动去除首尾空格并转为大写。未知字段会被拒绝，避免前后端悄悄使用不同结构。

## 2. 任务与追踪

每个任务同时拥有：

- `task_id`：业务任务编号；
- `trace_id`：一次完整执行链路编号；
- `status`：queued、running、succeeded、failed 或 cancelled；
- `timeline`：各 Agent 的状态、耗时、摘要和错误。

## 3. AgentState

`AgentState` 是节点之间传递的唯一状态对象。它包括原始请求、当前 Agent、市场快照、研究证据、预测、风险、最终报告和错误列表。

`create_initial_state()` 为每个任务创建独立列表，防止多个并发任务共享数据。该结构不依赖 LangGraph，W1-04 可以直接将它接入图工作流。

## 4. 统一结果

最终 `ForecastReport` 固定包含：

- `prediction`：方向、上涨概率、预期收益和模型名；
- `research_summary`：研究结论；
- `evidence`：来源、链接、摘要和相关度；
- `risk`：风险等级、置信度和风险因素；
- `disclaimer`：研究教学用途声明。

## 5. 代码位置

```text
packages/contracts/enums.py       枚举值
packages/contracts/models.py      Pydantic 输入输出模型
packages/agent_runtime/state.py   AgentState 与初始化函数
tests/test_contracts.py           字段校验与序列化测试
tests/test_agent_state.py         状态完整性和隔离测试
```
