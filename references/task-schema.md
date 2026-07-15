# Task Schema

Create one JSON file per run. Domestic and foreign platforms use the same runner but different fields.

## Domestic Task

```json
{
  "collector": "domestic",
  "platform": "xhs",
  "crawler_type": "search",
  "login_type": "qrcode",
  "keywords": ["India travel", "India visitors"],
  "get_comment": true,
  "get_sub_comment": false,
  "max_posts": 20,
  "max_comments_per_post": 30,
  "max_concurrency": 1,
  "save_data_option": "jsonl",
  "headless": false
}
```

Domestic `platform` values: `xhs`, `dy`, `ks`, `bili`, `wb`, `tieba`, `zhihu`.

Useful fields: `crawler_type`, `login_type`, `keywords`, `specified_id`, `creator_id`, `get_comment`, `get_sub_comment`, `max_posts`, `max_comments_per_post`, `max_concurrency`, `save_data_option`, `save_data_path`, `headless`, and approved proxy settings.

## Foreign Task

```json
{
  "collector": "foreign",
  "topic": "AI public discussion",
  "platforms": ["x", "youtube", "reddit", "bluesky"],
  "start_date": "2026-06-01",
  "end_date": "2026-06-30",
  "keywords": ["AI", "artificial intelligence", "large language model"],
  "match_mode": "any",
  "foreign_mode": "fallback-only",
  "max_results_per_platform": 50,
  "command_timeout": 180,
  "deep_crawl": false
}
```

Common foreign platforms: `x`, `youtube`, `reddit`, `tiktok`, `instagram`, `bluesky`, `threads`, `pinterest`, `truthsocial`, `github`, `hackernews`, `polymarket`, `grounding`. Availability depends on installed local backends, login state, and platform access.

Foreign fields:

- `topic`: Human-readable task label or broad query.
- `platforms`: String or list of foreign platform codes.
- `start_date`, `end_date`: Inclusive `YYYY-MM-DD` range.
- `keywords`: One keyword group.
- `subject_terms`, `issue_terms`: Two groups for double-hit filtering.
- `match_mode`: `auto`, `any`, `all`, or `double-hit`.
- `foreign_mode`: `fallback-only`, `hybrid`, or `last30days`. Default is `fallback-only`.
- `max_results_per_platform`: Requested fallback rows per query and source; upstream platforms may return fewer.
- `drop_undated`: Drop rows without a parseable date when a date range is set.
- `deep_crawl`: Expand comments/replies for supported X, Reddit, and YouTube backends.
- `deep_targets_per_source`, `deep_comments_per_item`, `deep_reply_depth`: Deep-crawl controls.
- `last30days_script`: Optional explicit path to `last30days.py`.
- `output`, `output_dir`: Optional paths. Otherwise the runner creates `raw/foreign_sources.xlsx` and retains raw JSON/logs.

Double-hit example:

```json
{
  "collector": "foreign",
  "topic": "India travel to China",
  "platforms": ["x", "youtube", "reddit"],
  "start_date": "2026-06-01",
  "end_date": "2026-06-30",
  "subject_terms": ["India", "Indian tourists", "Indian students"],
  "issue_terms": ["China", "visa", "travel"],
  "match_mode": "double-hit",
  "foreign_mode": "hybrid"
}
```

## Shared Fields

- `mediaspider_home` or legacy `media_crawler_home`: Optional engine path. Prefer `MEDIASPIDER_HOME`.
- `run_dir`: Optional run directory. If omitted, the runner creates a timestamped directory beside the task file.
- Do not mix domestic and foreign platforms in one task file. Use two task files and merge their outputs downstream.

Each run contains `task.resolved.json`, `command.txt`, `run.log`, a `raw/` directory, and `inspection.json` after inspection.
