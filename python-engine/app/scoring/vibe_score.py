"""
vibe_score.py — Community Intelligence Layer
===============================================
Converts individual post sentiment signals into a single community-level metric.
This is the heart of the oracle.
"""

from app.config import ENGAGEMENT_WEIGHT_MULTIPLIER, MIN_SCORE, MAX_SCORE


def compute(posts: list[dict]) -> dict:
    """
    Compute the community vibe score from analyzed posts.

    Algorithm:
      1. Per-post weighted contribution:
           weight = engagement * confidence * ENGAGEMENT_WEIGHT_MULTIPLIER
           signal = polarity_score * weight

      2. Aggregate:
           community_signal = sum(signals) / post_count

      3. Normalize to [-100, +100] and clamp to MIN_SCORE / MAX_SCORE.

    Returns:
        {
            "raw_score": float,
            "post_count": int,
            "positive_count": int,
            "negative_count": int,
        }
    """
    if not posts:
        return {
            "raw_score": 0.0,
            "post_count": 0,
            "positive_count": 0,
            "negative_count": 0,
        }

    signals: list[float] = []
    positive_count = 0
    negative_count = 0

    max_possible_weight = 0.0

    for post in posts:
        sentiment = post["sentiment"]
        engagement = post.get("engagement", 1)
        confidence = sentiment["confidence"]
        polarity = sentiment["polarity_score"]

        weight = engagement * confidence * ENGAGEMENT_WEIGHT_MULTIPLIER
        signal = polarity * weight

        signals.append(signal)

        if polarity > 0:
            positive_count += 1
        else:
            negative_count += 1

        max_possible_weight += weight

    # Aggregate — mean of weighted signals
    community_signal = sum(signals) / len(signals) if signals else 0.0

    # Normalize to [-100, +100]
    # Use the max possible single-post weight as the normalization ceiling
    if max_possible_weight > 0:
        max_single_weight = max_possible_weight / len(signals)
        raw_score = (community_signal / max_single_weight) * 100.0
    else:
        raw_score = 0.0

    # Clamp to guaranteed bounds
    raw_score = max(MIN_SCORE, min(MAX_SCORE, raw_score))
    raw_score = round(raw_score, 2)

    return {
        "raw_score": raw_score,
        "post_count": len(posts),
        "positive_count": positive_count,
        "negative_count": negative_count,
    }
