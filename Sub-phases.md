Sub-phases

 Phase 4a — Implement agent/scorer.py

 Create the scoring module with the full prompt from the spec.

 Key decisions:
 - Field mapping: current articles use source_name, spec uses source → map in prompt construction
 - Model: claude-sonnet-4-5 (spec choice — more capable than haiku for editorial judgment)
 - Input cap: truncate summary to 300 chars per article to stay within context limits
 - Short IDs: generate 8-char UUIDs for the prompt, map back to full articles after

 Functions to implement:
 1. score_articles(articles: list[dict], now: datetime) -> list[dict]
   - Builds prompt with all articles (up to 20)
   - Calls Claude with system + user prompt from spec
   - Parses JSON response, reconstructs full article dicts with scoring metadata
   - Adds fields: scores, total_score, reasoning, cluster_sources
 2. score_with_retry(articles: list[dict], now: datetime, max_retries: int = 3) -> list[dict]
   - Wraps score_articles with retry + exponential backoff on JSONDecodeError/KeyError

 Files: agent/scorer.py (new)

 ---
 Phase 4b — Supabase article_scores table + persistence

 Create the scoring observability table and a function to persist results.

 1. SQL migration — create article_scores table per spec schema
 2. Persistence function in agent/scorer.py:
   - save_scores(sb_client, scored: list[dict], rejected: list[dict], run_at: datetime)
   - Insert both selected (selected=true) and rejected (selected=false) articles
   - Only runs if Supabase client is available (graceful skip in legacy mode)

 Files: agent/scorer.py (extend), Supabase dashboard (manual SQL)

 ---
 Phase 4c — Integrate scorer into main.py pipeline

 Update both run_legacy() and run_per_user() to use the scorer.

 Pipeline change:
 Before: fetch → filter_recent → deduplicate → limit_per_category → summarize → publish
 After:  fetch → filter_recent → deduplicate → score (top 5) → summarize → publish

 Specific changes:
 - Replace limit_per_category() call with score_with_retry() call
 - Cap deduplicated articles at 20 (add max_total param or slice)
 - Pass scored articles to summarize_digest() (works as-is — it groups by category)
 - Optionally save scores to Supabase after scoring step
 - Fallback: if scorer fails after retries, fall back to limit_per_category() so the digest still sends

 Files: main.py

 ---
 Verification

 1. Unit test scorer prompt construction — ensure field mapping is correct
 2. Run python main.py --skip-summarize — verify scorer logs scores and selects 5 articles
 3. Full run python main.py — verify end-to-end: scoring → summarization → publish
 4. Check Supabase — verify article_scores rows are inserted with correct data
 5. Review reasoning field — confirm Claude provides meaningful one-sentence explanations

 ---
 Out of scope

 - Shadow mode (operational, not a code concern for initial implementation)
 - Per-user scoring weights
 - Prompt tuning (iterative, post-launch)