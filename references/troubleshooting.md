# Troubleshooting

## MediaCrawler Not Found

Run:

```powershell
scripts\doctor.ps1
```

If missing, ask the user before installing:

```powershell
scripts\bootstrap.ps1
```

The user must review MediaCrawler's license and the target platforms' terms before collection.

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
