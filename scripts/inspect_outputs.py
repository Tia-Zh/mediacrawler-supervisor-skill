#!/usr/bin/env python3
"""Inspect MediaSpider outputs and write simple quality metrics."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from pathlib import Path
from typing import Any


POST_HINTS = ("note", "post", "video", "content", "tieba", "zhihu", "bili", "xhs", "dy", "ks", "weibo")
COMMENT_HINTS = ("comment", "comments")
COMMENT_KEYS = {"comment_id", "comment_content", "parent_comment_id", "parent_comment_id_str"}


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows = []
    with path.open("r", encoding="utf-8", errors="replace") as file:
        for line in file:
            line = line.strip()
            if not line:
                continue
            try:
                item = json.loads(line)
                if isinstance(item, dict):
                    rows.append(item)
            except json.JSONDecodeError:
                continue
    return rows


def read_json(path: Path) -> list[dict[str, Any]]:
    try:
        data = json.loads(path.read_text(encoding="utf-8", errors="replace"))
    except Exception:
        return []
    if isinstance(data, list):
        return [item for item in data if isinstance(item, dict)]
    if not isinstance(data, dict):
        return []

    items_by_source = data.get("items_by_source")
    if isinstance(items_by_source, dict):
        rows = []
        for platform, items in items_by_source.items():
            if not isinstance(items, list):
                continue
            for item in items:
                if isinstance(item, dict):
                    rows.append({"__platform": platform, **item})
        return rows

    for value in data.values():
        if isinstance(value, list):
            return [item for item in value if isinstance(item, dict)]
    return []


def read_csv(path: Path) -> list[dict[str, Any]]:
    with path.open("r", encoding="utf-8-sig", errors="replace", newline="") as file:
        return list(csv.DictReader(file))


def classify_row(path: Path, row: dict[str, Any]) -> str:
    keys = {str(key).lower() for key in row}
    metadata = row.get("metadata") if isinstance(row.get("metadata"), dict) else {}
    record_type = str(metadata.get("record_type") or row.get("record_type") or "").lower()
    if "comment" in record_type or "reply" in record_type:
        return "comments"
    name = path.name.lower()
    if any(hint in name for hint in COMMENT_HINTS) or bool(keys & COMMENT_KEYS):
        return "comments"
    if row.get("__platform") or any(hint in name for hint in POST_HINTS):
        return "posts"
    return "unknown"


def row_id(row: dict[str, Any]) -> str:
    metadata = row.get("metadata") if isinstance(row.get("metadata"), dict) else {}
    for key in ("id", "note_id", "comment_id", "item_id", "aweme_id", "video_id", "source_id", "url"):
        value = row.get(key) or metadata.get(key)
        if value:
            return str(value)
    text = row.get("content") or row.get("body") or row.get("desc") or row.get("title") or row.get("text")
    return str(text or "")[:200]


def files_to_scan(root: Path) -> list[Path]:
    ignored_names = {"task.resolved.json", "inspection.json", "fallback_counts.json", "deep_comment_counts.json"}
    files = [
        path for path in root.rglob("*")
        if path.is_file()
        and path.name not in ignored_names
        and path.suffix.lower() in {".jsonl", ".json", ".csv"}
    ]
    foreign_reports = [path for path in files if path.name == "multi_topic_raw_with_fallbacks.json"]
    if foreign_reports:
        final_report = min(foreign_reports, key=lambda path: len(path.parts))
        files = [path for path in files if path.suffix.lower() != ".json"] + [final_report]
    return sorted(set(files))


def inspect(root: Path) -> dict[str, Any]:
    files = files_to_scan(root)
    totals = Counter()
    platform_totals = Counter()
    file_stats = []
    ids = []

    for path in files:
        try:
            if path.suffix.lower() == ".jsonl":
                rows = read_jsonl(path)
            elif path.suffix.lower() == ".json":
                rows = read_json(path)
            else:
                rows = read_csv(path)
        except Exception as exc:
            file_stats.append({"file": str(path), "error": str(exc), "rows": 0, "kind": "error"})
            continue

        kinds = Counter(classify_row(path, row) for row in rows)
        totals.update(kinds)
        for row in rows:
            platform = str(row.get("__platform") or row.get("platform") or "").strip()
            if platform:
                platform_totals[platform] += 1
            value = row_id(row)
            if value:
                ids.append(value)
        file_kind = next(iter(kinds)) if len(kinds) == 1 else ("mixed" if kinds else "empty")
        file_stats.append({"file": str(path), "rows": len(rows), "kind": file_kind, "kinds": dict(kinds)})

    id_counts = Counter(ids)
    duplicate_ids = sum(1 for count in id_counts.values() if count > 1)
    metrics = {
        "root": str(root),
        "files_scanned": len(files),
        "posts": totals["posts"],
        "comments": totals["comments"],
        "unknown_rows": totals["unknown"],
        "total_rows": sum(totals.values()),
        "platform_rows": dict(sorted(platform_totals.items())),
        "duplicate_id_count": duplicate_ids,
        "duplicate_id_ratio": round(duplicate_ids / len(ids), 4) if ids else 0,
        "files": file_stats,
    }
    return metrics


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("path", type=Path)
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args()

    root = args.path.resolve()
    metrics = inspect(root)
    out = args.output or (root / "inspection.json")
    out.write_text(json.dumps(metrics, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(metrics, ensure_ascii=False, indent=2))
    print(f"Wrote: {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
