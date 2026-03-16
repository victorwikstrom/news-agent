SOURCE_REGISTRY: dict[str, dict] = {
    "svt-nyheter": {"name": "SVT Nyheter", "url": "https://www.svt.se/nyheter/rss.xml", "category": "Sweden"},
    "techcrunch": {"name": "TechCrunch", "url": "https://techcrunch.com/feed/", "category": "Tech"},
    "hacker-news": {"name": "Hacker News", "url": "https://hnrss.org/frontpage", "category": "Tech"},
    "the-verge": {"name": "The Verge", "url": "https://www.theverge.com/rss/index.xml", "category": "Tech"},
    "omni-ekonomi": {"name": "Omni Ekonomi", "url": "https://omni.se/rss", "category": "Economy"},
}


def get_sources_for_ids(source_ids: list[str]) -> list[dict]:
    """Return source configs for the given IDs, skipping unknown ones."""
    sources = []
    for sid in source_ids:
        if sid in SOURCE_REGISTRY:
            sources.append(SOURCE_REGISTRY[sid])
    return sources
