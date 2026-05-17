#!/usr/bin/env python3
"""Import prompt records from the cloned upstream GitHub repositories.

The script intentionally uses only the Python standard library so it can run
locally or in a cloud build step without installing dependencies.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


REPO_CONFIGS = [
    {
        "slug": "youmind",
        "name": "YouMind",
        "owner_repo": "YouMind-OpenLab/awesome-gpt-image-2",
        "github": "https://github.com/YouMind-OpenLab/awesome-gpt-image-2",
        "license": "CC BY 4.0",
        "root": "youmind",
        "patterns": ["README*.md"],
    },
    {
        "slug": "zerolu",
        "name": "ZeroLu",
        "owner_repo": "ZeroLu/awesome-gpt-image",
        "github": "https://github.com/ZeroLu/awesome-gpt-image",
        "license": "Repository license file",
        "root": "zerolu",
        "patterns": ["README*.md"],
    },
    {
        "slug": "anil",
        "name": "Anil-matcha",
        "owner_repo": "Anil-matcha/Awesome-GPT-Image-2-API-Prompts",
        "github": "https://github.com/Anil-matcha/Awesome-GPT-Image-2-API-Prompts",
        "license": "CC BY 4.0",
        "root": "anil",
        "patterns": ["README.md"],
    },
    {
        "slug": "evolink",
        "name": "EvoLinkAI",
        "owner_repo": "EvoLinkAI/awesome-gpt-image-2-API-and-Prompts",
        "github": "https://github.com/EvoLinkAI/awesome-gpt-image-2-API-and-Prompts",
        "license": "Repository license file",
        "root": "evolink",
        "patterns": ["cases/*.md"],
    },
]


CATEGORY_ALIASES = {
    "portrait": "人像写真",
    "photography": "人像写真",
    "poster": "海报排版",
    "illustration": "插画海报",
    "game": "游戏场景",
    "entertainment": "游戏场景",
    "ui": "UI 设计",
    "ux": "UI 设计",
    "social": "社媒内容",
    "ecommerce": "电商主图",
    "product": "电商主图",
    "character": "角色设计",
    "comparison": "效果对比",
    "infographic": "信息图",
    "typography": "字体排版",
    "ad": "广告创意",
    "creative": "广告创意",
    "editing": "图像编辑",
    "style": "风格迁移",
    "api": "API",
}


FLAG_PATTERNS = {
    "requires_reference": r"\b(uploaded|reference image|based on the uploaded|input image|style reference)\b|参考图|上传",
    "has_text": r"\b(text|typography|headline|title|sign|poster|logo)\b|文字|标题|海报|招牌|标语",
    "api_ready": r"\b(api|json|request|response|parameter|payload)\b",
    "celebrity_or_public_figure": r"\b(Sam Altman|Elon Musk|Tim Cook|Donald Trump|Liu Yifei)\b|刘亦菲|马斯克",
    "sensitive_style": r"\b(sexy|seductive|cleavage|idol|bikini|nude)\b|性感|诱惑|暴露",
}


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def language_from_path(path: Path) -> str:
    name = path.name
    stem = path.stem
    if name == "README.md" or stem.endswith(".README"):
        return "en"
    for marker in ("README_", "README."):
        if name.startswith(marker):
            return name[len(marker) : -3]
    match = re.search(r"_([a-z]{2}(?:-[A-Z]{2})?)\.md$", name)
    return match.group(1) if match else "en"


def clean_heading(text: str) -> str:
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"!\[[^\]]*\]\([^)]+\)", "", text)
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
    text = re.sub(r"^No\.\s*\d+\s*:\s*", "", text, flags=re.I)
    text = re.sub(r"^Case\s*\d+\s*:\s*", "", text, flags=re.I)
    text = re.sub(r"\s*\(by\s+.*?\)\s*$", "", text, flags=re.I)
    text = re.sub(r"^[^\w\u4e00-\u9fff]+", "", text).strip()
    return text or "Untitled Prompt"


def normalize_space(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def markdown_link_url(text: str) -> str | None:
    match = re.search(r"\[[^\]]+\]\((https?://[^)]+)\)", text)
    return match.group(1) if match else None


def raw_url(owner_repo: str, rel_path: str) -> str:
    return f"https://raw.githubusercontent.com/{owner_repo}/main/{rel_path.replace('\\', '/')}"


def extract_first_image(section: str, owner_repo: str, rel_dir: str) -> str | None:
    patterns = [
        r'<img[^>]+src=["\']([^"\']+)["\']',
        r"!\[[^\]]*\]\(([^)]+)\)",
    ]
    for pattern in patterns:
        match = re.search(pattern, section, flags=re.I)
        if not match:
            continue
        url = match.group(1).strip()
        if url.startswith("http://") or url.startswith("https://"):
            return url
        if url.startswith("#"):
            continue
        return raw_url(owner_repo, str(Path(rel_dir) / url))
    return None


def extract_source(section: str, heading: str) -> str | None:
    source_line = re.search(r"\*\*Source:\*\*\s*(.+)", section, flags=re.I)
    if source_line:
        return markdown_link_url(source_line.group(1)) or normalize_space(source_line.group(1))
    return markdown_link_url(heading)


def extract_prompt_blocks(section: str) -> list[str]:
    marker_patterns = [
        r"(?:\*\*Prompt:\*\*|####\s*[^\n]*Prompt[^\n]*)(.*)",
    ]
    target = section
    for marker in marker_patterns:
        match = re.search(marker, section, flags=re.I | re.S)
        if match:
            target = match.group(1)
            break

    blocks = re.findall(r"```(?:[a-zA-Z0-9_-]+)?\s*\n(.*?)```", target, flags=re.S)
    cleaned = []
    for block in blocks:
        block = block.strip()
        if len(block) >= 8 and not block.lower().startswith(("python", "javascript", "bash")):
            cleaned.append(block)
    return cleaned


def infer_category(repo_slug: str, rel_path: str, h2: str, title: str, prompt: str) -> str:
    haystack = f"{rel_path} {h2} {title} {prompt[:500]}".lower()
    for key, label in CATEGORY_ALIASES.items():
        if key in haystack:
            return label
    if repo_slug == "anil" and "api" in haystack:
        return "API"
    return clean_heading(h2) if h2 else "综合"


def infer_flags(prompt: str, title: str) -> list[str]:
    haystack = f"{title}\n{prompt}"
    flags = [
        name
        for name, pattern in FLAG_PATTERNS.items()
        if re.search(pattern, haystack, flags=re.I)
    ]
    return sorted(flags)


def parse_markdown_file(path: Path, repo_root: Path, config: dict[str, Any]) -> list[dict[str, Any]]:
    rel_path = path.relative_to(repo_root).as_posix()
    text = read_text(path)
    language = language_from_path(path)
    headers = list(re.finditer(r"^(#{2,3})\s+(.+?)\s*$", text, flags=re.M))
    records: list[dict[str, Any]] = []
    current_h2 = ""

    for index, header in enumerate(headers):
        level = len(header.group(1))
        heading = header.group(2).strip()
        if level == 2:
            current_h2 = clean_heading(heading)
            continue
        if level != 3:
            continue

        end = len(text)
        for next_header in headers[index + 1 :]:
            if len(next_header.group(1)) <= 3:
                end = next_header.start()
                break

        section = text[header.end() : end]
        prompt_blocks = extract_prompt_blocks(section)
        if not prompt_blocks:
            continue

        title = clean_heading(heading)
        source_url = extract_source(section, heading)
        image_url = extract_first_image(section, config["owner_repo"], str(Path(rel_path).parent))
        for block_index, prompt in enumerate(prompt_blocks):
            prompt = prompt.strip()
            if len(prompt) < 8:
                continue
            identity = "|".join(
                [
                    config["slug"],
                    rel_path,
                    language,
                    title,
                    hashlib.sha1(prompt.encode("utf-8")).hexdigest(),
                    str(block_index),
                ]
            )
            record_id = hashlib.sha1(identity.encode("utf-8")).hexdigest()[:18]
            category = infer_category(config["slug"], rel_path, current_h2, title, prompt)
            records.append(
                {
                    "id": record_id,
                    "title": title,
                    "prompt": prompt,
                    "category": category,
                    "language": language,
                    "source": config["name"],
                    "sourceSlug": config["slug"],
                    "sourceRepo": config["github"],
                    "sourceUrl": source_url or config["github"],
                    "sourceFile": rel_path,
                    "image": image_url,
                    "license": config["license"],
                    "flags": infer_flags(prompt, title),
                    "length": len(prompt),
                    "searchText": normalize_space(f"{title} {category} {language} {config['name']} {prompt}")[:12000],
                }
            )

    return records


def iter_files(root: Path, patterns: list[str]) -> list[Path]:
    files: list[Path] = []
    for pattern in patterns:
        files.extend(root.glob(pattern))
    return sorted({file for file in files if file.is_file()})


def import_prompts(cache_dir: Path) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    all_records: list[dict[str, Any]] = []
    repo_stats: dict[str, Any] = {}

    for config in REPO_CONFIGS:
        repo_root = cache_dir / config["root"]
        if not repo_root.exists():
            repo_stats[config["slug"]] = {"error": f"Missing repository cache: {repo_root}"}
            continue
        files = iter_files(repo_root, config["patterns"])
        records: list[dict[str, Any]] = []
        seen = set()
        for path in files:
            for record in parse_markdown_file(path, repo_root, config):
                key = (record["sourceSlug"], record["language"], record["prompt"])
                if key in seen:
                    continue
                seen.add(key)
                records.append(record)
        all_records.extend(records)
        repo_stats[config["slug"]] = {
            "name": config["name"],
            "repo": config["github"],
            "license": config["license"],
            "files": len(files),
            "records": len(records),
            "languages": dict(sorted(Counter(r["language"] for r in records).items())),
        }

    all_records.sort(key=lambda item: (item["source"], item["language"], item["title"], item["id"]))

    meta = {
        "generatedAt": dt.datetime.now(dt.timezone.utc).isoformat(),
        "total": len(all_records),
        "sources": repo_stats,
        "categories": dict(sorted(Counter(r["category"] for r in all_records).items())),
        "languages": dict(sorted(Counter(r["language"] for r in all_records).items())),
        "flags": dict(sorted(Counter(flag for r in all_records for flag in r["flags"]).items())),
        "note": "Imported from cloned GitHub repository Markdown files. Multi-language README/case files are preserved as separate searchable records.",
    }
    return all_records, meta


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cache-dir", default=".cache/repos", type=Path)
    parser.add_argument("--out-dir", default="data", type=Path)
    args = parser.parse_args()

    records, meta = import_prompts(args.cache_dir)
    args.out_dir.mkdir(parents=True, exist_ok=True)
    (args.out_dir / "prompts.json").write_text(
        json.dumps(records, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (args.out_dir / "meta.json").write_text(
        json.dumps(meta, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print(f"Imported {len(records)} prompt records")
    for slug, stats in meta["sources"].items():
        print(f"- {slug}: {stats.get('records', 0)} records from {stats.get('files', 0)} files")


if __name__ == "__main__":
    main()
