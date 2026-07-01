# Platform Notes

Use these notes to choose conservative defaults. Platform behavior changes often, so treat them as starting points, not guarantees.

## Common Rules

- Prefer visible browser mode for first login.
- Keep concurrency low.
- Preserve raw JSONL/CSV files before transforming to Excel.
- Avoid repeated large retries with the same account after captcha, block, or suspicious-login signals.

## xhs

- Good for lifestyle, consumer, travel, brand, and public discussion posts.
- Often useful to start with small post counts and deeper comments.
- Login/captcha can appear; keep `headless: false`.
- Use keyword variants and colloquial terms.

## dy

- Good for short-video topics and event reactions.
- Results may be sensitive to login state and search ranking.
- Start with low comments per post and inspect relevance before expanding.

## ks

- Good for regional and broad public-interest topics.
- Search quality can vary by keyword. Use several focused keyword groups.

## bili

- Good for videos, bullet comments where supported, topic explainers, and youth/community discussion.
- Topic-specific IDs may be better than broad search when a known video anchors the conversation.

## wb

- Good for breaking events and public timeline discussion.
- Time windows matter. Narrow by event terms and date when possible.

## tieba

- Good for forum-style long-tail discussion.
- Detail mode can be useful after finding relevant thread IDs.

## zhihu

- Good for Q&A, longer explanations, and opinion reasoning.
- Search may produce fewer but longer items; inspect text quality before increasing volume.

## Strategy Signals

- Few posts, many comments: switch to comment-deepening mode.
- Many posts, few comments: improve keywords or switch platform.
- Empty results across several keywords: broaden language, aliases, or platform.
- High duplicate ratio: reduce overlapping keywords or use detail mode from selected IDs.
- Off-topic results: add context terms and avoid ambiguous single words.
