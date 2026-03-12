import logging
import os

from dotenv import load_dotenv

from agent.fetcher import fetch_all_feeds, filter_recent, load_sources
from agent.filter import deduplicate, limit_per_category
from agent.publisher import publish_to_slack
from agent.summarizer import summarize_digest

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

    articles = deduplicate(articles)
    articles = limit_per_category(articles)
    logger.info(f"{len(articles)} articles after filtering")

    digest = summarize_digest(articles)

    print(f"\n{'='*60}")
    print(f"  {digest['headline']}")
    print(f"{'='*60}")

    for category, items in digest["categories"].items():
        print(f"\n{'─'*60}")
        print(f"  {category} ({len(items)} articles)")
        print(f"{'─'*60}")
        for a in items:
            pub = a["published"].strftime("%Y-%m-%d %H:%M") if a["published"] else "unknown"
            print(f"\n  {a['title']}")
            print(f"  Source: {a['source_name']} | Published: {pub}")
            if a.get("ai_summary"):
                print(f"  {a['ai_summary']}")
            print(f"  {a['url']}")

    if publish_to_slack(digest):
        logger.info("Digest delivered to Slack")
    else:
        logger.warning("Slack delivery skipped or failed")


if __name__ == "__main__":
    main()
