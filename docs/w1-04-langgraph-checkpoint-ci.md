# W1-04：LangGraph、PostgreSQL 检查点与 CI

## 本阶段交付

- 六个 Agent 由 LangGraph `StateGraph` 依次调度。
- 每个任务使用 `task_id` 作为 LangGraph `thread_id`，任务状态互不混淆。
- API 启动时自动连接 PostgreSQL，并由 `PostgresSaver.setup()` 创建检查点表。
- 本地单元测试使用 `InMemorySaver`，不依赖 Docker，执行更快。
- GitHub Actions 在提交和 PR 时自动执行 Ruff 与 Pytest。

## 运行方式

```powershell
Copy-Item .env.example .env
docker compose up -d --build
```

创建并执行任务后，可查看 PostgreSQL 中的检查点数量：

```powershell
docker compose exec postgres psql -U financial_agents -d financial_agents -c "select count(*) from checkpoints;"
```

## 当前边界

本阶段持久化的是 Agent 图运行检查点。任务列表仍保存在 API 进程内存中，API 重启后列表会清空；任务表持久化将在后续阶段完成。预测与研究内容目前仍是可重复的 Mock 数据，不构成投资建议。
