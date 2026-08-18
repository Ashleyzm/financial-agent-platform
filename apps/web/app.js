const API_BASE = "/api/v1/tasks";
const TERMINAL_STATUSES = new Set(["succeeded", "failed", "cancelled"]);

const agentLabels = {
  supervisor: "总控 Agent",
  data: "数据 Agent",
  research: "研究 Agent",
  prediction: "预测 Agent",
  risk: "风险 Agent",
  report: "报告 Agent",
};

const statusLabels = {
  queued: "排队中",
  pending: "等待中",
  running: "执行中",
  succeeded: "已完成",
  failed: "失败",
  cancelled: "已取消",
  skipped: "已跳过",
};

const directionLabels = { bullish: "偏多", neutral: "中性", bearish: "偏空" };
const riskLabels = { high: "高风险", medium: "中风险", low: "低风险" };
const confidenceLabels = { high: "高置信度", medium: "中等置信度", low: "低置信度" };
const evidenceLabels = { market: "行情", financial: "财务", news: "新闻", filing: "公告", research: "研究" };

const elements = {
  form: document.querySelector("#task-form"),
  submit: document.querySelector("#submit-button"),
  market: document.querySelector("#market"),
  currencyHint: document.querySelector("#currency-hint"),
  servicePill: document.querySelector("#service-pill"),
  serviceText: document.querySelector("#service-text"),
  taskList: document.querySelector("#task-list"),
  refresh: document.querySelector("#refresh-button"),
  empty: document.querySelector("#empty-state"),
  dashboard: document.querySelector("#task-dashboard"),
  loading: document.querySelector("#loading-banner"),
  error: document.querySelector("#error-banner"),
  report: document.querySelector("#report-area"),
  timeline: document.querySelector("#timeline"),
  toast: document.querySelector("#toast"),
};

let activeTaskId = null;
let pollTimer = null;

function escapeHTML(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

async function api(path = "", options = {}) {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json", ...(options.headers || {}) },
    ...options,
  });
  const payload = await response.json().catch(() => ({}));
  if (!response.ok) {
    const detail = payload.error?.message
      || (typeof payload.detail === "string" ? payload.detail : "请求失败，请稍后重试");
    throw new Error(detail);
  }
  return payload;
}

async function checkService() {
  try {
    const response = await fetch("/api/health");
    if (!response.ok) throw new Error("offline");
    const data = await response.json();
    elements.servicePill.className = "service-pill online";
    elements.serviceText.textContent = `服务正常 · ${data.version}`;
  } catch {
    elements.servicePill.className = "service-pill offline";
    elements.serviceText.textContent = "API 未连接";
  }
}

function showToast(message) {
  elements.toast.textContent = message;
  elements.toast.classList.add("show");
  window.setTimeout(() => elements.toast.classList.remove("show"), 2200);
}

function setBusy(busy) {
  elements.submit.disabled = busy;
  elements.submit.querySelector("span:first-child").textContent = busy ? "正在提交任务..." : "启动多 Agent 研究";
}

function formatTime(value) {
  if (!value) return "—";
  return new Intl.DateTimeFormat("zh-CN", { month: "2-digit", day: "2-digit", hour: "2-digit", minute: "2-digit" }).format(new Date(value));
}

function formatPercent(value, signed = false) {
  if (value === null || value === undefined) return "—";
  const number = Number(value) * 100;
  return `${signed && number > 0 ? "+" : ""}${number.toFixed(1)}%`;
}

function shortId(value) {
  return value ? `${value.slice(0, 8)}…${value.slice(-4)}` : "—";
}

function renderTaskList(tasks) {
  if (!tasks.length) {
    elements.taskList.innerHTML = '<p class="muted-message">还没有研究任务。</p>';
    return;
  }
  elements.taskList.innerHTML = tasks.slice(0, 8).map((task) => `
    <button class="task-list-item ${task.task_id === activeTaskId ? "active" : ""}" data-task-id="${escapeHTML(task.task_id)}" type="button">
      <strong>${escapeHTML(task.request.symbol)} · ${escapeHTML(task.request.market)}</strong>
      <span class="mini-status status-${escapeHTML(task.status)}">${statusLabels[task.status] || task.status}</span>
      <small>${formatTime(task.created_at)} · ${task.request.horizon_days} 日预测</small>
    </button>
  `).join("");
  elements.taskList.querySelectorAll("[data-task-id]").forEach((button) => {
    button.addEventListener("click", () => loadTask(button.dataset.taskId));
  });
}

async function loadTasks() {
  try {
    renderTaskList(await api());
  } catch (error) {
    elements.taskList.innerHTML = `<p class="muted-message">${escapeHTML(error.message)}</p>`;
  }
}

function renderTimeline(timeline = []) {
  const completed = timeline.filter((step) => step.status === "succeeded").length;
  document.querySelector("#timeline-progress").textContent = `${completed} / ${timeline.length || 6} 完成`;
  elements.timeline.innerHTML = timeline.map((step, index) => `
    <div class="timeline-step ${escapeHTML(step.status)}">
      <span class="step-dot">${step.status === "succeeded" ? "✓" : String(index + 1).padStart(2, "0")}</span>
      <strong>${escapeHTML(agentLabels[step.agent] || step.agent)}</strong>
      <small>${escapeHTML(step.module_code || "AGT-01")} · ${step.duration_ms === null ? statusLabels[step.status] || step.status : `${step.duration_ms} ms`}</small>
    </div>
  `).join("");
}

function renderEvidence(evidence = []) {
  document.querySelector("#evidence-count").textContent = `${evidence.length} 条证据`;
  document.querySelector("#evidence-list").innerHTML = evidence.length ? evidence.map((item) => `
    <div class="evidence-item">
      <span class="evidence-type">${escapeHTML(evidenceLabels[item.evidence_type] || item.evidence_type)}</span>
      <div><h3>${escapeHTML(item.title)}</h3><p>${escapeHTML(item.excerpt)}</p></div>
      <div class="evidence-source"><strong>${escapeHTML(item.source)}</strong><span>相关度 ${Math.round(item.relevance * 100)}%</span></div>
    </div>
  `).join("") : '<p class="muted-message">暂无证据。</p>';
}

function renderReport(report, modelUsage = {}) {
  if (!report) {
    elements.report.classList.add("hidden");
    return;
  }
  const prediction = report.prediction;
  const risk = report.risk;
  const direction = document.querySelector("#direction-value");
  direction.textContent = directionLabels[prediction.direction] || prediction.direction;
  direction.className = `value-${prediction.direction}`;
  document.querySelector("#probability-value").textContent = formatPercent(prediction.upward_probability);
  document.querySelector("#return-value").textContent = formatPercent(prediction.expected_return, true);
  document.querySelector("#risk-value").textContent = riskLabels[risk.level] || risk.level;
  document.querySelector("#risk-value").className = `risk-${risk.level}`;
  const usageText = modelUsage.provider
    ? `${modelUsage.provider} · ${Number(modelUsage.total_tokens || 0)} tokens`
    : prediction.model_name;
  document.querySelector("#model-name").textContent = usageText;
  document.querySelector("#horizon-note").textContent = `未来 ${prediction.horizon_days} 个交易日`;
  document.querySelector("#confidence-note").textContent = confidenceLabels[risk.confidence] || risk.confidence;
  document.querySelector("#research-summary").textContent = report.research_summary;
  document.querySelector("#risk-factors").innerHTML = risk.factors.map((factor) => `<li>${escapeHTML(factor)}</li>`).join("");
  document.querySelector("#disclaimer").textContent = report.disclaimer;
  renderEvidence(report.evidence);
  elements.report.classList.remove("hidden");
}

function renderTask(task) {
  activeTaskId = task.task_id;
  elements.empty.classList.add("hidden");
  elements.dashboard.classList.remove("hidden");
  document.querySelector("#detail-market").textContent = task.request.market;
  document.querySelector("#detail-symbol").textContent = task.request.symbol;
  document.querySelector("#detail-question").textContent = task.request.question;
  const status = document.querySelector("#detail-status");
  status.textContent = statusLabels[task.status] || task.status;
  status.className = `status-badge status-${task.status}`;
  const taskId = document.querySelector("#task-id");
  taskId.textContent = shortId(task.task_id);
  taskId.dataset.fullId = task.task_id;
  elements.error.classList.toggle("hidden", !task.error);
  elements.error.textContent = task.error
    ? `${task.error.module_code || "PLT-03"} · ${agentLabels[task.error.agent] || "任务"}：${task.error.message}`
    : "";
  renderTimeline(task.timeline);
  renderReport(task.report, task.model_usage);
  elements.loading.classList.toggle("hidden", TERMINAL_STATUSES.has(task.status));
  if (!TERMINAL_STATUSES.has(task.status)) {
    const loadingTitle = elements.loading.querySelector("strong");
    const loadingText = elements.loading.querySelector("p");
    loadingTitle.textContent = task.status === "queued" ? "任务正在排队" : "Agent 团队正在研究";
    loadingText.textContent = task.status === "queued"
      ? "Worker 将自动领取任务，无需手动运行。"
      : "页面每 2 秒自动更新节点进度。";
  }
  loadTasks();
}

async function loadTask(taskId) {
  clearTimeout(pollTimer);
  try {
    const task = await api(`/${taskId}`);
    renderTask(task);
    if (!TERMINAL_STATUSES.has(task.status)) {
      pollTimer = window.setTimeout(() => loadTask(taskId), 2000);
    }
  } catch (error) {
    showToast(error.message);
  }
}

async function createTask(event) {
  event.preventDefault();
  clearTimeout(pollTimer);
  const form = new FormData(elements.form);
  const payload = {
    symbol: String(form.get("symbol")).trim().toUpperCase(),
    market: form.get("market"),
    horizon_days: Number(form.get("horizon_days")),
    question: String(form.get("question")).trim(),
    include_news: document.querySelector("#include-news").checked,
    include_financials: document.querySelector("#include-financials").checked,
  };
  setBusy(true);
  elements.error.classList.add("hidden");
  try {
    const created = await api("", { method: "POST", body: JSON.stringify(payload) });
    activeTaskId = created.task_id;
    await loadTask(created.task_id);
    showToast("任务已进入异步队列");
  } catch (error) {
    elements.error.textContent = error.message;
    elements.error.classList.remove("hidden");
    showToast(error.message);
  } finally {
    setBusy(false);
    await loadTasks();
  }
}

elements.form.addEventListener("submit", createTask);
elements.refresh.addEventListener("click", loadTasks);
elements.market.addEventListener("change", () => { elements.currencyHint.textContent = elements.market.value; });
document.querySelector("#symbol").addEventListener("input", (event) => { event.target.value = event.target.value.toUpperCase(); });
document.querySelector("#task-id").addEventListener("click", async (event) => {
  if (!event.currentTarget.dataset.fullId) return;
  await navigator.clipboard.writeText(event.currentTarget.dataset.fullId).catch(() => {});
  showToast("任务编号已复制");
});

checkService();
loadTasks();
