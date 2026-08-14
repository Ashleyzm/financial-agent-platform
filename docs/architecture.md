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
- `packages/financial_data`：定义金融数据与 Evidence Provider。

公共数据结构将在 W1-02 冻结为 `v0.1`。

