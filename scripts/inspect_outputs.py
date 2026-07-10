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
    with path.open("r", encoding="utf-8", errors="replace") as f:
        for line in f:
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
        return [x for x in data if isinstance(x, dict)]
    if isinstance(data, dict):
        for value in data.values():
            if isinstance(value, list):
                return [x for x in value if isinstance(x, dict)]
        return [data]
    return []


def read_csv(path: Path) -> list[dict[str, Any]]:
    with path.open("r", encoding="utf-8-sig", errors="replace", newline="") as f:
        return list(csv.DictReader(f))


def classify(path: Path, rows: list[dict[str, Any]]) -> str:
    name = path.name.lower()
    keys = set()
    for row in rows[:20]:
        keys.update(k.lower() for k in row.keys())
    if any(h in name for h in COMMENT_HINTS) or bool(keys & COMMENT_KEYS):
        return "comments"
    if any(h in name for h in POST_HINTS):
        return "posts"
    return "unknown"


def row_id(row: dict[str, Any]) -> str:
    for key in ("id", "note_id", "comment_id", "aweme_id", "video_id", "source_id", "url"):
        value = row.get(key)
        if value:
            return str(value)
    text = row.get("content") or row.get("desc") or row.get("title") or row.get("text")
    return str(text or "")[:200]


def inspect(root: Path) -> dict[str, Any]:
    ignored_names = {"task.resolved.json", "inspection.json"}
    files = [
        p for p in root.rglob("*")
        if p.is_file()
        and p.name not in ignored_names
        and p.suffix.lower() in {".jsonl", ".json", ".csv"}
    ]
    totals = Counter()
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

        kind = classify(path, rows)
        totals[kind] += len(rows)
        ids.extend(row_id(row) for row in rows if row_id(row))
        file_stats.append({"file": str(path), "rows": len(rows), "kind": kind})

    id_counts = Counter(ids)
    duplicate_ids = sum(1 for _, count in id_counts.items() if count > 1)
    total_ids = len(ids)

    metrics = {
        "root": str(root),
        "files_scanned": len(files),
        "posts": totals["posts"],
        "comments": totals["comments"],
        "unknown_rows": totals["unknown"],
        "duplicate_id_count": duplicate_ids,
        "duplicate_id_ratio": round(duplicate_ids / total_ids, 4) if total_ids else 0,
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
