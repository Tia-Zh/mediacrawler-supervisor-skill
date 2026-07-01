# Task Schema

Create one JSON file per MediaCrawler run. Keep it small, explicit, and reproducible.

## Minimal Search Task

```json
{
  "platform": "xhs",
  "crawler_type": "search",
  "login_type": "qrcode",
  "keywords": ["india travel", "india visitors"],
  "get_comment": true,
  "get_sub_comment": false,
  "max_posts": 20,
  "max_comments_per_post": 30,
  "max_concurrency": 1,
  "save_data_option": "jsonl",
  "headless": false
}
```

## Fields

- `media_crawler_home`: Optional absolute path to MediaCrawler. Prefer `MEDIACRAWLER_HOME` when available.
- `run_dir`: Optional absolute or relative run directory. If omitted, `run_task.py` creates a timestamped directory beside the task file.
- `platform`: Required. One of `xhs`, `dy`, `ks`, `bili`, `wb`, `tieba`, `zhihu`.
- `crawler_type`: Required. One of `search`, `detail`, `creator`.
- `login_type`: Usually `qrcode`. Use `cookie` only when the user provides cookies locally.
- `keywords`: String or list. Used by `search`.
- `specified_id`: String or list. Used by `detail`.
- `creator_id`: String or list. Used by `creator`.
- `get_comment`: Boolean. Crawl first-level comments.
- `get_sub_comment`: Boolean. Crawl second-level comments. Start with `false` unless the task needs deep threads.
- `max_posts`: Maximum posts/videos/items to crawl.
- `max_comments_per_post`: Maximum first-level comments per post.
- `max_concurrency`: Keep `1` for trial runs and login-sensitive platforms.
- `save_data_option`: Prefer `jsonl` for raw collection, `excel` for immediate human review.
- `save_data_path`: Optional output directory. If omitted, `run_task.py` creates `raw/` under the run directory.
- `headless`: Keep `false` when login, captcha, or manual verification may appear.
- `enable_ip_proxy`, `ip_proxy_pool_count`, `ip_proxy_provider_name`, `static_proxy_url`: Proxy settings. Do not enable unless the user has approved and configured a compliant provider.

## Trial Limits

Start with:

- `max_posts`: 10-30
- `max_comments_per_post`: 10-50
- `max_concurrency`: 1
- `get_sub_comment`: false

Increase only after inspecting output quality and explaining why.

## Run Package

Each run directory should contain:

- `task.resolved.json`
- `command.txt`
- `run.log`
- `inspection.json`
- `decision_log.jsonl` for multi-step runs
- `raw/` output files
- `collection_note.md` for the final summary
