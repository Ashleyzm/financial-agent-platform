# 金融多智能体平台

面向金融研究任务的多智能体平台。当前版本为首月框架 `v0.1.0`，目标是建立可运行、可替换、可追踪的基础链路。

## 当前阶段

正在执行 W1：工程骨架与公共契约。

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

## 项目结构

```text
apps/web/                   最小Web界面
services/api/               FastAPI服务
services/worker/            异步任务Worker
packages/contracts/         公共数据契约
packages/agent_runtime/     Agent工作流运行时
packages/financial_data/    金融数据与Provider
tests/                      自动化测试
infra/                      部署与基础设施说明
docs/                       产品、架构与开发文档
```

## 当前限制

- W1阶段使用占位Worker，尚未执行正式Agent流程。
- 尚未接入真实LLM和金融数据。
- 产品仅用于研究与教学，不构成投资建议。

