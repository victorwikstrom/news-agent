# Phase 4 — Sophisticated Article Scoring

Replace the current "take first 5 articles" logic with a single, well-engineered Claude call that scores all 20 articles at once and selects the 5 most newsworthy based on a transparent, consistent set of editorial criteria.

---

## What Changes

| Area | Before | After |
|---|---|---|
| Selection | First 5 fetched articles | Top 5 scored from 20 |
| Deduplication | Simple URL/title match | Semantic story clustering in scoring prompt |
| Scoring | None | Multi-factor with explicit weights |
| Transparency | None | Score + reasoning stored per article |
| Prompt | One summarization prompt | Two prompts: score → summarize |

---

## Architecture

The agent pipeline gets a new step between `filter` and `summarize`:

```
fetch (20 articles)
  → filter (deduplicate by URL/title)
  → score  ← NEW: Claude ranks and selects top 5
  → summarize (Claude summarizes the 5 winners)
  → publish (Slack)
```

A new file `agent/scorer.py` owns the scoring logic entirely.

---

## Scoring Criteria

Five factors, each contributing to a total score of 100:

| Factor | Weight | Description |
|---|---|---|
| **Cross-source corroboration** | 30 pts | How many sources cover this story? More = higher signal |
| **Recency** | 25 pts | Decayed score based on hours since publication |
| **Impact & scope** | 25 pts | Geographic/social breadth — local event vs global consequence |
| **Novelty** | 10 pts | Is this genuinely new information, or a follow-up/opinion? |
| **Source authority** | 10 pts | Wire services and established outlets score higher than blogs |

**Why these weights:**
- Corroboration is the strongest objective signal available without user data
- Recency matters but shouldn't punish genuinely important slow-burning stories
- Impact/scope and novelty require Claude's judgment — this is where LLM reasoning adds real value over simple heuristics
- Source authority is a tiebreaker, not a dominant factor

---

## Scoring Prompt Design

The prompt sends all 20 articles in a single call and asks for structured JSON output.

### System prompt

```
You are a senior news editor with 20 years of experience at an international wire service.
Your job is to review a batch of articles and select the 5 most newsworthy stories of the day.

You evaluate each article on five criteria:
1. Cross-source corroboration (0-30): How many sources in this batch cover the same story?
   Multiple sources reporting the same event is a strong signal of importance.
2. Recency (0-25): How recently was this published? Apply a decay curve — stories under
   6 hours old score highest, 6-12 hours medium, 12-24 hours lower.
3. Impact & scope (0-25): What is the real-world significance? Local incident = low,
   national policy = medium, global consequence = high.
4. Novelty (0-10): Is this genuinely new information? Breaking news and exclusives score
   higher than opinion pieces, analysis, or follow-ups to yesterday's stories.
5. Source authority (0-10): Wire services (Reuters, AP, AFP) and major national broadcasters
   score highest. Niche blogs or aggregators score lowest.

Rules:
- Identify story clusters first: group articles covering the same event before scoring.
  Score the cluster as one story, using the highest-authority source as the representative.
- Select exactly 5 stories. Return them ordered by total score, highest first.
- Be ruthless: a slow news day still only gets 5 stories.
- Do not let recency override genuine importance. A major geopolitical development from
  18 hours ago outranks a minor local story from 1 hour ago.

Respond only with valid JSON. No preamble, no explanation outside the JSON structure.
```

### User prompt

```
Today is {date}. Current time: {time} ({timezone}).

Review these {n} articles and return your top 5:

{articles_json}

Return this exact structure:
{
  "selected": [
    {
      "article_id": "string",
      "representative_source": "string",
      "cluster_sources": ["source1", "source2"],
      "scores": {
        "corroboration": 0-30,
        "recency": 0-25,
        "impact": 0-25,
        "novelty": 0-10,
        "authority": 0-10
      },
      "total": 0-100,
      "reasoning": "One sentence explaining why this story matters today."
    }
  ],
  "rejected_count": 15,
  "scoring_notes": "Optional: anything unusual about this batch."
}
```

### Article format in the prompt

Keep each article compact to stay within context limits:

```json
[
  {
    "id": "uuid-short",
    "title": "Riksbank cuts interest rate by 0.25 points",
    "source": "SVT Nyheter",
    "category": "business",
    "published_iso": "2026-03-16T06:30:00Z",
    "summary": "The Riksbank announced a quarter-point rate cut...",
    "url": "https://svt.se/..."
  }
]
```

---

## Implementation — `agent/scorer.py`

```python
import json
import uuid
from datetime import datetime, timezone
from anthropic import Anthropic

client = Anthropic()

SYSTEM_PROMPT = """..."""  # Full prompt above

def score_articles(articles: list[dict], now: datetime) -> list[dict]:
    """
    Takes up to 20 articles, returns the top 5 scored and ordered.
    Each returned article has additional keys: scores, total, reasoning.
    """
    # Assign short IDs for the prompt (avoid sending full UUIDs)
    id_map = {}
    prompt_articles = []
    for article in articles:
        short_id = str(uuid.uuid4())[:8]
        id_map[short_id] = article
        prompt_articles.append({
            "id": short_id,
            "title": article["title"],
            "source": article["source"],
            "category": article["category"],
            "published_iso": article["published"].isoformat(),
            "summary": article.get("summary", "")[:300],  # cap length
            "url": article["url"]
        })

    user_prompt = f"""
Today is {now.strftime('%A, %d %B %Y')}. Current time: {now.strftime('%H:%M')} UTC.

Review these {len(prompt_articles)} articles and return your top 5:

{json.dumps(prompt_articles, ensure_ascii=False, indent=2)}
"""

    response = client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=1500,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_prompt}]
    )

    raw = response.content[0].text
    result = json.loads(raw)

    # Reconstruct full article objects with scoring metadata
    scored = []
    for item in result["selected"]:
        article = id_map[item["article_id"]].copy()
        article["scores"] = item["scores"]
        article["total_score"] = item["total"]
        article["reasoning"] = item["reasoning"]
        article["cluster_sources"] = item["cluster_sources"]
        scored.append(article)

    return scored


def score_with_retry(articles: list[dict], now: datetime, max_retries: int = 3) -> list[dict]:
    """Wrap score_articles with retry + exponential backoff on failure."""
    import time
    for attempt in range(max_retries):
        try:
            return score_articles(articles, now)
        except (json.JSONDecodeError, KeyError) as e:
            if attempt == max_retries - 1:
                raise
            time.sleep(2 ** attempt)
    return []
```

---

## Updated `main.py` Pipeline

```python
from agent.fetcher import fetch_all_sources
from agent.filter import deduplicate
from agent.scorer import score_with_retry
from agent.summarizer import summarize_articles
from agent.publisher import publish_to_slack
from datetime import datetime, timezone

def run_digest(user: dict):
    now = datetime.now(timezone.utc)

    # 1. Fetch up to 20 articles from user's sources
    raw = fetch_all_sources(user["sources"], max_per_source=4)

    # 2. Deduplicate by URL and near-identical titles
    articles = deduplicate(raw, max_total=20)

    if not articles:
        log.warning(f"No articles found for user {user['id']}")
        return

    # 3. Score and select top 5
    top5 = score_with_retry(articles, now)

    # 4. Summarize the winners
    summaries = summarize_articles(top5)

    # 5. Publish
    publish_to_slack(user["slack_webhook_url"], summaries, now)
```

---

## Storing Scores in Supabase

Store scoring results for observability — useful for debugging and future analysis.

```sql
create table article_scores (
  id uuid primary key default gen_random_uuid(),
  run_at timestamptz not null,
  article_url text not null,
  article_title text not null,
  source text not null,
  score_corroboration int,
  score_recency int,
  score_impact int,
  score_novelty int,
  score_authority int,
  score_total int,
  reasoning text,
  cluster_sources text[],
  selected boolean not null
);
```

This table lets you:
- Inspect why an article was or wasn't selected on any given day
- Spot patterns in what scores well over time
- Tune the prompt criteria based on real data

---

## Prompt Tuning Process

The scoring prompt will need iteration. Recommended process:

1. **Run silently first** — for the first week, run the scorer but still send the old top-5. Log both sets. Compare.
2. **Review the `reasoning` field** — Claude explains each pick in one sentence. Read these daily for a few days.
3. **Check `scoring_notes`** — Claude flags unusual batches (very slow news day, all articles from one source, etc.)
4. **Tune weights if needed** — if recency is dominating and burying genuinely important older stories, drop it from 25 to 15 and increase impact.

---

## Build Order

1. Implement `agent/scorer.py` with the full prompt
2. Create `article_scores` table in Supabase
3. Update `main.py` pipeline to include scoring step
4. Run in shadow mode for 5–7 days (score but don't change output yet)
5. Review reasoning + scoring_notes logs
6. Tune prompt if needed
7. Switch scorer output to be the live top 5

---

## Out of Scope for This Phase

- Per-user scoring weights
- Slack feedback buttons (deferred from Phase 4 discussions)
- Telegram support
- Trend detection across multiple days
