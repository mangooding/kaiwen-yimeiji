#!/usr/bin/env python3
"""Local and cloud-ready backend for 开文伊美姬.

Run locally:
    python server.py

Then open:
    http://127.0.0.1:8891
"""

from __future__ import annotations

import argparse
import json
import mimetypes
import os
import re
import time
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, unquote, urlparse


ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data"
PROMPTS_PATH = DATA_DIR / "prompts.json"
META_PATH = DATA_DIR / "meta.json"
DEFAULT_LIMIT = 24
MAX_LIMIT = 96


class PromptStore:
    def __init__(self, prompts_path: Path, meta_path: Path) -> None:
        self.prompts_path = prompts_path
        self.meta_path = meta_path
        self.prompts: list[dict[str, Any]] = []
        self.meta: dict[str, Any] = {}
        self.by_id: dict[str, dict[str, Any]] = {}
        self.load()

    def load(self) -> None:
        if self.prompts_path.exists():
            self.prompts = json.loads(self.prompts_path.read_text(encoding="utf-8"))
        else:
            self.prompts = []
        if self.meta_path.exists():
            self.meta = json.loads(self.meta_path.read_text(encoding="utf-8"))
        else:
            self.meta = {"total": len(self.prompts), "sources": {}, "categories": {}, "languages": {}}
        self.by_id = {item["id"]: item for item in self.prompts}
        for item in self.prompts:
            item["_index"] = normalize(f'{item.get("searchText", "")} {item.get("prompt", "")}')
            item["_titleIndex"] = normalize(item.get("title", ""))
            item["_categoryIndex"] = normalize(item.get("category", ""))

    def facets(self) -> dict[str, Any]:
        return {
            "total": len(self.prompts),
            "generatedAt": self.meta.get("generatedAt"),
            "sources": self.meta.get("sources", {}),
            "categories": self.meta.get("categories", {}),
            "languages": self.meta.get("languages", {}),
            "flags": self.meta.get("flags", {}),
        }

    def search(self, params: dict[str, list[str]]) -> dict[str, Any]:
        query = first(params, "q", "").strip()
        source = first(params, "source", "").strip()
        category = first(params, "category", "").strip()
        language = first(params, "language", "").strip()
        flag = first(params, "flag", "").strip()
        offset = to_int(first(params, "offset", "0"), 0)
        limit = min(max(to_int(first(params, "limit", str(DEFAULT_LIMIT)), DEFAULT_LIMIT), 1), MAX_LIMIT)
        tokens = tokenize(query)

        started = time.perf_counter()
        matches: list[tuple[int, dict[str, Any]]] = []
        for item in self.prompts:
            if source and item.get("sourceSlug") != source:
                continue
            if category and item.get("category") != category:
                continue
            if language and item.get("language") != language:
                continue
            if flag and flag not in item.get("flags", []):
                continue
            score = score_item(item, tokens)
            if tokens and score <= 0:
                continue
            matches.append((score, item))

        if tokens:
            matches.sort(key=lambda pair: (-pair[0], pair[1].get("source", ""), pair[1].get("title", "")))
        else:
            matches.sort(key=lambda pair: (pair[1].get("source", ""), pair[1].get("language", ""), pair[1].get("title", "")))

        sliced = matches[offset : offset + limit]
        items = [public_prompt(item, score=score, compact=True) for score, item in sliced]
        elapsed_ms = round((time.perf_counter() - started) * 1000, 2)
        return {
            "query": query,
            "total": len(matches),
            "offset": offset,
            "limit": limit,
            "elapsedMs": elapsed_ms,
            "items": items,
        }

    def get_prompt(self, prompt_id: str) -> dict[str, Any] | None:
        item = self.by_id.get(prompt_id)
        return public_prompt(item, compact=False) if item else None


def first(params: dict[str, list[str]], key: str, default: str) -> str:
    value = params.get(key)
    return value[0] if value else default


def to_int(value: str, default: int) -> int:
    try:
        return int(value)
    except ValueError:
        return default


def normalize(text: str) -> str:
    return text.casefold()


def tokenize(query: str) -> list[str]:
    normalized = normalize(query)
    tokens = re.findall(r"[\w.-]+|[\u4e00-\u9fff]+", normalized)
    if not tokens and normalized:
        tokens = [normalized]
    return [token for token in tokens if token.strip()]


def score_item(item: dict[str, Any], tokens: list[str]) -> int:
    if not tokens:
        return 1
    score = 0
    index = item.get("_index", "")
    title = item.get("_titleIndex", "")
    category = item.get("_categoryIndex", "")
    for token in tokens:
        if token not in index:
            continue
        score += 10
        if token in title:
            score += 24
        if token in category:
            score += 12
        if token in normalize(item.get("source", "")):
            score += 8
        if token in normalize(item.get("language", "")):
            score += 4
    return score


def public_prompt(item: dict[str, Any] | None, score: int = 0, compact: bool = True) -> dict[str, Any]:
    if not item:
        return {}
    prompt = item.get("prompt", "")
    preview = prompt if len(prompt) <= 520 else f"{prompt[:520].rstrip()}..."
    data = {
        "id": item.get("id"),
        "title": item.get("title"),
        "prompt": prompt,
        "promptPreview": preview,
        "category": item.get("category"),
        "language": item.get("language"),
        "source": item.get("source"),
        "sourceSlug": item.get("sourceSlug"),
        "sourceRepo": item.get("sourceRepo"),
        "sourceUrl": item.get("sourceUrl"),
        "sourceFile": item.get("sourceFile"),
        "image": item.get("image"),
        "license": item.get("license"),
        "flags": item.get("flags", []),
        "length": item.get("length"),
        "score": score,
    }
    if compact:
        return data
    data["searchText"] = item.get("searchText")
    return data


class AppHandler(SimpleHTTPRequestHandler):
    store = PromptStore(PROMPTS_PATH, META_PATH)

    def translate_path(self, path: str) -> str:
        parsed = urlparse(path)
        request_path = unquote(parsed.path)
        if request_path == "/":
            request_path = "/index.html"
        request_path = request_path.lstrip("/")
        target = (ROOT / request_path).resolve()
        if not str(target).startswith(str(ROOT)):
            return str(ROOT / "index.html")
        return str(target)

    def end_headers(self) -> None:
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        super().end_headers()

    def do_OPTIONS(self) -> None:
        self.send_response(HTTPStatus.NO_CONTENT)
        self.end_headers()

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/api/health":
            self.write_json({"ok": True, "total": len(self.store.prompts)})
            return
        if parsed.path == "/api/facets":
            self.write_json(self.store.facets())
            return
        if parsed.path == "/api/search":
            self.write_json(self.store.search(parse_qs(parsed.query)))
            return
        if parsed.path.startswith("/api/prompts/"):
            prompt_id = parsed.path.rsplit("/", 1)[-1]
            item = self.store.get_prompt(prompt_id)
            if not item:
                self.write_json({"error": "Prompt not found"}, status=HTTPStatus.NOT_FOUND)
                return
            self.write_json(item)
            return
        super().do_GET()

    def guess_type(self, path: str) -> str:
        if path.endswith(".js"):
            return "text/javascript; charset=utf-8"
        if path.endswith(".css"):
            return "text/css; charset=utf-8"
        if path.endswith(".json"):
            return "application/json; charset=utf-8"
        return mimetypes.guess_type(path)[0] or "application/octet-stream"

    def write_json(self, data: dict[str, Any], status: HTTPStatus = HTTPStatus.OK) -> None:
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default=os.environ.get("HOST", "127.0.0.1"))
    parser.add_argument("--port", default=int(os.environ.get("PORT", "8891")), type=int)
    args = parser.parse_args()

    server = ThreadingHTTPServer((args.host, args.port), AppHandler)
    print(f"开文伊美姬 backend running at http://{args.host}:{args.port}")
    print(f"Loaded {len(AppHandler.store.prompts)} prompt records")
    server.serve_forever()


if __name__ == "__main__":
    main()
