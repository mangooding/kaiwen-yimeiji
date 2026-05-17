# 开文伊美姬

<p align="center">
  <strong>一个面向 GPT-Image-2 创作者的提示词检索站。</strong><br>
  把多个公开高质量提示词仓库整理成可搜索、可筛选、可复制、可部署的本地知识库。
</p>

<p align="center">
  <img alt="Prompts" src="https://img.shields.io/badge/prompts-7%2C391-246bfe">
  <img alt="Sources" src="https://img.shields.io/badge/sources-4-00a7a0">
  <img alt="Categories" src="https://img.shields.io/badge/categories-12-f0a400">
  <img alt="Runtime" src="https://img.shields.io/badge/runtime-Python%203.12-3776ab">
  <img alt="Dependencies" src="https://img.shields.io/badge/dependencies-zero-222222">
</p>

![开文伊美姬桌面端界面预览](screenshots/fullstack-desktop.png)

## 项目简介

开文伊美姬是一个本地优先的 GPT-Image-2 提示词网站。它把 YouMind、ZeroLu、Anil-matcha、EvoLinkAI 等公开仓库中的真实提示词案例导入为统一 JSON 数据，并提供一套轻量后台 API 和可直接使用的前端检索界面。

适合用来做：

- 提示词灵感库：按关键词、分类、来源、语言和标签快速找案例。
- 创作工作台：打开提示词卡片，一键复制，继续改写细节。
- 本地资料站：无需数据库，数据直接来自 `data/prompts.json`。
- 云端服务：可部署到 VPS、Docker、Render、Railway、Heroku 风格平台。
- 二次开发底座：前后端都很轻，适合继续加收藏、登录、在线生成、管理后台等功能。

## 当前数据

数据由 `scripts/import_prompts.py` 从克隆到 `.cache/repos` 的上游 Markdown 文件中抽取生成。

| 指标 | 数量 |
| --- | ---: |
| 提示词记录 | 7,391 |
| 来源仓库 | 4 |
| 分类 | 12 |
| 语言/地区标记 | 25 |
| 带文字相关标签的记录 | 3,968 |
| 需要参考图的记录 | 339 |
| API 相关记录 | 16 |

主要分类包括：

`海报排版`、`人像写真`、`广告创意`、`UI 设计`、`效果对比`、`角色设计`、`插画海报`、`电商主图`、`游戏场景`、`社媒内容`、`字体排版`、`信息图`。

## 功能亮点

- 本地全文检索：关键词会匹配标题、分类、来源、语言和提示词正文。
- 多维筛选：支持来源、分类、语言、标签组合筛选。
- 即开即用：Python 标准库后台，无第三方 Python 依赖。
- 前端降级友好：直接打开 `index.html` 时会连接 `http://127.0.0.1:8891`。
- 云端友好：内置 `Dockerfile`、`Procfile`、`render.yaml`。
- 来源可追溯：每条记录保留来源仓库、来源文件、来源链接和许可证字段。
- 复制体验完整：提示词卡片可以一键复制，适合高频创作场景。

## 快速开始

### 1. 克隆项目

```bash
git clone https://github.com/mangooding/kaiwen-yimeiji.git
cd kaiwen-yimeiji
```

### 2. 启动后台

Windows PowerShell、macOS、Linux 都可以直接运行：

```bash
python server.py
```

默认监听：

```text
http://127.0.0.1:8891
```

### 3. 打开网站

浏览器访问：

```text
http://127.0.0.1:8891
```

启动成功后，页面顶部会显示本地 API 已连接，并展示当前提示词总数。

## API 文档

后台由 `server.py` 提供，运行时会同时托管静态页面和 JSON API。

### 健康检查

```http
GET /api/health
```

示例响应：

```json
{
  "ok": true,
  "total": 7391
}
```

### 获取筛选维度

```http
GET /api/facets
```

返回来源、分类、语言、标签等统计信息，前端筛选器由这个接口自动生成。

### 搜索提示词

```http
GET /api/search?q=UI&source=evolink&language=zh-CN&limit=24
```

支持参数：

| 参数 | 说明 |
| --- | --- |
| `q` | 搜索关键词，可为空 |
| `source` | 来源 slug，例如 `youmind`、`zerolu`、`anil`、`evolink` |
| `category` | 分类名，例如 `UI 设计`、`人像写真` |
| `language` | 语言/地区标记，例如 `en`、`zh-CN`、`ja-JP` |
| `flag` | 标签，例如 `has_text`、`requires_reference`、`api_ready` |
| `offset` | 分页起点，默认 `0` |
| `limit` | 每页数量，默认 `24`，最大 `96` |

PowerShell 示例：

```powershell
Invoke-RestMethod "http://127.0.0.1:8891/api/search?q=电商&limit=3"
```

### 获取单条提示词

```http
GET /api/prompts/{id}
```

返回完整提示词正文、搜索文本、来源信息、预览图链接和标签。

## 数据来源

当前数据来自以下公开 GitHub 仓库：

| 来源 | 仓库 | 记录数 | 许可证字段 |
| --- | --- | ---: | --- |
| YouMind | https://github.com/YouMind-OpenLab/awesome-gpt-image-2 | 2,016 | CC BY 4.0 |
| ZeroLu | https://github.com/ZeroLu/awesome-gpt-image | 443 | Repository license file |
| Anil-matcha | https://github.com/Anil-matcha/Awesome-GPT-Image-2-API-Prompts | 52 | CC BY 4.0 |
| EvoLinkAI | https://github.com/EvoLinkAI/awesome-gpt-image-2-API-and-Prompts | 4,880 | Repository license file |

请遵守各上游仓库的许可证、署名和再分发要求。本项目保留来源字段是为了方便追溯和标注，不代表上游仓库与本项目存在官方关联。

## 重新导入数据

`.cache/` 已加入 `.gitignore`，适合临时存放上游仓库。

```bash
mkdir -p .cache/repos

git clone --depth 1 https://github.com/YouMind-OpenLab/awesome-gpt-image-2 .cache/repos/youmind
git clone --depth 1 https://github.com/ZeroLu/awesome-gpt-image .cache/repos/zerolu
git clone --depth 1 https://github.com/Anil-matcha/Awesome-GPT-Image-2-API-Prompts .cache/repos/anil
git clone --depth 1 https://github.com/EvoLinkAI/awesome-gpt-image-2-API-and-Prompts .cache/repos/evolink

python scripts/import_prompts.py
```

脚本会更新：

- `data/prompts.json`：统一后的提示词记录。
- `data/meta.json`：来源、分类、语言、标签统计。

## 云端部署

### Docker / VPS

```bash
docker build -t kaiwen-yimeiji .
docker run -p 8891:8891 kaiwen-yimeiji
```

部署后访问：

```text
http://服务器IP:8891
```

### Render

仓库已包含 `render.yaml`。

1. 在 Render 中连接 GitHub 仓库。
2. 选择 Blueprint 或 Web Service。
3. 使用默认配置部署。
4. 启动命令为：

```bash
python server.py --host 0.0.0.0 --port $PORT
```

### Railway / Heroku 风格平台

仓库包含 `Procfile`：

```text
web: python server.py --host 0.0.0.0 --port $PORT
```

平台识别 Python 项目后会自动使用该命令启动 Web 服务。

## 项目结构

```text
.
├── index.html              # 前端页面
├── styles.css              # 页面样式
├── script.js               # 检索、筛选、复制等前端逻辑
├── server.py               # 本地/云端后台 API
├── data/
│   ├── prompts.json        # 提示词数据
│   └── meta.json           # 数据统计
├── scripts/
│   └── import_prompts.py   # 上游仓库导入脚本
├── assets/                 # 站点视觉素材
├── screenshots/            # README 与展示截图
├── Dockerfile              # Docker 部署
├── Procfile                # Heroku/Railway 风格部署
└── render.yaml             # Render 部署配置
```

## 本地开发建议

- 修改前端：编辑 `index.html`、`styles.css`、`script.js`，刷新浏览器即可。
- 修改后台：编辑 `server.py` 后重启服务。
- 修改数据：更新 `.cache/repos` 中的上游仓库后重新运行导入脚本。
- 检查 Python 语法：

```bash
python -m py_compile server.py scripts/import_prompts.py
```

检查 JavaScript 语法：

```bash
node --check script.js
```

## 设计原则

开文伊美姬不是把提示词简单堆成列表，而是把“找案例、判断场景、复制改写、追溯来源”做成一个顺手的流程：

- 先按场景筛：人像、UI、海报、电商、角色、广告。
- 再按语言筛：中文、英文、日文、韩文等多语言记录。
- 最后按用途筛：需要参考图、含文字、API 相关、公众人物、敏感风格。

这样可以少翻很多 README 和 Markdown 文件，把时间留给真正的创作。

## 免责声明

- 本项目是独立整理与检索工具，不是 OpenAI 或任何上游仓库的官方项目。
- 提示词内容来自公开仓库导入结果，使用时请自行判断版权、肖像权、商标、平台政策和当地法律要求。
- 对外发布作品前，建议保留必要的来源标注，并遵守上游许可证要求。
