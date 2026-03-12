import logging
import os
from collections import defaultdict
from difflib import SequenceMatcher

logger = logging.getLogger(__name__)


def deduplicate(articles: list[dict]) -> list[dict]:
    seen_urls: set[str] = set()
    unique: list[dict] = []

    for article in articles:
        url = article["url"]
        if url in seen_urls:
            logger.debug(f"Dropping exact URL duplicate: {url}")
            continue

        is_fuzzy_dup = False
        for kept in unique:
            if kept["category"] != article["category"]:
                continue
            ratio = SequenceMatcher(None, kept["title"].lower(), article["title"].lower()).ratio()
            if ratio >= 0.75:
                logger.debug(f"Dropping fuzzy duplicate ({ratio:.2f}): {article['title']!r} ~ {kept['title']!r}")
                is_fuzzy_dup = True
                break

        if not is_fuzzy_dup:
            seen_urls.add(url)
            unique.append(article)

    dropped = len(articles) - len(unique)
    if dropped:
        logger.info(f"Deduplication removed {dropped} articles")
    return unique


def limit_per_category(articles: list[dict], max_per_category: int = 5) -> list[dict]:
    limit = int(os.getenv("MAX_ARTICLES_PER_CATEGORY", max_per_category))
    counts: dict[str, int] = defaultdict(int)
    result: list[dict] = []

    for article in articles:
        cat = article["category"]
        if counts[cat] < limit:
            result.append(article)
            counts[cat] += 1

    dropped = len(articles) - len(result)
    if dropped:
        logger.info(f"Category limit ({limit}) removed {dropped} articles")
    return result
