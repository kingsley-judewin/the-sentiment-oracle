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


def _timed_fetch(source_name: str, fetch_fn) -> list[dict]:
    """
    Execute fetch with timing and metrics recording.
    
    Args:
        source_name: Source identifier for metrics
        fetch_fn: Fetch function to call
    
    Returns:
        List of posts (empty on failure)
    """
    start_time = time.perf_counter()
    error = None
    
    try:
        posts = fetch_fn()
        latency_ms = (time.perf_counter() - start_time) * 1000
        record_fetch(source_name, True, len(posts), latency_ms)
        return posts
    except Exception as e:
        latency_ms = (time.perf_counter() - start_time) * 1000
        error = str(e)
        record_fetch(source_name, False, 0, latency_ms, error)
        logger.error(f"Fetch failed for {source_name}: {error}")
        return []


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
    source_stats = {}

    if mode == "mock":
        from app.ingestion.mock_stream import fetch_posts
        posts = _timed_fetch("mock", fetch_posts)
        logger.info(f"Source router: mock mode, {len(posts)} posts")

    elif mode == "rss":
        from app.ingestion.reddit_rss import fetch_reddit_posts
        posts = _timed_fetch("reddit", lambda: managed_fetch("reddit", fetch_reddit_posts))
        logger.info(f"Source router: RSS mode, {len(posts)} posts")

    elif mode == "twitter":
        from app.ingestion.twitter_dataset import fetch_twitter_posts
        posts = _timed_fetch("twitter", lambda: managed_fetch("twitter", fetch_twitter_posts))
        logger.info(f"Source router: Twitter dataset mode, {len(posts)} posts")

    elif mode == "hybrid":
        from app.ingestion.reddit_rss import fetch_reddit_posts
        from app.ingestion.twitter_dataset import fetch_twitter_posts

        rss_posts = _timed_fetch("reddit", lambda: managed_fetch("reddit", fetch_reddit_posts))
        twitter_posts = _timed_fetch("twitter", lambda: managed_fetch("twitter", fetch_twitter_posts))
        
        posts = rss_posts + twitter_posts
        
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
        posts = _timed_fetch("mock", fetch_posts)

    # Apply cross-cycle deduplication
    before_dedup = len(posts)
    deduplicated = deduplicate(posts)
    collapsed = before_dedup - len(deduplicated)
    
    if collapsed > 0:
        record_dedup(collapsed)
        logger.info(f"Source router: {collapsed} duplicates removed ({before_dedup} → {len(deduplicated)})")
    
    # Record pipeline cycle
    record_cycle()
    
    # Log final stats
    if source_stats:
        source_stats["after_dedup"] = len(deduplicated)
        source_stats["duplicates_removed"] = collapsed
        logger.info(f"Source distribution: {source_stats}")
    
    logger.info(f"Source router: returning {len(deduplicated)} posts to pipeline")
    return deduplicated
