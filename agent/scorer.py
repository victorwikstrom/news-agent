import json
import logging
import time
import uuid
from datetime import datetime, timezone

import anthropic

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = (
    "You are a senior news editor with 20 years of experience at an international wire service.\n"
    "Your job is to review a batch of articles and select the most newsworthy stories of the day.\n"
    "\n"
    "You evaluate each article on five criteria:\n"
    "1. Cross-source corroboration (0-30): How many sources in this batch cover the same story?\n"
    "   Multiple sources reporting the same event is a strong signal of importance.\n"
    "2. Recency (0-25): How recently was this published? Apply a decay curve — stories under\n"
    "   6 hours old score highest, 6-12 hours medium, 12-24 hours lower.\n"
    "3. Impact & scope (0-25): What is the real-world significance? Local incident = low,\n"
    "   national policy = medium, global consequence = high.\n"
    "4. Novelty (0-10): Is this genuinely new information? Breaking news and exclusives score\n"
    "   higher than opinion pieces, analysis, or follow-ups to yesterday's stories.\n"
    "5. Source authority (0-10): Wire services (Reuters, AP, AFP) and major national broadcasters\n"
    "   score highest. Niche blogs or aggregators score lowest.\n"
    "\n"
    "Rules:\n"
    "- Identify story clusters first: group articles covering the same event before scoring.\n"
    "  Score the cluster as one story, using the highest-authority source as the representative.\n"
    "- Select the number of stories requested. Return them ordered by total score, highest first.\n"
    "- Be ruthless: a slow news day still only gets the requested number of stories.\n"
    "- Do not let recency override genuine importance. A major geopolitical development from\n"
    "  18 hours ago outranks a minor local story from 1 hour ago.\n"
    "\n"
    "Respond only with valid JSON. No preamble, no explanation outside the JSON structure."
)


def _parse_json(text: str) -> dict:
    """Extract and parse JSON from Claude's response, handling markdown fences."""
    import re

    # Try direct parse first
    stripped = text.strip()
    try:
        return json.loads(stripped)
    except json.JSONDecodeError:
        pass

    # Strip markdown code fences
    match = re.search(r"```(?:json)?\s*\n?(.*?)\n?\s*```", stripped, re.DOTALL)
    if match:
        return json.loads(match.group(1).strip())

    # Try to find first { ... last }
    start = stripped.find("{")
    end = stripped.rfind("}")
    if start != -1 and end != -1:
        return json.loads(stripped[start : end + 1])

    raise json.JSONDecodeError("No JSON found in response", stripped, 0)


def _score_category(
    client: anthropic.Anthropic,
    articles: list[dict],
    category: str,
    now: datetime,
    top_n: int = 5,
) -> list[dict]:
    """Score articles within a single category and return the top N."""
    id_map: dict[str, dict] = {}
    prompt_articles = []
    for article in articles:
        short_id = str(uuid.uuid4())[:8]
        id_map[short_id] = article
        prompt_articles.append({
            "id": short_id,
            "title": article["title"],
            "source": article["source_name"],
            "category": article["category"],
            "published_iso": (
                article["published"].isoformat()
                if article.get("published")
                else now.isoformat()
            ),
            "summary": (article.get("summary") or "")[:300],
            "url": article["url"],
        })

    select_n = min(top_n, len(prompt_articles))

    user_prompt = (
        f"Today is {now.strftime('%A, %d %B %Y')}. "
        f"Current time: {now.strftime('%H:%M')} UTC.\n\n"
        f"Category: {category}\n\n"
        f"Review these {len(prompt_articles)} articles and return your top {select_n}:\n\n"
        f"{json.dumps(prompt_articles, ensure_ascii=False, indent=2)}\n\n"
        "Return this exact structure:\n"
        "{\n"
        '  "selected": [\n'
        "    {\n"
        '      "article_id": "string",\n'
        '      "representative_source": "string",\n'
        '      "cluster_sources": ["source1", "source2"],\n'
        '      "scores": {\n'
        '        "corroboration": 0-30,\n'
        '        "recency": 0-25,\n'
        '        "impact": 0-25,\n'
        '        "novelty": 0-10,\n'
        '        "authority": 0-10\n'
        "      },\n"
        '      "total": 0-100,\n'
        '      "reasoning": "One sentence explaining why this story matters today."\n'
        "    }\n"
        "  ],\n"
        f'  "rejected_count": {len(prompt_articles) - select_n},\n'
        '  "scoring_notes": "Optional: anything unusual about this batch."\n'
        "}"
    )

    logger.info(f"Scoring {len(prompt_articles)} articles in '{category}' with Claude")

    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=4096,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_prompt}],
    )

    raw = response.content[0].text if response.content else ""
    if response.stop_reason == "max_tokens":
        logger.warning(f"Scorer response for '{category}' was truncated (max_tokens reached)")
    logger.debug(f"Raw scorer response for '{category}': {raw[:500]}")
    result = _parse_json(raw)

    scored = []
    for item in result["selected"]:
        article = id_map[item["article_id"]].copy()
        article["scores"] = item["scores"]
        article["total_score"] = item["total"]
        article["reasoning"] = item["reasoning"]
        article["cluster_sources"] = item.get("cluster_sources", [])
        scored.append(article)

    for i, s in enumerate(scored, 1):
        logger.info(
            f"  [{category}] #{i} [{s['total_score']}] {s['title']} — {s['reasoning']}"
        )

    if result.get("scoring_notes"):
        logger.info(f"Scoring notes ({category}): {result['scoring_notes']}")

    return scored


def score_articles(articles: list[dict], now: datetime, top_n: int = 5) -> list[dict]:
    """Score articles per category and return the top N from each category."""
    client = anthropic.Anthropic()

    # Group by category
    by_category: dict[str, list[dict]] = {}
    for article in articles:
        by_category.setdefault(article["category"], []).append(article)

    all_scored = []
    for category, cat_articles in by_category.items():
        scored = _score_category(client, cat_articles, category, now, top_n)
        all_scored.extend(scored)

    return all_scored


def score_with_retry(
    articles: list[dict], now: datetime, top_n: int = 5, max_retries: int = 3
) -> list[dict]:
    """Wrap score_articles with retry + exponential backoff on parse failures."""
    for attempt in range(max_retries):
        try:
            return score_articles(articles, now, top_n)
        except (json.JSONDecodeError, KeyError) as e:
            logger.warning(
                f"Scoring attempt {attempt + 1}/{max_retries} failed: {e}"
            )
            if attempt == max_retries - 1:
                raise
            time.sleep(2**attempt)
    return []


def save_scores(
    sb_client,
    scored: list[dict],
    rejected: list[dict],
    run_at: datetime,
) -> None:
    """Persist scoring results to Supabase article_scores table."""
    rows = []

    for article in scored:
        scores = article.get("scores", {})
        rows.append({
            "run_at": run_at.isoformat(),
            "article_url": article["url"],
            "article_title": article["title"],
            "source": article["source_name"],
            "score_corroboration": scores.get("corroboration"),
            "score_recency": scores.get("recency"),
            "score_impact": scores.get("impact"),
            "score_novelty": scores.get("novelty"),
            "score_authority": scores.get("authority"),
            "score_total": article.get("total_score"),
            "reasoning": article.get("reasoning"),
            "cluster_sources": article.get("cluster_sources", []),
            "selected": True,
        })

    for article in rejected:
        rows.append({
            "run_at": run_at.isoformat(),
            "article_url": article["url"],
            "article_title": article["title"],
            "source": article["source_name"],
            "score_corroboration": None,
            "score_recency": None,
            "score_impact": None,
            "score_novelty": None,
            "score_authority": None,
            "score_total": None,
            "reasoning": None,
            "cluster_sources": [],
            "selected": False,
        })

    try:
        sb_client.table("article_scores").insert(rows).execute()
        logger.info(f"Saved {len(rows)} article scores to Supabase")
    except Exception as e:
        logger.warning(f"Failed to save article scores: {e}")
