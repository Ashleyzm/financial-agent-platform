# ADR-001：首月平台运行时与异步边界

- 状态：已接受
- 日期：2026-08-17
- 决策人：研发 A；研发 B/C 评审

## 决策

首月采用 Python、FastAPI、LangGraph、PostgreSQL、Redis 和 Docker Compose。API 只创建、查询和取消任务；Worker 消费 Redis 队列并执行 Graph。跨模块数据只通过 `packages/contracts` 传递。

金融数据和模型都必须通过 Provider 注入。默认 Mock，AkShare 与 OpenAI-compatible 作为可替换示例。节点完成后立即保存任务状态，LangGraph 使用 PostgreSQL checkpoint。

## 原因

三人团队使用 Monorepo 可以降低版本协调成本；异步边界可避免长任务阻塞 API；默认 Mock 能避免外部网络和 API Key 阻塞框架验收。

## 约束

- 不接真实券商或自动交易。
- `main` 只通过 Pull Request 更新。
- 公共契约变更必须有测试和兼容说明。
- 日志必须携带 `task_id`、`trace_id` 和 `module_code`。
