# W2/W3 集成与验收说明

## 已完成链路

```text
Web -> FastAPI -> PostgreSQL/Redis -> Worker -> LangGraph
    -> per-node persistence/checkpoint -> Report -> Web polling
```

## Provider 配置

- `MARKET_DATA_PROVIDER=mock|akshare`
- `LLM_PROVIDER=mock|openai-compatible`
- OpenAI-compatible 模式还需配置 `LLM_API_KEY`、`LLM_BASE_URL` 和 `LLM_MODEL`。

API 与 Worker 使用相同配置创建 Provider。Mock 模式不联网，适合本地开发、CI 和课堂演示。

## 追踪与错误

- 每个任务具有 `task_id` 和 `trace_id`。
- 每个时间线节点具有 `module_code`。
- 节点开始、成功和失败日志包含三类定位字段。
- API 错误统一返回 `{"error": {code, message, module_code, trace_id, ...}}`。

## 验收

```powershell
python -m ruff check .
python -m ruff format --check .
python -m pytest -q
docker compose up -d --build --wait
python tests/e2e_smoke.py
```

E2E 冒烟任务必须由 Worker 自动领取，不调用调试接口 `/run`；最终状态应为 `succeeded`，六个节点均成功并生成结构化报告。
