"""
deduplicator.py — Cross-Cycle Rolling Deduplication Layer
============================================================
Maintains a rolling window of seen post hashes across pipeline cycles.
Prevents the same post from being re-processed in consecutive runs.

Distinct from aggregator.py which handles within-batch dedup only.
This module handles cross-cycle dedup via a persistent hash window.
"""

import hashlib
from collections import deque

from app.config import DEDUP_WINDOW_SIZE, MIN_POST_WORD_COUNT
from app.utils.logger import logger


class RollingDeduplicator:
    """
    Stateful cross-cycle deduplicator using a bounded hash window.

    Uses SHA256 for stronger collision resistance across the larger
    cross-cycle window. (Aggregator uses MD5 for within-batch dedup,
    which is sufficient for small batches.)
    """

    def __init__(self, window_size: int = DEDUP_WINDOW_SIZE):
        self._window_size = window_size
        self._hash_order: deque[str] = deque()
        self._hash_set: set[str] = set()

    @staticmethod
    def _compute_hash(text: str) -> str:
        """SHA256 hash of normalized text."""
        normalized = text.strip().lower()
        return hashlib.sha256(normalized.encode("utf-8")).hexdigest()

    def _evict_oldest(self) -> None:
        """Remove oldest hashes until window size is respected."""
        while len(self._hash_order) > self._window_size:
            oldest = self._hash_order.popleft()
            self._hash_set.discard(oldest)

    def deduplicate(self, posts: list[dict]) -> list[dict]:
        """
        Filter posts against the rolling hash window.

        Drops:
          - Posts with text shorter than MIN_POST_WORD_COUNT (coarse pre-filter)
          - Posts whose text hash already exists in the window

        Surviving posts are added to the window for future cycles.
        """
        result = []

        for post in posts:
            text = post.get("text", "")

            # Coarse word count pre-filter (cleaner applies authoritative filter later)
            if len(text.split()) < MIN_POST_WORD_COUNT:
                continue

            text_hash = self._compute_hash(text)

            if text_hash in self._hash_set:
                continue

            # New post — track and keep
            self._hash_order.append(text_hash)
            self._hash_set.add(text_hash)
            result.append(post)

        self._evict_oldest()

        dropped = len(posts) - len(result)
        if dropped > 0:
            logger.info(f"Deduplicator: {len(posts)} in, {len(result)} out, {dropped} dropped")

        return result

    @property
    def window_size(self) -> int:
        """Current number of hashes in the window."""
        return len(self._hash_set)


# ── Global singleton ────────────────────────────────────────
_deduplicator = RollingDeduplicator()


def deduplicate(posts: list[dict]) -> list[dict]:
    """Apply cross-cycle deduplication using the global deduplicator."""
    return _deduplicator.deduplicate(posts)


def get_deduplicator() -> RollingDeduplicator:
    """Return the global deduplicator for inspection/testing."""
    return _deduplicator
