# 开文伊美姬

GPT-Image-2 提示词本地检索站，已导入 4 个公开 GitHub 仓库里的多语言提示词记录。

## 本地运行

```powershell
python server.py
```

打开：

```text
http://127.0.0.1:8891
```

## API

- `GET /api/health`：健康检查
- `GET /api/facets`：来源、分类、语言、标记统计
- `GET /api/search?q=UI&source=evolink&language=zh-CN&limit=24`：本地全文检索
- `GET /api/prompts/{id}`：获取单条提示词

## 重新导入数据

先把仓库克隆到 `.cache/repos` 下：

```powershell
git clone --depth 1 https://github.com/YouMind-OpenLab/awesome-gpt-image-2 .cache/repos/youmind
git clone --depth 1 https://github.com/ZeroLu/awesome-gpt-image .cache/repos/zerolu
git clone --depth 1 https://github.com/Anil-matcha/Awesome-GPT-Image-2-API-Prompts .cache/repos/anil
git clone --depth 1 https://github.com/EvoLinkAI/awesome-gpt-image-2-API-and-Prompts .cache/repos/evolink
python scripts/import_prompts.py
```

## 云端部署

### Docker / VPS

```bash
docker build -t kaiwen-yimeiji .
docker run -p 8891:8891 kaiwen-yimeiji
```

### Render

仓库里已经包含 `render.yaml`，连接 GitHub 仓库后可按 Blueprint 创建 Web Service。

### Railway / Heroku 风格平台

平台会读取 `Procfile`：

```text
web: python server.py --host 0.0.0.0 --port $PORT
```

## 数据与来源

导入结果位于 `data/prompts.json` 和 `data/meta.json`。当前数据来自：

- YouMind: https://github.com/YouMind-OpenLab/awesome-gpt-image-2
- ZeroLu: https://github.com/ZeroLu/awesome-gpt-image
- Anil-matcha: https://github.com/Anil-matcha/Awesome-GPT-Image-2-API-Prompts
- EvoLinkAI: https://github.com/EvoLinkAI/awesome-gpt-image-2-API-and-Prompts

请遵守各原仓库许可证和署名要求。本站保留来源仓库、来源文件、来源链接和许可证字段，方便追溯。
