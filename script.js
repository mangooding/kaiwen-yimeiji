const API_BASE = window.location.protocol === "file:" ? "http://127.0.0.1:8891" : "";
const PAGE_SIZE = 24;

const state = {
  q: "",
  source: "",
  category: "",
  language: "",
  flag: "",
  offset: 0,
  total: 0,
  loading: false
};

const grid = document.querySelector("#template-grid");
const searchInput = document.querySelector("#prompt-search");
const resultCount = document.querySelector("#result-count");
const emptyState = document.querySelector("#empty-state");
const toast = document.querySelector("#toast");
const categoryTabs = document.querySelector("#category-tabs");
const quickButtons = document.querySelectorAll("[data-filter]");
const apiStatus = document.querySelector("#api-status");
const sourceFilter = document.querySelector("#source-filter");
const languageFilter = document.querySelector("#language-filter");
const flagFilter = document.querySelector("#flag-filter");
const loadMoreButton = document.querySelector("#load-more");
let toastTimer = null;
let searchTimer = null;
const promptCache = new Map();

const sourceAccent = {
  youmind: "#246bfe",
  zerolu: "#ff5a52",
  anil: "#00a7a0",
  evolink: "#f0a400"
};

function iconCopy() {
  return '<svg aria-hidden="true" viewBox="0 0 24 24"><path d="M8 8h10v12H8z"/><path d="M6 16H4V4h12v2"/></svg>';
}

function iconExternal() {
  return '<svg aria-hidden="true" viewBox="0 0 24 24"><path d="M7 17 17 7"/><path d="M9 7h8v8"/><path d="M5 5v14h14"/></svg>';
}

function escapeHtml(value = "") {
  return value
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function getTagStyle(sourceSlug) {
  const color = sourceAccent[sourceSlug] || "#246bfe";
  return `--tag-color: ${color}; --tag-bg: ${color}14;`;
}

async function fetchJson(path) {
  const response = await fetch(`${API_BASE}${path}`);
  if (!response.ok) {
    throw new Error(`HTTP ${response.status}`);
  }
  return response.json();
}

function buildQuery(extra = {}) {
  const params = new URLSearchParams({
    q: state.q,
    source: state.source,
    category: state.category,
    language: state.language,
    flag: state.flag,
    offset: String(state.offset),
    limit: String(PAGE_SIZE),
    ...extra
  });
  [...params.entries()].forEach(([key, value]) => {
    if (!value) params.delete(key);
  });
  return params.toString();
}

async function loadFacets() {
  const facets = await fetchJson("/api/facets");
  apiStatus.textContent = `本地 API 已连接：${facets.total.toLocaleString("zh-CN")} 条提示词`;
  resultCount.textContent = facets.total;

  Object.entries(facets.sources || {}).forEach(([slug, source]) => {
    const option = document.createElement("option");
    option.value = slug;
    option.textContent = `${source.name} (${source.records})`;
    sourceFilter.appendChild(option);

    const count = document.querySelector(`[data-source-count="${slug}"]`);
    if (count) count.textContent = `${source.records} 条`;
  });

  Object.entries(facets.languages || {}).forEach(([language, count]) => {
    const option = document.createElement("option");
    option.value = language;
    option.textContent = `${language} (${count})`;
    languageFilter.appendChild(option);
  });

  const categories = Object.entries(facets.categories || {}).sort((a, b) => b[1] - a[1]);
  categoryTabs.innerHTML =
    '<button class="active" type="button" data-category="">全部</button>' +
    categories
      .map(([category, count]) => {
        return `<button type="button" data-category="${escapeHtml(category)}">${escapeHtml(category)} <span>${count}</span></button>`;
      })
      .join("");
}

async function searchPrompts({ append = false } = {}) {
  if (state.loading) return;
  state.loading = true;
  loadMoreButton.disabled = true;
  if (!append) {
    state.offset = 0;
    grid.innerHTML = '<p class="loading-state">正在检索本地提示词库...</p>';
  }

  try {
    const data = await fetchJson(`/api/search?${buildQuery()}`);
    state.total = data.total;
    resultCount.textContent = data.total;
    apiStatus.textContent = `本地 API 已连接：${data.total.toLocaleString("zh-CN")} 条结果，用时 ${data.elapsedMs}ms`;

    if (!append) grid.innerHTML = "";
    data.items.forEach((item) => promptCache.set(item.id, item));
    grid.insertAdjacentHTML("beforeend", data.items.map(renderPromptCard).join(""));
    emptyState.hidden = data.total !== 0;
    loadMoreButton.hidden = state.offset + data.items.length >= data.total;
    state.offset += data.items.length;
  } catch (error) {
    grid.innerHTML = renderApiOffline(error);
    resultCount.textContent = "0";
    emptyState.hidden = true;
    loadMoreButton.hidden = true;
    apiStatus.textContent = "本地 API 未启动：请运行 python server.py";
  } finally {
    state.loading = false;
    loadMoreButton.disabled = false;
  }
}

function renderPromptCard(item) {
  const flags = (item.flags || [])
    .slice(0, 3)
    .map((flag) => `<span>${formatFlag(flag)}</span>`)
    .join("");
  const image = item.image
    ? `<img class="prompt-image" src="${escapeHtml(item.image)}" alt="${escapeHtml(item.title)} 预览图" loading="lazy" referrerpolicy="no-referrer" />`
    : "";
  return `
    <article class="template-card prompt-card" data-prompt-id="${escapeHtml(item.id)}">
      ${image}
      <div class="template-head">
        <span class="template-tag" style="${getTagStyle(item.sourceSlug)}">${escapeHtml(item.category || "综合")}</span>
        <span class="language-chip">${escapeHtml(item.language || "en")}</span>
      </div>
      <h3>${escapeHtml(item.title || "Untitled Prompt")}</h3>
      <p class="prompt-meta">${escapeHtml(item.source)} · ${escapeHtml(item.sourceFile || "")}</p>
      <div class="prompt-preview">${escapeHtml(item.promptPreview || item.prompt || "")}</div>
      <div class="flag-row">${flags}</div>
      <div class="card-actions">
        <a class="source-link" href="${escapeHtml(item.sourceUrl || item.sourceRepo)}" target="_blank" rel="noreferrer">
          ${iconExternal()} 来源
        </a>
        <button class="copy-button" type="button" data-copy-prompt="${escapeHtml(item.id)}">
          ${iconCopy()} 复制
        </button>
      </div>
    </article>
  `;
}

function renderApiOffline(error) {
  return `
    <div class="offline-panel">
      <h3>后台还没启动</h3>
      <p>本地检索需要运行 Python 后端。打开 PowerShell 后在项目目录执行：</p>
      <pre><code>python server.py</code></pre>
      <p>然后访问 <strong>http://127.0.0.1:8891</strong>。当前错误：${escapeHtml(error.message)}</p>
    </div>
  `;
}

function formatFlag(flag) {
  const labels = {
    requires_reference: "参考图",
    has_text: "文字",
    api_ready: "API",
    celebrity_or_public_figure: "公众人物",
    sensitive_style: "敏感"
  };
  return labels[flag] || flag;
}

async function copyText(text) {
  try {
    await navigator.clipboard.writeText(text);
  } catch {
    const textarea = document.createElement("textarea");
    textarea.value = text;
    document.body.appendChild(textarea);
    textarea.select();
    document.execCommand("copy");
    textarea.remove();
  }
  showToast("已复制提示词");
}

function showToast(message) {
  toast.textContent = message;
  toast.classList.add("show");
  clearTimeout(toastTimer);
  toastTimer = window.setTimeout(() => {
    toast.classList.remove("show");
  }, 1600);
}

function scheduleSearch() {
  clearTimeout(searchTimer);
  searchTimer = window.setTimeout(() => searchPrompts(), 180);
}

searchInput.addEventListener("input", () => {
  state.q = searchInput.value.trim();
  scheduleSearch();
});

document.querySelector("[data-clear-search]").addEventListener("click", () => {
  searchInput.value = "";
  state.q = "";
  searchInput.focus();
  searchPrompts();
});

quickButtons.forEach((button) => {
  button.addEventListener("click", () => {
    searchInput.value = button.dataset.filter;
    state.q = button.dataset.filter;
    searchInput.focus();
    searchPrompts();
  });
});

categoryTabs.addEventListener("click", (event) => {
  const button = event.target.closest("[data-category]");
  if (!button) return;
  state.category = button.dataset.category || "";
  categoryTabs.querySelectorAll("button").forEach((item) => item.classList.toggle("active", item === button));
  searchPrompts();
});

sourceFilter.addEventListener("change", () => {
  state.source = sourceFilter.value;
  searchPrompts();
});

languageFilter.addEventListener("change", () => {
  state.language = languageFilter.value;
  searchPrompts();
});

flagFilter.addEventListener("change", () => {
  state.flag = flagFilter.value;
  searchPrompts();
});

loadMoreButton.addEventListener("click", () => searchPrompts({ append: true }));

grid.addEventListener("click", (event) => {
  const button = event.target.closest("[data-copy-prompt]");
  if (!button) return;
  const item = promptCache.get(button.dataset.copyPrompt);
  if (!item) return;
  copyText(item.prompt);
});

async function init() {
  try {
    await loadFacets();
  } catch (error) {
    grid.innerHTML = renderApiOffline(error);
    apiStatus.textContent = "本地 API 未启动：请运行 python server.py";
    return;
  }
  await searchPrompts();
}

init();
