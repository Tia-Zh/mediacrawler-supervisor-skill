#!/usr/bin/env python3
"""Run a domestic or foreign MediaSpider task with reproducible logs."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


DOMESTIC_PLATFORMS = {"xhs", "dy", "ks", "bili", "wb", "tieba", "zhihu"}
FOREIGN_PLATFORMS = {
    "reddit", "x", "youtube", "tiktok", "instagram", "hackernews",
    "polymarket", "github", "threads", "pinterest", "bluesky",
    "truthsocial", "grounding", "xiaohongshu", "perplexity", "digg",
    "arxiv", "techmeme", "trustpilot", "jobs", "linkedin",
}

DOMESTIC_BOOL_FLAGS = {
    "get_comment": "--get_comment",
    "get_sub_comment": "--get_sub_comment",
    "headless": "--headless",
    "enable_ip_proxy": "--enable_ip_proxy",
}

DOMESTIC_VALUE_FLAGS = {
    "platform": "--platform",
    "login_type": "--lt",
    "crawler_type": "--type",
    "start_page": "--start",
    "save_data_option": "--save_data_option",
    "cookies": "--cookies",
    "specified_id": "--specified_id",
    "creator_id": "--creator_id",
    "max_comments_per_post": "--max_comments_count_singlenotes",
    "max_posts": "--crawler_max_notes_count",
    "max_concurrency": "--max_concurrency_num",
    "save_data_path": "--save_data_path",
    "ip_proxy_pool_count": "--ip_proxy_pool_count",
    "ip_proxy_provider_name": "--ip_proxy_provider_name",
    "static_proxy_url": "--static_proxy_url",
}

FOREIGN_VALUE_FLAGS = {
    "topics": "--topics",
    "topics_file": "--topics-file",
    "start_date": "--start-date",
    "end_date": "--end-date",
    "keywords": "--keywords",
    "subject_terms": "--subject-terms",
    "issue_terms": "--issue-terms",
    "match_mode": "--match-mode",
    "max_generated_topics": "--max-generated-topics",
    "days": "--days",
    "as_of": "--as-of",
    "last30days_script": "--last30days-script",
    "fallback_limit": "--fallback-limit",
    "command_timeout": "--command-timeout",
    "youtube_detail_limit": "--youtube-detail-limit",
    "deep_targets_per_source": "--deep-targets-per-source",
    "deep_comments_per_item": "--deep-comments-per-item",
    "deep_reply_depth": "--deep-reply-depth",
}

FOREIGN_BOOL_FLAGS = {
    "drop_undated": "--drop-undated",
    "quick": "--quick",
    "deep": "--deep",
    "mock": "--mock",
    "no_browser_cookies": "--no-browser-cookies",
    "deep_crawl": "--deep-crawl",
    "no_fallback": "--no-fallback",
}


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8-sig") as file:
        return json.load(file)


def as_csv(value: Any) -> str:
    if isinstance(value, list):
        return ",".join(str(item).strip() for item in value if str(item).strip())
    return str(value)


def as_topics(value: Any) -> str:
    if isinstance(value, list):
        return ";".join(str(item).strip() for item in value if str(item).strip())
    return str(value)


def truth(value: Any) -> str:
    return "true" if bool(value) else "false"


def default_home() -> Path:
    env_home = (
        os.environ.get("MEDIASPIDER_HOME")
        or os.environ.get("PUBLICSCOPE_HOME")
        or os.environ.get("MEDIACRAWLER_HOME")
    )
    if env_home:
        return Path(env_home)
    engine_root = Path.home() / ".data_assistant" / "engines"
    for name in ("MediaSpider", "PublicScopeCollector", "MediaCrawler"):
        candidate = engine_root / name
        if candidate.exists():
            return candidate
    return engine_root / "MediaSpider"


def platform_values(task: dict[str, Any]) -> list[str]:
    value = task.get("platforms", task.get("platform", []))
    if isinstance(value, list):
        return [str(item).strip().lower() for item in value if str(item).strip()]
    return [item.strip().lower() for item in str(value).split(",") if item.strip()]


def collector_kind(task: dict[str, Any]) -> str:
    explicit = str(task.get("collector") or "").strip().lower()
    if explicit in {"domestic", "foreign"}:
        return explicit
    platforms = set(platform_values(task))
    if platforms and platforms <= FOREIGN_PLATFORMS:
        return "foreign"
    if platforms and platforms <= DOMESTIC_PLATFORMS:
        return "domestic"
    if platforms & FOREIGN_PLATFORMS and platforms & DOMESTIC_PLATFORMS:
        raise ValueError("One task cannot mix domestic and foreign platforms; create two task files.")
    raise ValueError("Set collector to domestic/foreign or provide supported platform values.")


def python_command(entrypoint: str) -> list[str]:
    if shutil.which("uv"):
        return ["uv", "run", "python", entrypoint]
    return [sys.executable, entrypoint]


def build_domestic_command(task: dict[str, Any]) -> list[str]:
    cmd = python_command("main.py")
    for key, flag in DOMESTIC_VALUE_FLAGS.items():
        value = task.get(key)
        if value is not None and value != "":
            cmd.extend([flag, as_csv(value)])
    if task.get("keywords"):
        cmd.extend(["--keywords", as_csv(task["keywords"])])
    for key, flag in DOMESTIC_BOOL_FLAGS.items():
        if key in task:
            cmd.extend([flag, truth(task[key])])
    return cmd


def build_foreign_command(task: dict[str, Any]) -> list[str]:
    topic = str(task.get("topic") or "foreign-collection").strip()
    cmd = python_command("foreign_collect.py") + [topic]
    platforms = task.get("platforms", task.get("platform"))
    if platforms:
        cmd.extend(["--platforms", as_csv(platforms)])

    for key, flag in FOREIGN_VALUE_FLAGS.items():
        value = task.get(key)
        if value is None or value == "":
            continue
        formatter = as_topics if key == "topics" else as_csv
        cmd.extend([flag, formatter(value)])

    if task.get("max_results_per_platform") is not None and task.get("fallback_limit") is None:
        cmd.extend(["--fallback-limit", str(task["max_results_per_platform"])])
    if task.get("max_posts") is not None and task.get("fallback_limit") is None and task.get("max_results_per_platform") is None:
        cmd.extend(["--fallback-limit", str(task["max_posts"])])
    if task.get("max_comments_per_post") is not None and task.get("deep_comments_per_item") is None:
        cmd.extend(["--deep-comments-per-item", str(task["max_comments_per_post"])])

    mode = str(task.get("foreign_mode") or "fallback-only").strip().lower()
    if mode in {"fallback", "fallback-only", "local", "agent-reach"}:
        cmd.append("--fallback-only")
    elif mode == "hybrid":
        cmd.append("--hybrid")
    elif mode not in {"last30days", "last30days-only"}:
        raise ValueError("foreign_mode must be fallback-only, hybrid, or last30days.")

    for key, flag in FOREIGN_BOOL_FLAGS.items():
        if bool(task.get(key)):
            cmd.append(flag)

    cmd.extend(["--output", str(task["output"]), "--output-dir", str(task["output_dir"])])
    return cmd


def build_command(task: dict[str, Any], kind: str) -> list[str]:
    return build_foreign_command(task) if kind == "foreign" else build_domestic_command(task)


def resolve_run_dir(task_path: Path, task: dict[str, Any]) -> Path:
    if task.get("run_dir"):
        return Path(task["run_dir"]).expanduser().resolve()
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return (task_path.parent / f"{stamp}_{task_path.stem}").resolve()


def has_cleanup_patch(media_home: Path) -> bool:
    for platform in ("douyin", "kuaishou", "xhs", "bilibili", "weibo", "tieba", "zhihu"):
        core_py = media_home / "media_platform" / platform / "core.py"
        if not core_py.exists():
            return False
        text = core_py.read_text(encoding="utf-8", errors="ignore")
        if "async def data_assistant_cleanup_pages" not in text:
            return False
        if "await self.data_assistant_cleanup_pages()" not in text:
            return False
    return True


def foreign_row_count(output_dir: Path) -> int:
    for path in sorted(output_dir.rglob("multi_topic_raw_with_fallbacks.json"), reverse=True):
        try:
            report = json.loads(path.read_text(encoding="utf-8", errors="replace"))
            return sum(
                len(rows) for rows in (report.get("items_by_source") or {}).values()
                if isinstance(rows, list)
            )
        except Exception:
            continue
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("task_json", type=Path)
    parser.add_argument("--media-home", type=Path, default=None)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    task_path = args.task_json.resolve()
    task = load_json(task_path)
    kind = collector_kind(task)
    configured_home = task.get("media_crawler_home") or task.get("mediaspider_home")
    media_home = args.media_home or (Path(configured_home) if configured_home else default_home())
    media_home = media_home.resolve()

    entrypoint = media_home / ("foreign_collect.py" if kind == "foreign" else "main.py")
    if not entrypoint.exists():
        raise SystemExit(f"MediaSpider entrypoint not found: {entrypoint}")

    run_dir = resolve_run_dir(task_path, task)
    run_dir.mkdir(parents=True, exist_ok=False)
    output_dir = Path(task.get("save_data_path") or task.get("output_dir") or (run_dir / "raw")).expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    task["collector"] = kind
    if kind == "foreign":
        task["output_dir"] = str(output_dir)
        task["output"] = str(Path(task.get("output") or (output_dir / "foreign_sources.xlsx")).expanduser().resolve())
    else:
        task["save_data_path"] = str(output_dir)

    cmd = build_command(task, kind)
    command_text = subprocess.list2cmdline(cmd)
    (run_dir / "task.resolved.json").write_text(json.dumps(task, ensure_ascii=False, indent=2), encoding="utf-8")
    (run_dir / "command.txt").write_text(command_text, encoding="utf-8")

    print(f"Run directory: {run_dir}")
    print(f"MediaSpider: {media_home}")
    print(f"Collector: {kind}")
    if kind == "domestic" and not has_cleanup_patch(media_home):
        print("Warning: MediaSpider is missing the stale-tab cleanup patch.")
        print("Run scripts/bootstrap.ps1 to install the current MediaSpider release.")
    print("Command:", command_text)

    if args.dry_run:
        return 0

    log_path = run_dir / "run.log"
    with log_path.open("w", encoding="utf-8", errors="replace") as log:
        log.write(f"started_at={datetime.now().isoformat()}\n")
        log.write(f"command={command_text}\n\n")
        log.flush()
        proc = subprocess.Popen(cmd, cwd=str(media_home), stdout=log, stderr=subprocess.STDOUT, text=True)
        try:
            code = proc.wait()
        except KeyboardInterrupt:
            proc.terminate()
            try:
                proc.wait(timeout=10)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait()
            code = 130
        log.write(f"\nfinished_at={datetime.now().isoformat()}\nexit_code={code}\n")

    output_suffixes = {".jsonl", ".json", ".csv", ".xlsx", ".xls"}
    output_files = [
        path for path in output_dir.rglob("*")
        if path.is_file() and path.suffix.lower() in output_suffixes and path.stat().st_size > 0
    ]
    if code == 0 and kind == "foreign" and foreign_row_count(output_dir) == 0:
        print("Status: foreign collection finished without data rows.")
        code = 4
    elif code == 0 and not output_files:
        log_text = log_path.read_text(encoding="utf-8", errors="replace").lower()
        login_markers = ("login failed", "failed by qrcode", "waiting for scan code", "have not found qrcode")
        if any(marker in log_text for marker in login_markers):
            print("Status: login required; no raw output was produced.")
            code = 3
        else:
            print("Status: task finished without non-empty raw output.")
            code = 4

    print(f"Exit code: {code}")
    print(f"Log: {log_path}")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
