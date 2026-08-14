const API = "/api/v1/tasks";
const terminalStatuses = new Set(["succeeded", "failed", "cancelled"]);
const agentLabels = {
  supervisor: "总控规划",
  data: "行情数据",
  research: "研究分析",
  prediction: "走势预测",
  risk: "风险审核",
  report: "报告生成",
};
const statusLabels = {
  queued: "排队中",
  running: "执行中",
  succeeded: "已完成",
  failed: "失败",
  cancelled: "已取消",
  pending: "等待",
};
const directionLabels = { bullish: "偏多", neutral: "中性", bearish: "偏空" };
const riskLabels = { low: "低风险", medium: "中风险", high: "高风险" };
const confidenceLabels = { low: "低", medium: "中", high: "高" };

const $ = (selector) => document.querySelector(selector);
const percent = (value, digits = 1) => value == null ? "—" : `${(value * 100).toFixed(digits)}%`;
const dateTime = (value) => value ? new Intl.DateTimeFormat("zh-CN", { dateStyle: "medium", timeStyle: "short" }).format(new Date(value)) : "—";
const escapeHtml = (value) => String(value ?? "").replace(/[&<>'"]/g, (character) => ({
  "&": "&amp;", "<": "&lt;", ">": "&gt;", "'": "&#39;", '"': "&quot;",
})[character]);

async function request(url, options = {}) {
  const response = await fetch(url, { headers: { "Content-Type": "application/json", ...(options.headers || {}) }, ...options });
  if (!response.ok) {
    const payload = await response.json().catch(() => ({}));
    const detail = Array.isArray(payload.detail)
      ? payload.detail.map((item) => item.msg).join("；")
      : payload.detail || `请求失败 (${response.status})`;
    throw new Error(detail);
  }
  return response.json();
}

async function checkApi() {
  const state = $("#api-state");
  try {
    const health = await request("/api/health");
    state.className = "api-state online";
    state.innerHTML = `<span></span>API 在线 · v${health.version}`;
  } catch {
    state.className = "api-state offline";
    state.innerHTML = "<span></span>API 未连接";
  }
}

function showToast(message) {
  const toast = $("#toast");
  toast.textContent = message;
  toast.classList.add("show");
  window.setTimeout(() => toast.classList.remove("show"), 2600);
}

function setSubmitting(active) {
  const button = $("#submit-button");
  button.disabled = active;
  button.querySelector("span").textContent = active ? "Agent 团队正在研究…" : "启动多智能体研究";
}

function renderTimeline(timeline = []) {
  $("#timeline").innerHTML = timeline.map((step, index) => {
    const icon = step.status === "succeeded" ? "✓" : step.status === "failed" ? "!" : String(index + 1).padStart(2, "0");
    const detail = step.duration_ms != null ? `${step.duration_ms} ms` : statusLabels[step.status] || step.status;
    return `<div class="agent-step ${step.status}">
      <span class="agent-icon">${icon}</span>
      <strong>${escapeHtml(agentLabels[step.agent] || step.agent)}</strong>
      <small>${escapeHtml(detail)}</small>
    </div>`;
  }).join("");
  const complete = timeline.filter((step) => step.status === "succeeded").length;
  $("#timeline-summary").textContent = `${complete} / ${timeline.length || 6} 完成`;
}

function renderReport(report) {
  const prediction = report.prediction;
  const risk = report.risk;
  $("#report-grid").classList.remove("hidden");
  $("#direction").textContent = directionLabels[prediction.direction] || prediction.direction;
  $("#probability").textContent = percent(prediction.upward_probability);
  $("#probability-meter").style.width = percent(prediction.upward_probability, 0);
  $("#expected-return").textContent = percent(prediction.expected_return);
  $("#forecast-horizon").textContent = `${prediction.horizon_days} 日`;
  $("#model-name").textContent = prediction.model_name;
  $("#risk-level").textContent = riskLabels[risk.level] || risk.level;
  $("#confidence").textContent = `置信度 ${confidenceLabels[risk.confidence] || risk.confidence}`;
  $("#volatility").textContent = percent(risk.volatility);
  $("#drawdown").textContent = percent(risk.max_drawdown);
  $("#risk-factors").innerHTML = risk.factors.map((factor) => `<li>${escapeHtml(factor)}</li>`).join("");
  $("#research-summary").textContent = report.research_summary;
  $("#evidence-list").innerHTML = report.evidence.map((item) => `<div class="evidence-item">
    <div class="evidence-top"><strong>${escapeHtml(item.title)}</strong><span class="source-tag">${escapeHtml(item.source)}</span></div>
    <p>${escapeHtml(item.excerpt)}</p>
  </div>`).join("") || '<div class="empty-small">暂无证据</div>';
}

function renderTask(task, scroll = false) {
  $("#result-section").classList.remove("hidden");
  $("#result-symbol").textContent = task.request.symbol;
  $("#task-meta").textContent = `Task ${task.task_id} · Trace ${task.trace_id} · ${dateTime(task.updated_at)}`;
  const status = $("#task-status");
  status.className = `status-pill ${task.status}`;
  status.textContent = statusLabels[task.status] || task.status;
  renderTimeline(task.timeline);

  const errorCard = $("#error-card");
  if (task.error) {
    errorCard.classList.remove("hidden");
    $("#error-message").textContent = task.error.message;
  } else {
    errorCard.classList.add("hidden");
  }
  if (task.report) renderReport(task.report);
  else $("#report-grid").classList.add("hidden");
  if (scroll) $("#result-section").scrollIntoView({ behavior: "smooth", block: "start" });
}

async function pollTask(taskId) {
  for (let attempt = 0; attempt < 45; attempt += 1) {
    const task = await request(`${API}/${taskId}`);
    renderTask(task);
    if (terminalStatuses.has(task.status)) return task;
    await new Promise((resolve) => window.setTimeout(resolve, 2000));
  }
  throw new Error("任务执行时间较长，请稍后在最近任务中查看");
}

async function createAndRunTask(event) {
  event.preventDefault();
  setSubmitting(true);
  try {
    const payload = {
      symbol: $("#symbol").value.trim().toUpperCase(),
      market: $("#market").value,
      horizon_days: Number($("#horizon").value),
      question: $("#question").value.trim(),
      include_news: true,
      include_financials: true,
    };
    const created = await request(API, { method: "POST", body: JSON.stringify(payload) });
    const queued = await request(`${API}/${created.task_id}`);
    renderTask(queued, true);
    const result = await request(`${API}/${created.task_id}/run`, { method: "POST", body: "{}" });
    renderTask(result);
    if (!terminalStatuses.has(result.status)) await pollTask(created.task_id);
    showToast(result.status === "succeeded" ? "研究报告已生成" : "任务已结束，请查看状态");
    await loadRecentTasks();
  } catch (error) {
    showToast(error.message);
  } finally {
    setSubmitting(false);
  }
}

async function loadRecentTasks() {
  const list = $("#recent-list");
  try {
    const tasks = await request(API);
    list.innerHTML = tasks.slice(0, 6).map((task) => `<button class="recent-item" data-task-id="${task.task_id}">
      <span><strong>${escapeHtml(task.request.symbol)} · ${escapeHtml(task.request.market)}</strong><small>${escapeHtml(dateTime(task.created_at))}</small></span>
      <i class="mini-status ${escapeHtml(task.status)}">${escapeHtml(statusLabels[task.status] || task.status)}</i>
    </button>`).join("") || '<div class="empty-small">暂无任务记录</div>';
  } catch {
    list.innerHTML = '<div class="empty-small">任务列表暂不可用</div>';
  }
}

$("#task-form").addEventListener("submit", createAndRunTask);
$("#refresh-tasks").addEventListener("click", loadRecentTasks);
$("#recent-list").addEventListener("click", async (event) => {
  const item = event.target.closest("[data-task-id]");
  if (!item) return;
  try { renderTask(await request(`${API}/${item.dataset.taskId}`), true); }
  catch (error) { showToast(error.message); }
});
document.querySelectorAll("[data-symbol]").forEach((button) => button.addEventListener("click", () => {
  $("#symbol").value = button.dataset.symbol;
  $("#market").value = button.dataset.market;
}));

checkApi();
loadRecentTasks();
