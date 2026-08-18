# 金融多智能体平台

面向金融研究任务的多智能体平台。当前版本为首月框架 `v0.1.0`，目标是建立可运行、可替换、可追踪的基础链路。

## 当前阶段

W2/W3 集成链路已完成：任务由 API 写入 PostgreSQL 和 Redis，Worker 自动消费并按节点执行 LangGraph；节点状态、错误、`task_id`、`trace_id`、`module_code` 和模型用量可由 Web 轮询查看。

首月目标链路：

```text
Web -> FastAPI -> Redis/Worker -> LangGraph -> PostgreSQL -> 研究报告
```

## 环境要求

- Git
- Python 3.12（本地开发）
- Docker Desktop（推荐用于统一运行环境）
- VS Code（可选）

不需要独立安装 PostgreSQL 和 Redis，它们由 Docker Compose 启动。

## 第一次启动

1. 复制环境变量文件：

   ```powershell
   Copy-Item .env.example .env
   ```

2. 启动全部服务：

   ```powershell
   docker compose up --build
   ```

3. 验证服务：

   - Web：http://localhost:3000
   - API健康检查：http://localhost:8000/health
   - API文档：http://localhost:8000/docs

4. 停止服务：

   ```powershell
   docker compose down
   ```

默认使用不联网的 Mock Data 与 Mock LLM，保证学生团队没有外部 Key 也能稳定演示。需要真实行情时设置 `MARKET_DATA_PROVIDER=akshare`；需要兼容模型时设置 `LLM_PROVIDER=openai-compatible`、`LLM_API_KEY`、`LLM_BASE_URL` 和 `LLM_MODEL`。

## 项目结构

```text
apps/web/                   最小Web界面
services/api/               FastAPI服务
services/worker/            异步任务Worker
packages/contracts/         公共数据契约
packages/agent_runtime/     Agent工作流运行时
packages/model_provider/    统一 LLM Provider 与结构化输出
packages/financial_data/    金融数据与Provider
tests/                      自动化测试
infra/                      部署与基础设施说明
docs/                       产品、架构与开发文档
```

## 当前限制

- API、Redis、Worker、LangGraph 和 PostgreSQL 已打通；`POST /run` 仅保留给调试和测试，Web 使用异步队列。
- 任务、节点时间线和报告持久化到 PostgreSQL；LangGraph checkpoint 同样使用 PostgreSQL。
- 已提供 Mock 与 AkShare 行情模式；新闻与财务数据仍为后续阶段。
- 已提供 Mock 与 OpenAI-compatible LLM；当前只有 Research Agent 使用 LLM。
- Prediction Agent 当前仍使用规则模型，输出只用于验证产品链路。
- 产品仅用于研究与教学，不构成投资建议。
