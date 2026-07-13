#!/usr/bin/env python3
"""Run a MediaSpider task JSON with reproducible logs."""

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


BOOL_FLAGS = {
    "get_comment": "--get_comment",
    "get_sub_comment": "--get_sub_comment",
    "headless": "--headless",
    "enable_ip_proxy": "--enable_ip_proxy",
}

VALUE_FLAGS = {
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


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8-sig") as f:
        return json.load(f)


def as_csv(value: Any) -> str:
    if isinstance(value, list):
        return ",".join(str(v).strip() for v in value if str(v).strip())
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
    mediaspider_home = engine_root / "MediaSpider"
    if mediaspider_home.exists():
        return mediaspider_home
    publicscope_home = engine_root / "PublicScopeCollector"
    if publicscope_home.exists():
        return publicscope_home
    return engine_root / "MediaCrawler"


def build_command(task: dict[str, Any], media_home: Path) -> list[str]:
    if shutil.which("uv"):
        cmd = ["uv", "run", "python", "main.py"]
    else:
        cmd = [sys.executable, "main.py"]

    for key, flag in VALUE_FLAGS.items():
        value = task.get(key)
        if value is not None and value != "":
            cmd.extend([flag, as_csv(value)])

    keywords = task.get("keywords")
    if keywords:
        cmd.extend(["--keywords", as_csv(keywords)])

    for key, flag in BOOL_FLAGS.items():
        if key in task:
            cmd.extend([flag, truth(task[key])])

    return cmd


def resolve_run_dir(task_path: Path, task: dict[str, Any]) -> Path:
    if task.get("run_dir"):
        return Path(task["run_dir"]).expanduser().resolve()
    stem = task_path.stem
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return (task_path.parent / f"{stamp}_{stem}").resolve()


def has_cleanup_patch(media_home: Path) -> bool:
    platforms = ("douyin", "kuaishou", "xhs", "bilibili", "weibo", "tieba", "zhihu")
    for platform in platforms:
        core_py = media_home / "media_platform" / platform / "core.py"
        if not core_py.exists():
            return False
        text = core_py.read_text(encoding="utf-8", errors="ignore")
        if "async def data_assistant_cleanup_pages" not in text:
            return False
        if "await self.data_assistant_cleanup_pages()" not in text:
            return False
    return True


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("task_json", type=Path)
    parser.add_argument("--media-home", type=Path, default=None)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    task_path = args.task_json.resolve()
    task = load_json(task_path)
    configured_home = task.get("media_crawler_home")
    if args.media_home:
        media_home = args.media_home
    elif configured_home:
        media_home = Path(configured_home)
    else:
        media_home = default_home()
    media_home = media_home.resolve()

    main_py = media_home / "main.py"
    if not main_py.exists():
        raise SystemExit(f"MediaSpider main.py not found: {main_py}")

    cleanup_patch_ok = has_cleanup_patch(media_home)
    run_dir = resolve_run_dir(task_path, task)
    run_dir.mkdir(parents=True, exist_ok=False)

    if not task.get("save_data_path"):
        output_dir = run_dir / "raw"
        output_dir.mkdir(parents=True, exist_ok=True)
        task["save_data_path"] = str(output_dir)
    else:
        output_dir = Path(task["save_data_path"]).expanduser().resolve()
        output_dir.mkdir(parents=True, exist_ok=True)

    cmd = build_command(task, media_home)

    (run_dir / "task.resolved.json").write_text(
        json.dumps(task, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (run_dir / "command.txt").write_text(" ".join(cmd), encoding="utf-8")

    print(f"Run directory: {run_dir}")
    print(f"MediaSpider: {media_home}")
    if not cleanup_patch_ok:
        print("Warning: MediaCrawler is missing the Data Assistant stale-tab cleanup patch.")
        print("Run scripts/bootstrap.ps1 to install MediaSpider mediaspider-v0.2.1.")
    print("Command:", " ".join(cmd))

    if args.dry_run:
        return 0

    with (run_dir / "run.log").open("w", encoding="utf-8", errors="replace") as log:
        log.write(f"started_at={datetime.now().isoformat()}\n")
        log.write(f"command={' '.join(cmd)}\n\n")
        log.flush()
        proc = subprocess.Popen(
            cmd,
            cwd=str(media_home),
            stdout=log,
            stderr=subprocess.STDOUT,
            text=True,
        )
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
    if code == 0 and not output_files:
        log_text = (run_dir / "run.log").read_text(encoding="utf-8", errors="replace").lower()
        login_markers = ("login failed", "failed by qrcode", "waiting for scan code", "have not found qrcode")
        if any(marker in log_text for marker in login_markers):
            print("Status: login required; no raw output was produced.")
            code = 3
        else:
            print("Status: task finished without non-empty raw output.")
            code = 4

    print(f"Exit code: {code}")
    print(f"Log: {run_dir / 'run.log'}")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
