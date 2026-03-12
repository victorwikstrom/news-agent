import logging
from datetime import datetime, timezone
from time import mktime

import feedparser
import yaml

logger = logging.getLogger(__name__)


def load_sources(path: str = "sources.yaml") -> list[dict]:
    with open(path) as f:
        data = yaml.safe_load(f)
    return data["sources"]


def fetch_feed(source: dict) -> list[dict]:
    feed = feedparser.parse(source["url"])

    if feed.bozo and not feed.entries:
        raise Exception(f"Failed to parse feed: {feed.bozo_exception}")

    articles = []
    for entry in feed.entries:
        published = _parse_date(entry)
        articles.append(
            {
                "title": entry.get("title", ""),
                "url": entry.get("link", ""),
                "summary": _extract_summary(entry),
                "published": published,
                "category": source["category"],
                "source_name": source["name"],
            }
        )
    return articles


def fetch_all_feeds(sources: list[dict]) -> list[dict]:
    all_articles = []
    for source in sources:
        try:
            logger.info(f"Fetching {source['name']}...")
            articles = fetch_feed(source)
            logger.info(f"  Got {len(articles)} articles")
            all_articles.extend(articles)
        except Exception:
            logger.exception(f"Error fetching {source['name']}, skipping")
    return all_articles


def filter_recent(articles: list[dict], hours: int = 24) -> list[dict]:
    now = datetime.now(timezone.utc)
    result = []
    for article in articles:
        pub = article["published"]
        if pub is None:
            result.append(article)
            continue
        diff = (now - pub).total_seconds()
        if diff <= hours * 3600:
            result.append(article)
    return result


def _parse_date(entry) -> datetime | None:
    parsed = entry.get("published_parsed") or entry.get("updated_parsed")
    if parsed is None:
        return None
    try:
        return datetime.fromtimestamp(mktime(parsed), tz=timezone.utc)
    except Exception:
        return None


def _extract_summary(entry) -> str:
    summary = entry.get("summary", "")
    if not summary:
        content = entry.get("content")
        if content and isinstance(content, list):
            summary = content[0].get("value", "")
    return summary
