"""
reddit_rss.py — Live Reddit RSS Ingestion Layer (Production-Grade)
====================================================================
Fetches new posts from configured subreddits via Reddit's public RSS feeds.
Parses with feedparser and returns standardized post dicts.

Production Features:
  - Recentness-based engagement proxy (no fabricated votes)
  - Anti-spam filters (word count, all-caps, spam phrases)
  - Proper timestamp parsing to UTC datetime
  - ID extraction for deduplication
  - Graceful failure handling (never crashes pipeline)
"""

import feedparser
import requests
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime

from app.config import (
    SUBREDDITS,
    USER_AGENT,
    REDDIT_ENGAGEMENT_BASELINE,
    REDDIT_SPAM_PHRASES,
    MIN_POST_WORD_COUNT,
)
from app.utils.logger import logger


def _parse_timestamp(entry: dict) -> datetime:
    """
    Parse RSS timestamp to UTC datetime.
    
    Tries 'updated' then 'published' fields.
    Returns current UTC time if parsing fails.
    """
    timestamp_str = entry.get("updated", entry.get("published", ""))
    
    if not timestamp_str:
        return datetime.now(timezone.utc)
    
    try:
        # feedparser provides parsed_time as struct_time
        if hasattr(entry, "updated_parsed") and entry.updated_parsed:
            return datetime(*entry.updated_parsed[:6], tzinfo=timezone.utc)
        elif hasattr(entry, "published_parsed") and entry.published_parsed:
            return datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
        
        # Fallback: parse RFC 2822 format manually
        return parsedate_to_datetime(timestamp_str).astimezone(timezone.utc)
    except Exception:
        return datetime.now(timezone.utc)


def _compute_engagement_proxy(post_time: datetime) -> int:
    """
    Compute engagement proxy based on post recentness.
    
    Strategy:
      - Base weight: REDDIT_ENGAGEMENT_BASELINE (10)
      - < 10 minutes old: +15 (total 25)
      - < 30 minutes old: +8 (total 18)
      - Older: base only (10)
    
    This gives live activity importance without fabricating votes.
    """
    now = datetime.now(timezone.utc)
    age_minutes = (now - post_time).total_seconds() / 60
    
    if age_minutes < 10:
        return REDDIT_ENGAGEMENT_BASELINE + 15
    elif age_minutes < 30:
        return REDDIT_ENGAGEMENT_BASELINE + 8
    else:
        return REDDIT_ENGAGEMENT_BASELINE


def _is_spam(title: str) -> bool:
    """
    Apply anti-spam filters to post title.
    
    Rejects:
      - Titles with < MIN_POST_WORD_COUNT words
      - All-caps ratio > 70%
      - Known spam phrases (case-insensitive)
    """
    # Word count filter
    words = title.split()
    if len(words) < MIN_POST_WORD_COUNT:
        return True
    
    # All-caps filter
    if len(title) > 0:
        caps_ratio = sum(1 for c in title if c.isupper()) / len(title)
        if caps_ratio > 0.7:
            return True
    
    # Spam phrase filter
    title_lower = title.lower()
    for phrase in REDDIT_SPAM_PHRASES:
        if phrase.lower() in title_lower:
            return True
    
    return False


def _fetch_subreddit(subreddit: str) -> list[dict]:
    """
    Fetch and parse RSS feed from a single subreddit.

    Returns list of standardized post dicts.
    Never raises — returns [] on any failure.
    """
    url = f"https://www.reddit.com/r/{subreddit}/new.rss"

    try:
        response = requests.get(
            url,
            headers={"User-Agent": USER_AGENT},
            timeout=10,
        )

        if response.status_code != 200:
            logger.warning(f"Reddit RSS r/{subreddit}: HTTP {response.status_code}")
            return []

        feed = feedparser.parse(response.text)
        posts = []
        spam_count = 0

        for entry in feed.entries:
            title = entry.get("title", "").strip()
            if not title:
                continue
            
            # Anti-spam filters
            if _is_spam(title):
                spam_count += 1
                continue
            
            # Parse timestamp
            post_time = _parse_timestamp(entry)
            
            # Compute engagement proxy based on recentness
            engagement = _compute_engagement_proxy(post_time)
            
            # Extract ID (use link as unique identifier)
            post_id = entry.get("id", entry.get("link", ""))

            posts.append({
                "id": post_id,
                "text": title,
                "engagement": engagement,
                "timestamp": post_time.isoformat(),
                "author": entry.get("author", None),
                "source": "reddit",
            })

        if spam_count > 0:
            logger.info(f"Reddit RSS r/{subreddit}: filtered {spam_count} spam posts")
        
        return posts

    except requests.Timeout:
        logger.warning(f"Reddit RSS r/{subreddit}: request timed out")
        return []
    except requests.RequestException as e:
        logger.warning(f"Reddit RSS r/{subreddit}: network error — {e}")
        return []
    except Exception as e:
        logger.warning(f"Reddit RSS r/{subreddit}: unexpected error — {e}")
        return []


def fetch_reddit_posts() -> list[dict]:
    """
    Fetch posts from all configured subreddits.

    Iterates SUBREDDITS, fetches each independently.
    One subreddit failing does not affect others.
    """
    all_posts = []

    for subreddit in SUBREDDITS:
        posts = _fetch_subreddit(subreddit)
        all_posts.extend(posts)

    logger.info(
        f"Reddit RSS: fetched {len(all_posts)} posts "
        f"from {len(SUBREDDITS)} subreddits"
    )
    return all_posts
