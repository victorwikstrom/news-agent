import logging
import time
from collections import defaultdict

import anthropic

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = (
    "You are a news editor writing daily briefings.\n"
    "Summarize the article in 2–3 sentences in English.\n"
    "Be factual, concise, and informative.\n"
    "Avoid passive voice. No filler phrases.\n"
    "If the article is not newsworthy, respond with: SKIP"
)


def summarize_article(client: anthropic.Anthropic, article: dict) -> str | None:
    user_message = (
        f"Title: {article['title']}\n"
        f"Source: {article['source_name']}\n"
        f"Summary: {article['summary']}"
    )

    for attempt in range(3):
        try:
            response = client.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=256,
                system=SYSTEM_PROMPT,
                messages=[{"role": "user", "content": user_message}],
            )
            text = response.content[0].text.strip()
            if text == "SKIP":
                logger.debug(f"Claude skipped: {article['title']}")
                return None
            return text
        except Exception as e:
            wait = 2 ** attempt
            logger.warning(f"API error summarizing '{article['title']}' (attempt {attempt + 1}/3): {e}")
            if attempt < 2:
                time.sleep(wait)

    logger.warning(f"All retries failed for '{article['title']}', using RSS summary")
    return article["summary"] or None


def generate_digest_headline(client: anthropic.Anthropic, categories: dict[str, list[dict]]) -> str:
    lines = []
    for category, articles in categories.items():
        titles = ", ".join(a["title"] for a in articles[:5])
        lines.append(f"{category}: {titles}")
    overview = "\n".join(lines)

    try:
        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=100,
            system="You write short, punchy news digest headlines. Respond with a single one-line headline.",
            messages=[{"role": "user", "content": f"Write a headline for today's news digest:\n\n{overview}"}],
        )
        return response.content[0].text.strip()
    except Exception as e:
        logger.warning(f"Failed to generate headline: {e}")
        return "Today's News Digest"


def summarize_digest(articles: list[dict]) -> dict:
    client = anthropic.Anthropic()

    categories: dict[str, list[dict]] = defaultdict(list)
    for article in articles:
        categories[article["category"]].append(article)

    for category, items in categories.items():
        for article in items:
            logger.info(f"Summarizing: {article['title']}")
            article["ai_summary"] = summarize_article(client, article)

    headline = generate_digest_headline(client, categories)

    return {"headline": headline, "categories": dict(categories)}
