"""
source_router.py — Multi-Source Ingestion Orchestrator (Production-Grade)
============================================================================
Routes post ingestion to the appropriate source(s) based on
INGESTION_MODE config. Provides the single entry point get_posts()
that replaces mock_stream.fetch_posts() in the pipeline.

Production Features:
  - Metrics tracking for all fetch operations
  - Detailed source distribution stats in hybrid mode
  - Graceful fallback on unknown modes
"""

import time
from app.config import INGESTION_MODE
from app.ingestion.deduplicator import deduplicate
from app.ingestion.stream_manager import managed_fetch
from app.monitoring import record_fetch, record_dedup, record_cycle
from app.utils.logger import logger


def _timed_fetch(source_name: str, fetch_fn) -> tuple[list[dict], bool]:
    """
    Execute fetch with timing and metrics recording.

    Returns:
        Tuple of (posts, is_fresh).
    """
    start_time = time.perf_counter()

    try:
        posts, is_fresh = fetch_fn()
        latency_ms = (time.perf_counter() - start_time) * 1000
        record_fetch(source_name, True, len(posts), latency_ms)
        return posts, is_fresh
    except Exception as e:
        latency_ms = (time.perf_counter() - start_time) * 1000
        error = str(e)
        record_fetch(source_name, False, 0, latency_ms, error)
        logger.error(f"Fetch failed for {source_name}: {error}")
        return [], True


def get_posts() -> list[dict]:
    """
    Fetch posts from configured source(s), deduplicate across cycles,
    and return standardized post list for the pipeline.

    Ingestion modes:
        "mock"    — Use existing mock_stream (testing/development)
        "rss"     — Reddit RSS feeds only
        "twitter" — Sentiment140 CSV sampling only
        "hybrid"  — Both RSS and Twitter, merged and deduplicated

    Returns:
        list[dict] matching schema: {id, text, engagement, timestamp, author, source}
    """
    mode = INGESTION_MODE.lower()
    posts: list[dict] = []
    any_fresh = False
    source_stats = {}

    if mode == "mock":
        from app.ingestion.mock_stream import fetch_posts
        posts = _timed_fetch("mock", fetch_posts)[0]
        any_fresh = True

    elif mode == "rss":
        from app.ingestion.reddit_rss import fetch_reddit_posts
        posts, any_fresh = _timed_fetch("reddit", lambda: managed_fetch("reddit", fetch_reddit_posts))
        logger.info(f"Source router: RSS mode, {len(posts)} posts")

    elif mode == "twitter":
        from app.ingestion.twitter_dataset import fetch_twitter_posts
        posts, any_fresh = _timed_fetch("twitter", lambda: managed_fetch("twitter", fetch_twitter_posts))
        logger.info(f"Source router: Twitter dataset mode, {len(posts)} posts")

    elif mode == "hybrid":
        from app.ingestion.reddit_rss import fetch_reddit_posts
        from app.ingestion.twitter_dataset import fetch_twitter_posts

        rss_posts, rss_fresh = _timed_fetch("reddit", lambda: managed_fetch("reddit", fetch_reddit_posts))
        twitter_posts, twt_fresh = _timed_fetch("twitter", lambda: managed_fetch("twitter", fetch_twitter_posts))

        posts = rss_posts + twitter_posts
        any_fresh = rss_fresh or twt_fresh

        # Track source distribution
        source_stats = {
            "reddit": len(rss_posts),
            "twitter": len(twitter_posts),
            "total_before_dedup": len(posts),
        }

        logger.info(
            f"Source router: hybrid mode — "
            f"Reddit: {len(rss_posts)}, Twitter: {len(twitter_posts)}, "
            f"Combined: {len(posts)}"
        )

    else:
        logger.warning(
            f"Unknown INGESTION_MODE '{INGESTION_MODE}', falling back to mock"
        )
        from app.ingestion.mock_stream import fetch_posts
        posts = _timed_fetch("mock", fetch_posts)[0]
        any_fresh = True

    # Only dedup fresh data — cached data already passed through dedup before
    if any_fresh:
        before_dedup = len(posts)
        deduplicated = deduplicate(posts)
        collapsed = before_dedup - len(deduplicated)

        if collapsed > 0:
            record_dedup(collapsed)
            logger.info(f"Source router: {collapsed} duplicates removed ({before_dedup} → {len(deduplicated)})")
    else:
        deduplicated = posts
        logger.info("Source router: using cached data, skipping dedup")

    # Record pipeline cycle
    record_cycle()

    # Log final stats
    if source_stats:
        source_stats["after_dedup"] = len(deduplicated)
        logger.info(f"Source distribution: {source_stats}")

    logger.info(f"Source router: returning {len(deduplicated)} posts to pipeline")
    return deduplicated
