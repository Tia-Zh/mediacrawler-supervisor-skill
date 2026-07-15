# Troubleshooting

## MediaSpider Not Found

Run:

```powershell
scripts\doctor.ps1
```

If missing, ask the user before installing:

```powershell
scripts\bootstrap.ps1
```

By default, `bootstrap.ps1` installs MediaSpider, an adapted distribution based on MediaCrawler:

```text
https://github.com/Tia-Zh/MediaSpider.git
```

The default ref is `mediaspider-v0.3.0`. It includes the domestic stability fixes plus the official foreign-source collection entrypoint and Excel export.

Use `-RepoUrl` only when the user explicitly wants another engine source. The user must review the inherited MediaCrawler license and the target platforms' terms before collection.

## Missing Cleanup Patch

If `doctor.ps1` reports that the cleanup patch is missing, run:

```powershell
scripts\bootstrap.ps1
```

If the existing collector directory has local changes, bootstrap will not overwrite it automatically. Review or back up those changes, then update to the adapted ref manually.

## Dry Run Versus Real Success

A dry-run proves only that the task can be converted into a command. Real success requires at least one non-empty raw output file. `run_task.py` returns a failure status when login is required or the task exits without output.

## Proxy Failure

If the browser reports `ERR_PROXY_CONNECTION_FAILED`, check whether Windows proxy is enabled while its local proxy port is closed. Do not hardcode `--no-proxy-server` into every platform; correct the system proxy or task environment consistently so browser and API requests use the same network path.

## Dependency Failure

- Check `uv --version`.
- Run `uv sync` from the MediaCrawler directory.
- If browser automation fails in non-CDP mode, run `uv run playwright install`.
- Some platforms require Node.js; check `node --version`.

## Login Or Captcha

- Use visible mode: `headless: false`.
- Let the user scan QR codes or complete verification manually.
- Do not automate captcha solving.
- If verification repeats, pause and summarize the blocker.

## Empty Output

Check:

- Is the account logged in?
- Are keywords too narrow or in the wrong language?
- Is the platform suitable for the topic?
- Did output save to a different directory?
- Did the run exit early? Read `run.log`.

Recommended response:

1. Inspect `run.log`.
2. Inspect output with `inspect_outputs.py`.
3. Try one smaller alternative keyword group.
4. Stop after repeated empty results and report the likely cause.

For foreign tasks, also check which backend serves the requested platform. A workbook with zero rows in `采集概览` is an empty result, not a successful collection. Try `foreign_mode: "fallback-only"` first; use `hybrid` only when last30days is available.

## Too Few Posts But Many Comments

This can be a successful signal for comment-focused tasks. Do not force more posts automatically. Explain the tradeoff and switch to:

- fewer, more relevant posts
- higher `max_comments_per_post`
- optional detail mode for selected high-comment posts

## Too Many Duplicates

- Reduce overlapping keywords.
- Split runs by keyword group and dedupe later.
- Prefer IDs/detail mode once seed posts are found.

## Run Package Looks Incomplete

Expected files:

- `task.resolved.json`
- `command.txt`
- `run.log`
- `raw/` or a configured output directory
- `inspection.json` after inspection

If `inspection.json` is missing, run:

```bash
python scripts/inspect_outputs.py <run-dir>
```
