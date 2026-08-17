# 架构基线 v0.1

```text
Web -> API -> Redis -> Worker -> Agent Runtime -> PostgreSQL
```

## 模块边界

- `apps/web`：仅负责用户交互与结果展示。
- `services/api`：负责输入校验、任务接口和查询接口。
- `services/worker`：负责消费异步任务并调用 Agent Runtime。
- `packages/contracts`：定义跨模块公共数据结构。
- `packages/agent_runtime`：定义工作流状态、节点和执行逻辑。
- `packages/model_provider`：定义统一 LLM 请求/响应、Mock 与 OpenAI-compatible Provider，并负责结构化输出校验。
- `packages/financial_data`：定义金融数据与 Evidence Provider。

Research Agent 通过依赖注入使用 `LLMProvider`。默认 Mock 模式不访问网络；生产环境显式切换 `LLM_PROVIDER=openai-compatible`，模型调用失败、超时和结构化输出错误会写入 Agent 时间线。

公共数据结构将在 W1-02 冻结为 `v0.1`。
