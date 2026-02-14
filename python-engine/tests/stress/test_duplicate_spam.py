"""
test_duplicate_spam.py — Anti-Spam Deduplication Verification
================================================================
Validates that the aggregator layer prevents spam flood manipulation
by removing duplicate posts.
"""

import pytest
from app.ingestion.aggregator import aggregate
from app.nlp.cleaner import clean_posts
from app.nlp.sentiment import analyze_posts
from app.scoring.vibe_score import compute
from app.scoring.smoothing import Smoother
from app.config import MIN_SCORE, MAX_SCORE


def _make_duplicate_batch(text: str, count: int, engagement: int = 100) -> list[dict]:
    """Create N identical posts (simulating a spam flood)."""
    return [
        {
            "text": text,
            "engagement": engagement,
            "timestamp": "2025-01-01T00:00:00",
            "author": f"spam_bot_{i}",
        }
        for i in range(count)
    ]


class TestDeduplication:
    def test_50_identical_posts_collapse_to_one(self):
        """50 identical posts should deduplicate to exactly 1."""
        posts = _make_duplicate_batch(
            "This is a spam flood post designed to manipulate the oracle",
            count=50,
        )
        result = aggregate(posts)
        assert len(result) == 1

    def test_100_identical_collapse(self):
        """Even 100 duplicates should collapse."""
        posts = _make_duplicate_batch(
            "Another spam flood attempting to skew the sentiment score badly",
            count=100,
        )
        result = aggregate(posts)
        assert len(result) == 1

    def test_case_insensitive_dedup(self):
        """Duplicates that differ only in case should be caught."""
        posts = [
            {"text": "This post is a duplicate test for case sensitivity", "engagement": 100, "timestamp": "t", "author": "a"},
            {"text": "this post is a duplicate test for case sensitivity", "engagement": 100, "timestamp": "t", "author": "b"},
            {"text": "THIS POST IS A DUPLICATE TEST FOR CASE SENSITIVITY", "engagement": 100, "timestamp": "t", "author": "c"},
        ]
        result = aggregate(posts)
        assert len(result) == 1

    def test_whitespace_variant_dedup(self):
        """Posts with extra whitespace should be treated as the same."""
        posts = [
            {"text": "Same text here with normal spacing and content", "engagement": 100, "timestamp": "t", "author": "a"},
            {"text": "  Same text here with normal spacing and content  ", "engagement": 100, "timestamp": "t", "author": "b"},
        ]
        result = aggregate(posts)
        assert len(result) == 1


class TestSpamFloodResistance:
    def test_spam_flood_cannot_manipulate_score(self, mock_model):
        """
        50 identical negative posts should not produce a more extreme
        score than a single instance of that same post.
        """
        single_text = "This project is the worst scam ever and everyone should avoid it now"

        # Single post pipeline
        single_post = _make_duplicate_batch(single_text, count=1, engagement=200)
        single_agg = aggregate(single_post)
        single_cleaned = clean_posts(single_agg)
        single_analyzed = analyze_posts(single_cleaned)
        single_score = compute(single_analyzed)

        # Spam flood pipeline
        flood_posts = _make_duplicate_batch(single_text, count=50, engagement=200)
        flood_agg = aggregate(flood_posts)
        flood_cleaned = clean_posts(flood_agg)
        flood_analyzed = analyze_posts(flood_cleaned)
        flood_score = compute(flood_analyzed)

        # After dedup, they should produce the SAME score
        assert single_score["raw_score"] == flood_score["raw_score"], \
            "Spam flood should NOT amplify the score"

    def test_mixed_spam_and_legitimate(self, mock_model):
        """Spam duplicates mixed with real posts shouldn't drown out legitimate voices."""
        spam = _make_duplicate_batch(
            "This token is going to zero and everyone will lose money today",
            count=30, engagement=50,
        )
        legitimate = [
            {"text": "The project fundamentals look strong and the team is building", "engagement": 200, "timestamp": "t", "author": "legit_1"},
            {"text": "Great development progress this quarter with solid milestones hit", "engagement": 300, "timestamp": "t", "author": "legit_2"},
            {"text": "Partnership announcements have been impressive and very promising", "engagement": 250, "timestamp": "t", "author": "legit_3"},
        ]

        combined = spam + legitimate
        aggregated = aggregate(combined)

        # The 30 spam duplicates should collapse to 1
        # So we should have 4 posts max (1 spam + 3 legit)
        assert len(aggregated) <= 4


class TestDedupPreservesHighEngagement:
    def test_highest_engagement_copy_kept(self):
        """When duplicates exist, the highest-engagement one should survive."""
        posts = [
            {"text": "Duplicate post content for dedup engagement test", "engagement": 10, "timestamp": "t", "author": "low"},
            {"text": "Duplicate post content for dedup engagement test", "engagement": 500, "timestamp": "t", "author": "high"},
            {"text": "Duplicate post content for dedup engagement test", "engagement": 50, "timestamp": "t", "author": "mid"},
        ]
        result = aggregate(posts)
        assert len(result) == 1
        # Aggregator sorts by engagement first, so highest should be kept
        assert result[0]["engagement"] == 500
