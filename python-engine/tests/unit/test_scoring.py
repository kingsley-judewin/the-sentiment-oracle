"""
test_scoring.py — Community Intelligence Verification
========================================================
Validates the weighted vibe score computation guarantees:
  - Score bounds
  - Engagement weighting
  - Empty input handling
  - Deterministic output
"""

import pytest
from app.scoring.vibe_score import compute
from app.config import MIN_SCORE, MAX_SCORE


# ── Score Bounds ──────────────────────────────────────────────

class TestScoreBounds:
    def test_all_positive_within_bounds(self, make_analyzed_post):
        posts = [make_analyzed_post(f"good post {i}", 500, "POSITIVE", 0.99) for i in range(20)]
        result = compute(posts)
        assert MIN_SCORE <= result["raw_score"] <= MAX_SCORE

    def test_all_negative_within_bounds(self, make_analyzed_post):
        posts = [make_analyzed_post(f"bad post {i}", 500, "NEGATIVE", 0.99) for i in range(20)]
        result = compute(posts)
        assert MIN_SCORE <= result["raw_score"] <= MAX_SCORE

    def test_extreme_engagement_within_bounds(self, make_analyzed_post):
        """Even with absurd engagement, score stays clamped."""
        posts = [make_analyzed_post("viral post", 1_000_000, "POSITIVE", 1.0)]
        result = compute(posts)
        assert MIN_SCORE <= result["raw_score"] <= MAX_SCORE

    def test_score_is_numeric(self, make_analyzed_post):
        posts = [make_analyzed_post("test post here", 100, "POSITIVE", 0.8)]
        result = compute(posts)
        assert isinstance(result["raw_score"], (int, float))


# ── Engagement Weighting ──────────────────────────────────────

class TestEngagementWeighting:
    def test_high_engagement_positive_dominates(self, make_analyzed_post):
        """A high-engagement positive should outweigh low-engagement negatives."""
        posts = [
            make_analyzed_post("amazing viral post", 1000, "POSITIVE", 0.95),
            make_analyzed_post("bad post one", 10, "NEGATIVE", 0.6),
            make_analyzed_post("bad post two", 10, "NEGATIVE", 0.6),
        ]
        result = compute(posts)
        assert result["raw_score"] > 0, "High-engagement positive should push score positive"

    def test_high_engagement_negative_dominates(self, make_analyzed_post):
        """A high-engagement negative should outweigh low-engagement positives."""
        posts = [
            make_analyzed_post("terrible viral post", 1000, "NEGATIVE", 0.95),
            make_analyzed_post("ok post one", 10, "POSITIVE", 0.6),
            make_analyzed_post("ok post two", 10, "POSITIVE", 0.6),
        ]
        result = compute(posts)
        assert result["raw_score"] < 0, "High-engagement negative should push score negative"

    def test_equal_engagement_cancels(self, make_analyzed_post):
        """Equal positive/negative with same engagement should yield near-zero."""
        posts = [
            make_analyzed_post("great post", 100, "POSITIVE", 0.9),
            make_analyzed_post("terrible post", 100, "NEGATIVE", 0.9),
        ]
        result = compute(posts)
        assert abs(result["raw_score"]) < 10, "Balanced input should produce near-zero score"


# ── Empty Input ───────────────────────────────────────────────

class TestEmptyInput:
    def test_no_posts_returns_zero(self):
        result = compute([])
        assert result["raw_score"] == 0.0
        assert result["post_count"] == 0
        assert result["positive_count"] == 0
        assert result["negative_count"] == 0


# ── Count Tracking ────────────────────────────────────────────

class TestCountTracking:
    def test_positive_count(self, make_analyzed_post):
        posts = [
            make_analyzed_post("good one", 100, "POSITIVE", 0.9),
            make_analyzed_post("good two", 100, "POSITIVE", 0.9),
            make_analyzed_post("bad one", 100, "NEGATIVE", 0.9),
        ]
        result = compute(posts)
        assert result["positive_count"] == 2
        assert result["negative_count"] == 1
        assert result["post_count"] == 3

    def test_all_negative_counts(self, make_analyzed_post):
        posts = [make_analyzed_post(f"bad {i}", 50, "NEGATIVE", 0.8) for i in range(5)]
        result = compute(posts)
        assert result["positive_count"] == 0
        assert result["negative_count"] == 5


# ── Determinism ───────────────────────────────────────────────

class TestDeterminism:
    def test_same_input_same_output(self, make_analyzed_post):
        posts = [
            make_analyzed_post("post a", 200, "POSITIVE", 0.85),
            make_analyzed_post("post b", 150, "NEGATIVE", 0.75),
            make_analyzed_post("post c", 300, "POSITIVE", 0.92),
        ]
        result1 = compute(posts)
        result2 = compute(posts)
        assert result1["raw_score"] == result2["raw_score"]
        assert result1["positive_count"] == result2["positive_count"]
        assert result1["negative_count"] == result2["negative_count"]


# ── No Division by Zero ──────────────────────────────────────

class TestNoDivisionByZero:
    def test_zero_engagement(self, make_analyzed_post):
        posts = [make_analyzed_post("zero engagement post", 0, "POSITIVE", 0.9)]
        result = compute(posts)
        assert isinstance(result["raw_score"], float)

    def test_zero_confidence(self, make_analyzed_post):
        posts = [make_analyzed_post("zero confidence post", 100, "POSITIVE", 0.0)]
        result = compute(posts)
        assert isinstance(result["raw_score"], float)
