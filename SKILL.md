---
name: mediaspider-supervisor
description: Use when an AI agent needs to install, configure, run, monitor, troubleshoot, or summarize MediaSpider public-data tasks on a local machine, especially for posts or comments from xhs, dy, ks, bili, wb, tieba, or zhihu; use it to turn natural-language collection goals into reproducible tasks, verify real output, detect login or network blockers, adjust strategy, and deliver logs, raw data, inspection metrics, and a collection note.
---

# MediaSpider Supervisor

## Purpose

Use this skill to supervise MediaSpider, an adapted distribution based on MediaCrawler. Convert the user's collection goal into a small, auditable task, check whether the engine is installed, run with conservative limits first, inspect real output, and decide whether to continue, adjust, pause, or summarize.

Do not treat MediaSpider as a fire-and-forget script. Keep the user informed about progress, data quality, limits, and reasons for every strategy change.

## Safety Defaults

- Confirm the task is for lawful, non-commercial research, analysis, or internal review before a first run on a new machine.
- Do not bypass login, captcha, platform access controls, paywalls, or rate limits.
- Prefer small trial runs before large runs: 10-30 posts and 10-50 comments per post unless the user asks otherwise.
- Pause and explain when login, captcha, account risk, repeated empty results, or obvious platform blocking appears.
- Never ask for account passwords. If cookie login is needed, ask the user to provide the cookie locally and avoid printing it.
- Preserve raw outputs and logs. Do not overwrite a previous run directory.

## Workflow

1. **Understand the goal**
   - Extract platform(s), topic, time window, language/region, desired evidence type, and target output.
   - If the request is broad, start with one or two platforms and a trial run.
   - Translate vague goals into keyword groups. Include aliases, event terms, neutral terms, and negative/positive variants when useful.

2. **Check local readiness**
   - Run `scripts/doctor.ps1` on Windows when the user may not have MediaSpider installed.
   - If the collector is missing or the doctor reports a missing compatibility patch, use `scripts/bootstrap.ps1` only after telling the user it will clone/update MediaSpider and that they must review the inherited MediaCrawler license and platform terms.
   - Prefer `MEDIASPIDER_HOME` if set. Keep `PUBLICSCOPE_HOME`, `MEDIACRAWLER_HOME`, and the legacy `MediaCrawler` directory as compatibility fallbacks.

3. **Create a task file**
   - Use the schema in `references/task-schema.md`.
   - Put each run in a timestamped run directory.
   - Use `save_data_option: "jsonl"` for raw analysis-friendly output unless the user needs Excel immediately.
   - Keep `headless: false` for login/captcha-prone platforms unless the user has a stable logged-in browser context.

4. **Run a trial**
   - Use `scripts/run_task.py <task.json> --dry-run` first to show the command.
   - Run the real task only after checking paths, limits, and output directory. A successful dry-run proves only command generation.
   - Watch `run.log` and stop or pause when the run is clearly blocked.

5. **Inspect output**
   - Run `scripts/inspect_outputs.py <run-dir-or-output-dir>`.
   - Report post count, comment count, files found, empty/failed files, duplicate indicators, and whether the sample is enough for the user's goal. Do not report success when no non-empty raw output exists.
   - If the result is weak, choose a specific adjustment rather than simply increasing volume.

6. **Adjust strategy**
   - If posts are few but comments are rich, switch to fewer posts plus deeper comments.
   - If many keywords are empty, expand or replace keywords and keep a record of the change.
   - If duplicates are high, reduce overlapping keywords or switch platform/sort/time window.
   - If content is off-topic, narrow keywords with context terms, exclude ambiguous terms, or ask the user for a seed example.
   - If output is already sufficient, stop and summarize instead of crawling more.

7. **Deliver the run package**
   - Include raw data, task file, command file, run log, inspection JSON, and a short collection note.
   - Explain collection scope, limitations, failure points, and why the final strategy was chosen.

## Scripts

- `scripts/doctor.ps1`: Check local prerequisites and whether MediaSpider exists.
- `scripts/bootstrap.ps1`: Clone or update MediaSpider into a local tools directory. By default it uses `Tia-Zh/MediaSpider` at `mediaspider-v0.2.0`.
- `scripts/run_task.py`: Run a JSON task through MediaSpider with reproducible logs.
- `scripts/inspect_outputs.py`: Inspect raw output files and write collection metrics.

Read `references/task-schema.md` before creating or editing task JSON. Read `references/platform-notes.md` when choosing platform-specific limits. Read `references/troubleshooting.md` when a run fails, stalls, or returns empty data.

## Decision Log

For multi-step runs, maintain a `decision_log.jsonl` in the run directory. Append one JSON object per adjustment:

```json
{"time":"2026-07-01T15:30:00+08:00","observation":"posts are sparse but comments are dense","decision":"reduce post target and increase per-post comments","reason":"the user's goal is comment opinion analysis"}
```

## Final Summary

End with:

- What was collected and from where.
- Key counts and inspection metrics.
- Any blocked platforms, empty keywords, login/captcha events, or rate-limit signs.
- Files the user should inspect next.
- Suggested next run only if it directly improves the user's original goal.
