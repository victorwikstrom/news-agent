import argparse
import logging
import os

from dotenv import load_dotenv

from agent.fetcher import fetch_all_feeds, filter_recent, load_sources
from agent.filter import deduplicate, limit_per_category
from agent.publisher import publish_to_slack, send_email
from agent.sources import get_sources_for_ids
from agent.summarizer import summarize_digest

load_dotenv()

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


def run_legacy(skip_summarize: bool = False):
    """Original standalone mode: read sources.yaml, publish to env webhook."""
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

    digest = _build_stub_digest(articles) if skip_summarize else summarize_digest(articles)
    _print_digest(digest)

    if publish_to_slack(digest):
        logger.info("Digest delivered to Slack")
    else:
        logger.warning("Slack delivery skipped or failed")


def run_per_user(skip_summarize: bool = False):
    """Per-user mode: fetch subscriptions from Supabase, deliver personalized digests."""
    from supabase import create_client

    supabase_url = os.environ["SUPABASE_URL"]
    supabase_key = os.environ["SUPABASE_SERVICE_ROLE_KEY"]
    sb = create_client(supabase_url, supabase_key)

    subs = sb.table("subscriptions").select("*").execute()
    subscriptions = subs.data

    if not subscriptions:
        logger.info("No subscriptions found, nothing to do")
        return

    logger.info(f"Found {len(subscriptions)} subscription(s)")

    for sub in subscriptions:
        user_id = sub["user_id"]
        channel = sub["channel"]
        logger.info(f"Processing user {user_id} (channel={channel})")

        try:
            # Fetch user's selected sources
            user_sources_resp = (
                sb.table("user_sources")
                .select("source_id")
                .eq("user_id", user_id)
                .execute()
            )
            source_ids = [row["source_id"] for row in user_sources_resp.data]

            if not source_ids:
                logger.warning(f"User {user_id} has no sources selected, skipping")
                continue

            sources = get_sources_for_ids(source_ids)
            if not sources:
                logger.warning(f"User {user_id}: no valid sources resolved, skipping")
                continue

            logger.info(f"User {user_id}: fetching {len(sources)} source(s)")

            # Pipeline: fetch → filter → deduplicate → limit → summarize
            articles = fetch_all_feeds(sources)
            articles = filter_recent(articles, hours=24)

            if not articles:
                logger.warning(f"User {user_id}: no recent articles, skipping")
                continue

            articles = deduplicate(articles)
            articles = limit_per_category(articles)
            logger.info(f"User {user_id}: {len(articles)} articles after filtering")

            digest = _build_stub_digest(articles) if skip_summarize else summarize_digest(articles)

            # Publish via chosen channel
            if channel == "slack":
                webhook_url = sub.get("slack_webhook_url")
                if not webhook_url:
                    logger.error(f"User {user_id}: no Slack webhook URL, skipping")
                    continue
                if publish_to_slack(digest, webhook_url):
                    logger.info(f"User {user_id}: Slack delivery succeeded")
                else:
                    logger.error(f"User {user_id}: Slack delivery failed")
            elif channel == "email":
                email = sub.get("email")
                if not email:
                    logger.error(f"User {user_id}: no email address, skipping")
                    continue
                if send_email(digest, email):
                    logger.info(f"User {user_id}: email delivery succeeded")
                else:
                    logger.error(f"User {user_id}: email delivery failed")
            else:
                logger.warning(f"User {user_id}: unknown channel '{channel}', skipping")

        except Exception:
            logger.exception(f"Error processing user {user_id}, skipping")


def _build_stub_digest(articles: list[dict]) -> dict:
    """Build a digest without calling the summarizer (for testing delivery)."""
    categories: dict[str, list[dict]] = {}
    for a in articles:
        categories.setdefault(a["category"], []).append(a)
    return {"headline": "Test Digest (summarization skipped)", "categories": categories}


def _print_digest(digest: dict):
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


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--skip-summarize", action="store_true", help="Skip AI summarization, use raw articles for testing delivery")
    args = parser.parse_args()

    if args.skip_summarize:
        logger.info("Summarization skipped (--skip-summarize)")

    if os.getenv("SUPABASE_URL"):
        logger.info("SUPABASE_URL detected, running in per-user mode")
        run_per_user(skip_summarize=args.skip_summarize)
    else:
        logger.info("No SUPABASE_URL, running in legacy mode")
        run_legacy(skip_summarize=args.skip_summarize)


if __name__ == "__main__":
    main()
