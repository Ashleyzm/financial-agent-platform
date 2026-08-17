# W1-06 Agent Runtime 与统一 LLM Provider

本阶段为开发人员 B 的可运行最小实现，保持 `main` 的六节点 LangGraph 链路不变，同时把 Research Agent 的模型调用替换为可注入 Provider。

## Provider 选择

默认 `LLM_PROVIDER=mock`，不访问网络，适合本地开发、CI 和接口联调。真实模型使用 OpenAI-compatible Chat Completions 协议，因此可以连接 OpenAI、vLLM、Ollama 网关或兼容的云厂商：

```dotenv
LLM_PROVIDER=openai-compatible
LLM_API_KEY=替换为实际密钥
LLM_BASE_URL=https://api.openai.com/v1
LLM_MODEL=gpt-4o-mini
LLM_TIMEOUT_SECONDS=30
LLM_MAX_RETRIES=2
```

Provider 统一返回 `LLMResponse`，Research Agent 通过 `ResearchOutput` Pydantic Schema 校验 JSON。超时会产生 `llm_timeout` 且标记为可重试；HTTP/服务错误产生统一 Provider 错误；结构化 JSON 不合法会产生 `llm_structured_output_invalid`。

## 本地验证

```powershell
pip install -e ".[dev]"
pytest -q tests/test_model_provider.py tests/test_research_agent.py
```

不设置 API Key 也可以运行 Mock 模式。真实模型只在显式设置 `LLM_PROVIDER=openai-compatible` 后调用。
