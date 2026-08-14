# W1-03 最小可运行 Agent 链

本阶段使用确定性的 Mock 数据打通完整业务链路，不调用真实行情、新闻、机器学习模型或 LLM。

## 调用流程

```text
创建任务
  -> 手动运行
  -> Supervisor
  -> Data
  -> Research
  -> Prediction
  -> Risk
  -> Report
  -> 查询统一结果
```

## API

### 创建任务

```http
POST /api/v1/tasks
```

示例请求：

```json
{
  "symbol": "NVDA",
  "market": "US",
  "horizon_days": 5
}
```

### 查询任务

```http
GET /api/v1/tasks/{task_id}
```

任务中心列表：

```http
GET /api/v1/tasks
```

### 运行 Mock Agent 链

```http
POST /api/v1/tasks/{task_id}/run
```

这是 W1-03 的演示入口。W1-04 接入 Redis Worker 后，任务将由 Worker 自动消费。

### 取消排队任务

```http
DELETE /api/v1/tasks/{task_id}
```

当前仅 `queued` 任务允许取消；已执行或失败任务会返回 HTTP 409。

## 当前限制

- 任务保存在 API 进程内存中，服务重启后清空；
- Agent 按同步顺序执行；
- 所有行情、证据、预测和风险都是 Mock 数据；
- 预测结果不能用于实际投资决策。
