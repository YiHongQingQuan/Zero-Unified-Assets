/* LaTeX2Word v0.1 前端逻辑
 * 职责：把文本发去识别、渲染成稿预览、管理每条公式的取舍、导出 docx。
 * 预览用 KaTeX，只是"近似效果"；Word 里看到的是 OMML 原生公式。
 */

const $ = (sel) => document.querySelector(sel);
const API = "";

const DEFAULT_SETTINGS = {
  cn_font: "宋体",
  en_font: "Times New Roman",
  font_size: 12,
  line_spacing: 1.5,
  first_line_indent: 2,
  margin_cm: 2.54,
  paper: "A4",
  limits_mode: "below",
  nary_mode: "auto",
};

const state = {
  doc: null,
  overrides: new Map(), // latex -> accepted
  onlyPending: false,
  settings: { ...DEFAULT_SETTINGS },
  engine: null,
  seq: 0, // 防止旧请求覆盖新结果
};

/* ------------------------------------------------------------ 工具 */

const escapeHtml = (s) =>
  String(s).replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));

function el(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined) textContent(node, text);
  return node;
}

function textContent(node, text) {
  node.appendChild(document.createTextNode(text));
}

let toastTimer = null;
function toast(message, isError = false) {
  const box = $("#toast");
  box.textContent = message;
  box.className = "toast show" + (isError ? " err" : "");
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => (box.className = "toast"), 2800);
}

const debounce = (fn, wait) => {
  let timer = null;
  return (...args) => {
    clearTimeout(timer);
    timer = setTimeout(() => fn(...args), wait);
  };
};

/* ------------------------------------------------------------ 选项 */

function readOptions() {
  return {
    sensitivity: $("#sensitivity").value,
    markdown: $("#markdown").checked,
    line_mode: $("#lineMode").checked,
    ...state.settings,
  };
}

function optionsPayload() {
  const o = readOptions();
  return {
    sensitivity: o.sensitivity,
    markdown: o.markdown,
    line_mode: o.line_mode,
    cn_font: o.cn_font,
    en_font: o.en_font,
    font_size: Number(o.font_size),
    line_spacing: Number(o.line_spacing),
    first_line_indent: Number(o.first_line_indent),
    margin_cm: Number(o.margin_cm),
    paper: o.paper,
    limits_mode: o.limits_mode,
    nary_mode: o.nary_mode,
  };
}

/* ------------------------------------------------------------ 识别 */

async function analyze() {
  const text = $("#source").value;
  const token = ++state.seq;
  updateCharCount();

  if (!text.trim()) {
    state.doc = null;
    renderAll();
    return;
  }

  try {
    const res = await fetch(`${API}/api/analyze`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text, options: readOptions() }),
    });
    if (!res.ok) throw new Error(`识别失败（HTTP ${res.status}）`);
    const data = await res.json();
    if (token !== state.seq) return;
    state.doc = data;
    state.engine = data.engine;
    showEngineWarning(data.engine);
    renderAll();
  } catch (err) {
    if (token !== state.seq) return;
    toast(err.message || "识别失败", true);
  }
}

const analyzeSoon = debounce(analyze, 320);

function showEngineWarning(engine) {
  const box = $("#engineWarning");
  if (engine && engine.available === false) {
    box.textContent = `公式引擎不可用：${engine.error || "未找到 MML2OMML.XSL"}`;
    box.classList.remove("hidden");
  } else {
    box.classList.add("hidden");
  }
}

/* ------------------------------------------------------------ 公式状态 */

const isAccepted = (node) =>
  state.overrides.has(node.latex) ? state.overrides.get(node.latex) : !!node.accepted;

function statusOf(node) {
  if (!isAccepted(node)) {
    return state.overrides.has(node.latex) || node.origin === "explicit"
      ? { key: "off", label: "已忽略" }
      : { key: "pending", label: "待确认" };
  }
  if (node.error) return { key: "err", label: "转换失败" };
  return { key: "ok", label: "已纳入" };
}

function toggle(latex) {
  const node = findNode(latex);
  if (!node) return;
  state.overrides.set(latex, !isAccepted(node));
  renderAll();
}

function findNode(latex) {
  if (!state.doc) return null;
  for (const block of state.doc.blocks) {
    for (const inline of block.inlines || []) {
      if (inline.kind === "math" && inline.latex === latex) return inline;
    }
  }
  return null;
}

function collectMath() {
  const out = [];
  if (!state.doc) return out;
  for (const block of state.doc.blocks) {
    for (const inline of block.inlines || []) {
      if (inline.kind === "math") out.push(inline);
    }
  }
  return out;
}

/* ------------------------------------------------------------ 渲染 */

function renderAll() {
  renderPreview();
  renderList();
  renderStats();
}

function renderPreview() {
  const host = $("#preview");
  host.innerHTML = "";
  if (!state.doc || !state.doc.blocks.length) {
    host.appendChild(el("div", "empty", "左侧粘贴文本后，这里会实时显示成稿效果"));
    return;
  }

  const page = el("div", "paper-inner");
  let idx = 0;

  for (const block of state.doc.blocks) {
    if (block.kind === "table") {
      page.appendChild(renderTable(block));
      continue;
    }
    if (block.kind === "code") {
      const pre = el("pre");
      pre.textContent = (block.inlines || []).map((n) => n.text || "").join("");
      page.appendChild(pre);
      continue;
    }
    if (block.kind === "heading") {
      const h = el("h" + Math.min(block.level || 1, 3));
      appendInlines(h, block, () => ++idx);
      page.appendChild(h);
      continue;
    }
    if (block.kind === "display_math") {
      const div = el("div", "display-math");
      appendInlines(div, block, () => ++idx);
      page.appendChild(div);
      continue;
    }
    const p = el("p", block.kind === "list_item" ? "list-item" : block.kind === "quote" ? "quote" : "");
    if (block.kind === "list_item") p.appendChild(document.createTextNode(block.ordered ? "1. " : "• "));
    appendInlines(p, block, () => ++idx);
    page.appendChild(p);
  }

  host.appendChild(page);
}

function renderTable(block) {
  const table = el("table");
  const rows = block.rows || [];
  rows.forEach((row, ri) => {
    const tr = el("tr");
    const cells = ri === 0 ? row.map((c) => el("th", "", c)) : row.map((c) => el("td", "", c));
    cells.forEach((c) => tr.appendChild(c));
    table.appendChild(tr);
  });
  return table;
}

function appendInlines(host, block, nextIdx) {
  for (const inline of block.inlines || []) {
    if (inline.kind === "text") {
      const parts = String(inline.text || "").split("\n");
      parts.forEach((part, i) => {
        if (i) host.appendChild(document.createElement("br"));
        if (part) host.appendChild(document.createTextNode(part));
      });
      continue;
    }
    host.appendChild(renderMath(inline, nextIdx()));
  }
}

/* 这些运算符的上下限位置受「上下限位置」设置影响（积分不在其中） */
const LIMIT_OPERATORS =
  /(\\(?:limsup|liminf|lim|max|min|sup|inf|det|gcd|Pr|arg|sum|prod|coprod|bigcup|bigcap|bigvee|bigwedge|bigoplus|bigotimes|bigodot))(?=\s*[_^])/g;

function applyLimitsMode(latex, display) {
  const mode = state.settings.limits_mode || "below";
  if (mode === "auto") return latex;
  const forceBelow = mode === "below" && !display;
  const forceSide = mode === "side" && display;
  if (!forceBelow && !forceSide) return latex;
  const tag = forceBelow ? "\\limits" : "\\nolimits";
  return String(latex).replace(LIMIT_OPERATORS, (m) => m + tag);
}

function renderMath(node, index) {
  const accepted = isAccepted(node);
  const status = statusOf(node);
  const span = el("span", "math " + (node.origin === "implicit" ? "implicit " : "") + status.key);
  span.dataset.latex = node.latex;
  span.title = [
    `#${index} ${node.display ? "独立公式" : "行内公式"}`,
    `来源：${node.origin === "explicit" ? "带定界符" : "自动识别"}`,
    node.reasons && node.reasons.length ? `依据：${node.reasons.join("、")}` : "",
    node.error ? `转换失败：${node.error}` : "",
    "点击切换是否纳入",
  ]
    .filter(Boolean)
    .join("\n");

  if (accepted && !node.error) {
    try {
      katex.render(applyLimitsMode(node.latex, !!node.display), span, {
        displayMode: !!node.display,
        throwOnError: true,
        strict: false,
        trust: false,
      });
    } catch (err) {
      span.className += " failed";
      const raw = el("span", "raw", node.raw || node.latex);
      span.appendChild(raw);
    }
  } else {
    span.appendChild(el("span", "raw", node.raw || node.latex));
  }

  const badge = el("span", "idx", String(index));
  span.appendChild(badge);
  span.addEventListener("click", (ev) => {
    ev.stopPropagation();
    toggle(node.latex);
  });
  span.id = `math-i${index}`;
  return span;
}

function renderList() {
  const body = $("#formulaBody");
  const empty = $("#formulaEmpty");
  body.innerHTML = "";
  const items = collectMath();
  $("#formulaSummary").textContent = items.length ? `共 ${items.length} 条` : "";

  let pending = 0;
  items.forEach((node, i) => {
    const status = statusOf(node);
    if (status.key === "pending") pending += 1;
    if (state.onlyPending && status.key !== "pending") return;

    const tr = el("tr");
    tr.appendChild(el("td", "c-idx", String(i + 1)));
    const tdState = el("td", "c-state");
    tdState.appendChild(el("span", "tag " + status.key, status.label));
    tr.appendChild(tdState);
    tr.appendChild(el("td", "c-origin", node.origin === "explicit" ? "定界符" : "识别"));
    tr.appendChild(el("td", "c-type", node.display ? "独立" : "行内"));

    const tdLatex = el("td");
    const code = el("code", "", node.latex || node.raw);
    tdLatex.appendChild(code);
    if (node.error) {
      tdLatex.appendChild(el("div", "hint err", `⚠ ${node.error}`));
    }
    tr.appendChild(tdLatex);

    tr.appendChild(el("td", "c-why", (node.reasons || []).join("、") || "—"));

    const tdOp = el("td", "c-op");
    const btnToggle = el("button", "ghost sm", isAccepted(node) ? "忽略" : "接受");
    btnToggle.type = "button";
    btnToggle.addEventListener("click", (ev) => {
      ev.stopPropagation();
      toggle(node.latex);
    });
    const btnLocate = el("button", "ghost sm icon", "定位");
    btnLocate.type = "button";
    btnLocate.style.marginLeft = "4px";
    btnLocate.addEventListener("click", (ev) => {
      ev.stopPropagation();
      locate(i + 1);
    });
    tdOp.appendChild(btnToggle);
    tdOp.appendChild(btnLocate);
    tr.appendChild(tdOp);

    tr.addEventListener("click", () => locate(i + 1));
    body.appendChild(tr);
  });

  empty.style.display = body.children.length ? "none" : "grid";
  empty.textContent = state.onlyPending && items.length ? "没有待确认的公式" : "还没有识别到公式";
}

function locate(index) {
  const target = document.getElementById(`math-i${index}`);
  if (!target) {
    toast("该公式当前不在预览中（可能已被忽略）");
    return;
  }
  target.scrollIntoView({ block: "center", behavior: "smooth" });
  target.classList.remove("flash");
  void target.offsetWidth;
  target.classList.add("flash");
}

function renderStats() {
  const items = collectMath();
  const accepted = items.filter(isAccepted).length;
  const pending = items.filter((n) => statusOf(n).key === "pending").length;
  const blocks = state.doc ? state.doc.blocks.length : 0;
  const explicit = items.filter((n) => n.origin === "explicit").length;
  const implicit = items.length - explicit;

  $("#statsLine").textContent = items.length
    ? `${blocks} 个段落 · ${items.length} 个公式（定界符 ${explicit} / 识别 ${implicit}）· 纳入 ${accepted}${
        pending ? ` · 待确认 ${pending}` : ""
      }`
    : `${blocks} 个段落 · 未发现公式`;
  $("#formulaSummary").textContent = items.length
    ? `共 ${items.length} 条${pending ? `，待确认 ${pending} 条` : ""}`
    : "";
}

function updateCharCount() {
  const n = $("#source").value.length;
  $("#charCount").textContent = `${n} 字`;
}

/* ------------------------------------------------------------ 导出 */

function serializeDocument() {
  const blocks = (state.doc?.blocks || []).map((block) => ({
    kind: block.kind,
    level: block.level,
    ordered: block.ordered,
    rows: block.rows || [],
    inlines: (block.inlines || []).map((inline) =>
      inline.kind === "math"
        ? {
            kind: "math",
            id: inline.id,
            latex: inline.latex,
            raw: inline.raw,
            display: inline.display,
            origin: inline.origin,
            confidence: inline.confidence,
            accepted: isAccepted(inline),
          }
        : { kind: "text", text: inline.text, bold: inline.bold, italic: inline.italic, code: inline.code }
    ),
  }));
  return { source: "text", blocks };
}

function guessFilename() {
  const items = collectMath();
  const firstBlock = (state.doc?.blocks || []).find((b) => (b.inlines || []).some((i) => i.kind === "text" && i.text.trim()));
  const text = firstBlock
    ? firstBlock.inlines.filter((i) => i.kind === "text").map((i) => i.text).join("").trim()
    : "";
  const base = text.replace(/[\\/:*?"<>|]/g, "").slice(0, 24);
  return (base || `latex2word-${items.length}公式`) + ".docx";
}

async function exportDocx() {
  if (!state.doc || !state.doc.blocks.length) {
    toast("先粘贴一些内容", true);
    return;
  }
  const pending = collectMath().filter((n) => statusOf(n).key === "pending").length;
  if (pending) {
    toast(`还有 ${pending} 条待确认，已按当前状态导出`);
  }

  const btn = $("#btnExport");
  btn.disabled = true;
  btn.textContent = "导出中…";
  try {
    const res = await fetch(`${API}/api/export`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        document: serializeDocument(),
        options: optionsPayload(),
        filename: guessFilename(),
      }),
    });
    if (!res.ok) {
      let detail = `HTTP ${res.status}`;
      try {
        const j = await res.json();
        detail = j.detail || detail;
      } catch (_) {}
      throw new Error(detail);
    }
    const blob = await res.blob();
    const issues = Number(res.headers.get("X-Issues") || 0);
    const name = guessFilename();
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = name;
    document.body.appendChild(a);
    a.click();
    a.remove();
    setTimeout(() => URL.revokeObjectURL(url), 4000);
    toast(issues ? `已导出 ${name}，${issues} 条公式未能转换（已保留原文）` : `已导出 ${name}`);
  } catch (err) {
    toast(err.message || "导出失败", true);
  } finally {
    btn.disabled = false;
    btn.textContent = "导出 Word";
  }
}

/* ------------------------------------------------------------ 设置 */

function loadSettings() {
  try {
    const raw = localStorage.getItem("l2w.settings");
    if (raw) state.settings = { ...DEFAULT_SETTINGS, ...JSON.parse(raw) };
  } catch (_) {}
  syncSettingsForm();
}

function syncSettingsForm() {
  $("#optCnFont").value = state.settings.cn_font;
  $("#optEnFont").value = state.settings.en_font;
  $("#optFontSize").value = state.settings.font_size;
  $("#optLineSpacing").value = state.settings.line_spacing;
  $("#optIndent").value = state.settings.first_line_indent;
  $("#optMargin").value = state.settings.margin_cm;
  $("#optPaper").value = state.settings.paper;
  $("#optLimits").value = state.settings.limits_mode || DEFAULT_SETTINGS.limits_mode;
  $("#optNary").value = state.settings.nary_mode || DEFAULT_SETTINGS.nary_mode;
}

function saveSettings() {
  state.settings = {
    cn_font: $("#optCnFont").value.trim() || DEFAULT_SETTINGS.cn_font,
    en_font: $("#optEnFont").value.trim() || DEFAULT_SETTINGS.en_font,
    font_size: Number($("#optFontSize").value) || DEFAULT_SETTINGS.font_size,
    line_spacing: Number($("#optLineSpacing").value) || DEFAULT_SETTINGS.line_spacing,
    first_line_indent: Number($("#optIndent").value) || 0,
    margin_cm: Number($("#optMargin").value) || DEFAULT_SETTINGS.margin_cm,
    paper: $("#optPaper").value,
    limits_mode: $("#optLimits").value || DEFAULT_SETTINGS.limits_mode,
    nary_mode: $("#optNary").value || DEFAULT_SETTINGS.nary_mode,
  };
  try {
    localStorage.setItem("l2w.settings", JSON.stringify(state.settings));
  } catch (_) {}
  // 上下限位置会影响预览渲染，改完立刻重绘
  renderPreview();
  renderList();
}

/* ------------------------------------------------------------ 运行环境 */

async function loadEnvironment() {
  try {
    const res = await fetch(`${API}/api/environment`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const env = await res.json();
    $("#envPython").textContent = `${env.python.version}（${env.python.bits} 位）`;
    $("#envPath").textContent = env.python.executable;
    if (env.venv.exists) {
      const base = env.base && env.base.version ? `基解释器 ${env.base.version}` : "现有环境";
      $("#envVenv").textContent = `${env.venv.path}（${base}）`;
    } else {
      $("#envVenv").textContent = "尚未创建";
    }
  } catch (err) {
    $("#envPython").textContent = "读取失败";
    $("#envPath").textContent = String(err.message || err);
  }
}

async function switchPython() {
  const btn = $("#btnSwitchPython");
  const original = btn.textContent;
  btn.disabled = true;
  btn.textContent = "请在弹出的窗口里选择…";
  try {
    const res = await fetch(`${API}/api/environment/select`, { method: "POST" });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();
    if (data.cancelled) {
      toast("已取消，未做改动");
      return;
    }
    if (!data.changed) {
      toast("选择没有变化");
      return;
    }
    toast("已切换，正在重启服务…");
    $("#settingsDialog").close();
    showRestartOverlay();
    await fetch(`${API}/api/environment/restart`, { method: "POST" });
    waitForRestart();
  } catch (err) {
    toast(`切换失败：${err.message || err}`, true);
  } finally {
    btn.disabled = false;
    btn.textContent = original;
  }
}

function showRestartOverlay() {
  let box = document.getElementById("restartOverlay");
  if (!box) {
    box = document.createElement("div");
    box.id = "restartOverlay";
    box.className = "restart-overlay";
    box.innerHTML =
      '<div class="restart-card"><strong>正在重启服务…</strong>' +
      "<p>如果 10 秒后页面没有自动恢复，请关闭本页并重新双击 start.cmd。</p></div>";
    document.body.appendChild(box);
  }
  box.style.display = "flex";
}

async function waitForRestart() {
  for (let i = 0; i < 20; i += 1) {
    await new Promise((r) => setTimeout(r, 1000));
    try {
      const res = await fetch(`${API}/api/health`, { cache: "no-store" });
      if (res.ok) {
        location.reload();
        return;
      }
    } catch (_) {
      /* 服务还没起来，继续等 */
    }
  }
  const box = document.getElementById("restartOverlay");
  if (box) {
    box.querySelector("p").textContent = "服务没有自动恢复，请关闭本页并重新双击 start.cmd。";
  }
}

/* ------------------------------------------------------------ 事件绑定 */

const SAMPLE = `质能方程 E=mc² 说明质量与能量等价，当 v→c 时质量趋向无穷。

行内公式 $x^2+y^2=r^2$ 与独立公式：
$$\\int_0^{\\infty} e^{-x^2}\\,dx = \\frac{\\sqrt{\\pi}}{2}$$

设函数 f(x)=x^2+2x+1，当 x>0 时单调递增。设 $\\alpha \\le \\beta$ 且 $\\beta \\neq 0$。

贝叶斯公式：
$$P(A \\mid B) = \\frac{P(B \\mid A)\\,P(A)}{P(B)}$$

行内的极限 $\\lim_{n\\to\\infty} S_n$ 默认也会把下沿标排在下方。

补充说明：版本号 v1.2.3 与售价 $5 到 $10 都不是公式。`;

function loadSample() {
  const area = $("#source");
  area.value = SAMPLE;
  updateCharCount();
  resetScroll(area);
  analyze();
}

function resetScroll(area) {
  area.scrollTop = 0;
  requestAnimationFrame(() => {
    area.scrollTop = 0;
    area.setSelectionRange(0, 0);
  });
}

function bind() {
  $("#source").addEventListener("input", () => {
    updateCharCount();
    analyzeSoon();
  });

  ["#sensitivity", "#markdown", "#lineMode"].forEach((sel) =>
    $(sel).addEventListener("change", () => analyze())
  );

  $("#btnExport").addEventListener("click", exportDocx);
  $("#btnSample").addEventListener("click", loadSample);

  $("#btnAcceptAll").addEventListener("click", () => {
    collectMath().forEach((n) => state.overrides.set(n.latex, true));
    renderAll();
  });

  $("#btnRejectAll").addEventListener("click", () => {
    collectMath().forEach((n) => state.overrides.set(n.latex, false));
    renderAll();
  });

  $("#onlyPending").addEventListener("change", (ev) => {
    state.onlyPending = ev.target.checked;
    renderList();
  });

  $("#btnCollapse").addEventListener("click", () => {
    $("#formulaPanel").classList.toggle("collapsed");
    $("#btnCollapse").textContent = $("#formulaPanel").classList.contains("collapsed") ? "▸" : "▾";
  });

  const dialog = $("#settingsDialog");
  $("#btnSettings").addEventListener("click", () => {
    syncSettingsForm();
    loadEnvironment();
    dialog.showModal();
  });
  $("#btnSwitchPython").addEventListener("click", switchPython);
  $("#btnResetSettings").addEventListener("click", () => {
    state.settings = { ...DEFAULT_SETTINGS };
    syncSettingsForm();
    localStorage.removeItem("l2w.settings");
  });
  dialog.addEventListener("close", () => {
    saveSettings();
    toast("排版设置已保存");
  });

  document.addEventListener("keydown", (ev) => {
    if ((ev.ctrlKey || ev.metaKey) && ev.key === "Enter") {
      ev.preventDefault();
      exportDocx();
    }
  });

  // 拖入 txt
  const area = $("#source");
  ["dragover", "drop"].forEach((type) =>
    area.addEventListener(type, (ev) => {
      ev.preventDefault();
      if (type !== "drop") return;
      const file = ev.dataTransfer.files && ev.dataTransfer.files[0];
      if (!file) return;
      file.text().then((content) => {
        area.value = content;
        updateCharCount();
        resetScroll(area);
        analyze();
      });
    })
  );
}

/* ------------------------------------------------------------ 启动 */

async function boot() {
  loadSettings();
  bind();
  updateCharCount();
  try {
    const res = await fetch(`${API}/api/health`);
    const data = await res.json();
    state.engine = data.engine;
    showEngineWarning(data.engine);
  } catch (_) {
    showEngineWarning({ available: false, error: "无法连接本地服务" });
  }
  if ($("#source").value.trim()) {
    analyze();
  } else if (new URLSearchParams(location.search).has("sample")) {
    loadSample();
  }

  if (new URLSearchParams(location.search).has("settings")) {
    syncSettingsForm();
    loadEnvironment();
    $("#settingsDialog").showModal();

    // 截图/排障用：?settings=1&tip=limits 直接把对应气泡展开
    const wanted = new URLSearchParams(location.search).get("tip");
    if (wanted) {
      const el = document.querySelector(`.help[data-key="${wanted}"]`);
      if (el) el.classList.add("force-tip");
    }
  }
}

boot();
