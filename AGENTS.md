# Agents

Project-level context for AI coding agents working on this codebase.

## Tooling

- **Package manager:** [uv](https://docs.astral.sh/uv/)
- **Python version:** 3.11
- **Run commands with:** `uv run <command>` (e.g. `uv run python main.py`)
- **Add dependencies:** `uv add <package>`
- **No lock file committed** — `uv.lock` is not tracked

## Project structure

```
news-agent/
├── agent/           # Core pipeline modules
│   ├── fetcher.py   # RSS feed fetching & date parsing
│   ├── filter.py    # Deduplication & category limiting
│   ├── scorer.py    # Claude-powered article scoring (top 5 selection)
│   ├── summarizer.py# Claude article summarization
│   ├── publisher.py # Slack & email delivery
│   └── sources.py   # Source registry (hardcoded source dicts)
├── web/             # Next.js frontend (Supabase auth, dashboard)
├── migrations/      # SQL migrations (run manually in Supabase SQL editor)
├── main.py          # CLI entrypoint (legacy & per-user modes)
├── sources.yaml     # RSS feed sources config
└── pyproject.toml   # Project metadata & dependencies
```

## Pipeline

```
fetch → filter_recent → deduplicate → score (top 5) → summarize → publish
```

- **Legacy mode** (no `SUPABASE_URL`): reads `sources.yaml`, publishes to Slack webhook from env
- **Per-user mode** (`SUPABASE_URL` set): fetches subscriptions from Supabase, delivers personalized digests via Slack or email

## Testing

- **Framework:** pytest (`uv run pytest`)
- **Tests live in:** `tests/`
- When verifying behavior (field mappings, data transformations, edge cases), write small unit tests rather than just eyeballing it
- Tests should mock external services (Anthropic API, Supabase) — no real API calls in tests

## Key conventions

- All agent modules live in `agent/` and are imported by `main.py`
- Article dicts flow through the pipeline with keys: `title`, `url`, `summary`, `published`, `category`, `source_name`
- Scorer adds: `scores`, `total_score`, `reasoning`, `cluster_sources`
- Summarizer adds: `ai_summary`
- Config via environment variables (loaded from `.env` with `python-dotenv`)
- Supabase interactions use the `supabase-py` client with service role key
