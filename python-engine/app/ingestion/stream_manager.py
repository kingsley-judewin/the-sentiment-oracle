"""
stream_manager.py — Rate Limiting and Stability Layer
========================================================
Tracks fetch timing per source and caches last results.
Prevents excessive RSS requests and ensures the pipeline
always has data to work with, even during cooldown windows.
"""

import time
from typing import Callable

from app.config import RSS_FETCH_INTERVAL
from app.utils.logger import logger


class StreamManager:
    """
    Rate-limited data source manager with result caching.

    Tracks last fetch time per named source.
    During cooldown, returns cached results from last successful fetch.
    """

    def __init__(self, fetch_interval: float = RSS_FETCH_INTERVAL):
        self._fetch_interval = fetch_interval
        self._last_fetch_time: dict[str, float] = {}
        self._cache: dict[str, list[dict]] = {}

    def fetch(
        self,
        source_name: str,
        fetch_fn: Callable[[], list[dict]],
    ) -> list[dict]:
        """
        Execute fetch_fn if cooldown has elapsed, otherwise return cached results.

        Args:
            source_name: Unique identifier (e.g. "reddit", "twitter")
            fetch_fn:    Zero-argument callable returning list[dict]

        Returns:
            List of post dicts (fresh or cached).
        """
        now = time.monotonic()
        last_time = self._last_fetch_time.get(source_name, 0.0)
        elapsed = now - last_time

        if elapsed >= self._fetch_interval:
            try:
                results = fetch_fn()
                self._cache[source_name] = results
                self._last_fetch_time[source_name] = now
                logger.info(
                    f"StreamManager: fresh fetch for '{source_name}' "
                    f"({len(results)} posts)"
                )
                return results
            except Exception as e:
                logger.warning(
                    f"StreamManager: fetch failed for '{source_name}': {e}"
                )
                # Fall through to cached results
        else:
            remaining = self._fetch_interval - elapsed
            logger.info(
                f"StreamManager: '{source_name}' on cooldown "
                f"({remaining:.1f}s remaining), using cache"
            )

        return self._cache.get(source_name, [])


# ── Global singleton ────────────────────────────────────────
_stream_manager = StreamManager()


def managed_fetch(
    source_name: str,
    fetch_fn: Callable[[], list[dict]],
) -> list[dict]:
    """Fetch from a named source with rate limiting and caching."""
    return _stream_manager.fetch(source_name, fetch_fn)


def get_stream_manager() -> StreamManager:
    """Return the global stream manager for inspection/testing."""
    return _stream_manager
