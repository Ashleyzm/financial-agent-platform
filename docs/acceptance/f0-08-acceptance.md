# F0-08 接手验收记录

本记录由未参与原功能开发的自动化执行者从远端 `main` 的干净副本完成。团队备份成员可按同一手册补签人工复验；自动化结果不得替代后续真实用户反馈。

| 字段 | 记录 |
|---|---|
| 验收范围 | 一键启动/停止、五服务健康、Provider 替换、结构化失败、Web E2E、发布材料 |
| 候选分支 | `fix/f0-08-closeout` |
| 基线 Git SHA | `2797895784793c72e7155773e941ba85f7b91d83`；最终候选以远端分支头为准 |
| 验收时间 | `2026-08-19T16:00:47+08:00` |
| 验收环境 | Windows 11 10.0.26200；Docker 29.7.2；Compose 5.3.1；Python 3.13.15 |
| 独立执行者 | Codex 自动化执行；非原功能实现副本 |
| 技术结论 | 通过；F0 工程门禁 8/8 |
| 人工复验 | 团队备份成员可补签，不阻塞已通过的自动化工程门禁 |

## 必须通过的证据

- `scripts/start.cmd` 或 `scripts/start.sh` 从仓库根目录启动成功。
- `python scripts/verify_f0.py --docker` 返回 `status=passed`。
- Provider 演练输出 `sample-market` 与 `sample-llm`。
- 失败演练输出 `AGT-03`、`llm_timeout`、`retryable=true`。
- 五服务均为 healthy，异步 E2E 返回 succeeded。
- 停止后可再次启动，命名数据卷默认保留。
- `docs/releases/v0.1.0.md`、Git 标签和 GitHub Release 一致。

## 2026-08-19 实测结果

| 检查 | 结果 | 证据摘要 |
|---|---|---|
| 一键停止 | 通过 | 五容器与网络正常移除；命名数据卷保留 |
| 一键启动 | 通过 | `scripts/start.cmd` 从停止状态构建并等待五服务 healthy |
| 代码质量 | 通过 | `ruff check .`、`ruff format --check .` |
| 单元/契约测试 | 通过 | 44 passed；仅有上游 Starlette 弃用警告 |
| Shell 语法 | 通过 | Alpine 3.21 中 `sh -n scripts/start.sh scripts/stop.sh` |
| Provider 替换 | 通过 | `market_provider=sample-market`，`llm_provider=sample-llm` |
| 结构化失败 | 通过 | `module_code=AGT-03`，`error_code=llm_timeout`，`retryable=true` |
| Docker E2E | 通过 | 任务 `6b73518b-59bc-474d-87db-28778182bcff` 最终 `succeeded` |
| 停止后恢复 | 通过 | 停止后重新执行一键启动，五服务恢复 healthy |

最终发布前还需完成：远端分支 CI 通过、合入 `main`、推送 `v0.1.0` 标签并创建同名 GitHub Release。完成后本记录中的技术结论保持不变，发布证据以远端 Release 为准。
