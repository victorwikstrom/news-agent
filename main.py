import logging
import os
from collections import defaultdict

from dotenv import load_dotenv

from agent.fetcher import fetch_all_feeds, filter_recent, load_sources

load_dotenv()

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


def main():
    sources = load_sources()
    logger.info(f"Loaded {len(sources)} sources")

    articles = fetch_all_feeds(sources)
    logger.info(f"Fetched {len(articles)} total articles")

    articles = filter_recent(articles, hours=24)
    logger.info(f"{len(articles)} articles from the last 24 hours")

    if not articles:
        logger.warning("No recent articles found")
        return

    grouped: dict[str, list[dict]] = defaultdict(list)
    for article in articles:
        grouped[article["category"]].append(article)

    for category, items in grouped.items():
        print(f"\n{'='*60}")
        print(f"  {category} ({len(items)} articles)")
        print(f"{'='*60}")
        for a in items:
            pub = a["published"].strftime("%Y-%m-%d %H:%M") if a["published"] else "unknown"
            print(f"\n  {a['title']}")
            print(f"  Source: {a['source_name']} | Published: {pub}")
            print(f"  {a['url']}")


if __name__ == "__main__":
    main()
