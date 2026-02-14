"""
aggregator.py — Input Stabilization Layer
============================================
Prevents noisy, bursty ingestion by sorting, truncating, and deduplicating posts.
"""

import hashlib
from app.config import MAX_POSTS


def _text_hash(text: str) -> str:
    """Generate a hash of normalized text for deduplication."""
    normalized = text.strip().lower()
    return hashlib.md5(normalized.encode("utf-8")).hexdigest()


def aggregate(posts: list[dict]) -> list[dict]:
    """
    Stabilize raw post stream:
      1. Sort by engagement (descending)
      2. Deduplicate by text hash
      3. Truncate to MAX_POSTS

    Returns cleaned, bounded list of posts.
    """
    # Step 1 — Sort by engagement (highest first)
    sorted_posts = sorted(posts, key=lambda p: p.get("engagement", 0), reverse=True)

    # Step 2 — Deduplicate
    seen_hashes: set[str] = set()
    unique_posts: list[dict] = []

    for post in sorted_posts:
        h = _text_hash(post.get("text", ""))
        if h not in seen_hashes:
            seen_hashes.add(h)
            unique_posts.append(post)

    # Step 3 — Truncate to MAX_POSTS
    return unique_posts[:MAX_POSTS]
