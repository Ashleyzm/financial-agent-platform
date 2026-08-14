# 金融多智能体平台

面向金融研究任务的多智能体平台。当前版本为首月框架 `v0.1.0`，目标是建立可运行、可替换、可追踪的基础链路。

## 当前阶段

W1-06 已完成：工程骨架、六节点 LangGraph、PostgreSQL 检查点、CI、AkShare 真实行情，以及可替换的 Mock/OpenAI-compatible LLM Provider 已可运行。

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

默认使用不联网的 Mock LLM。需要接入真实模型时，在 `.env` 中设置 `LLM_PROVIDER=openai-compatible`、`LLM_API_KEY`、`LLM_BASE_URL` 和 `LLM_MODEL`，详见 `docs/w1-06-agent-runtime-provider.md`。

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

- 六个 Agent 已通过 API 同步运行；Worker 异步队列将在后续阶段接入。
- 任务列表暂存于 API 内存，LangGraph 运行检查点已写入 PostgreSQL。
- 已接入 A 股、美股和港股真实日线；新闻与财务数据仍为后续阶段，LLM 默认使用 Mock，可按配置切换真实模型。
- Prediction Agent 当前仍使用规则模型，输出只用于验证产品链路。
- 产品仅用于研究与教学，不构成投资建议。
