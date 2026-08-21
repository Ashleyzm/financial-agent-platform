# F0 接手与运行手册

本手册用于让未参与实现的成员在 30 分钟内独立启动、验证和停止 FinAgent Platform。所有命令均从仓库根目录执行；默认使用 Mock Provider，不需要付费 API Key。

## 1. 前置条件

- 安装 Git 与 Docker Desktop（Windows）或 Docker Engine + Compose（Linux/macOS）。
- Docker 已启动，当前用户可以执行 `docker info`。
- 仅在运行本地质量检查时需要 Python 3.12 或 3.13。

## 2. 一键启动

Windows：

```powershell
scripts\start.cmd
```

Linux/macOS：

```bash
./scripts/start.sh
```

脚本会在缺少 `.env` 时从 `.env.example` 创建本地配置，构建五个服务，并等待 PostgreSQL、Redis、API、Worker 和 Web 全部健康。不要提交 `.env`。

## 3. 接手验收

打开 Web 控制台 <http://localhost:3000>，创建一条 NVDA / US / 5 天任务，确认任务最终为 `succeeded`，且时间线有六个成功节点。

运行完整 F0 验收：

```powershell
python scripts/verify_f0.py --docker
```

输出必须同时包含：

- `status: passed`
- `sample-market` 与 `sample-llm`
- `module_code: AGT-03`
- `error_code: llm_timeout`
- 五个 `healthy_services`
- Docker E2E 的 `status: succeeded`

单独复现 Provider 替换与失败路由：

```powershell
python scripts/provider_replacement_demo.py
python scripts/failure_demo.py
```

## 4. 一键停止与恢复

Windows：

```powershell
scripts\stop.cmd
```

Linux/macOS：

```bash
./scripts/stop.sh
```

停止脚本保留命名数据卷。再次执行启动脚本即可恢复服务。需要清空本地数据时，由负责人确认后再执行 `docker compose down -v`。

## 5. 故障定位

| 现象 | 先查 | 责任模块 |
|---|---|---|
| API、队列、数据库或部署异常 | `docker compose ps`、`docker compose logs api worker` | PLT |
| Agent 或模型调用失败 | 任务 `trace_id`、时间线错误、原始 Provider 响应 | AGT |
| 行情、事件、产业数据异常 | Provider、来源、时间点与质量标记 | FIN |
| 页面、内容或流程使用问题 | Web 控制台、UAT 记录与内容版本 | OPS |

错误必须保留 `task_id`、`trace_id`、`module_code`、错误码、可重试标志和复现步骤。先按模块码定位，再交给唯一主责；统筹角色负责协调，不替代模块 Owner 的根因说明。

## 6. 接手记录模板

| 字段 | 填写内容 |
|---|---|
| 验收人 | 姓名或账号 |
| 日期和时区 | ISO 时间 |
| 机器与系统 | 操作系统、Docker 版本 |
| Git SHA | `git rev-parse HEAD` |
| 启动结果 | 五服务是否 healthy |
| Provider 演练 | `sample-market` / `sample-llm` 是否出现 |
| 失败演练 | `AGT-03` / `llm_timeout` / `retryable=true` 是否出现 |
| Web E2E | 任务 ID、最终状态 |
| 停止/恢复 | 是否通过 |
| 阻塞与结论 | 通过或阻塞说明 |

本次项目验收记录见 `docs/acceptance/f0-08-acceptance.md`。
