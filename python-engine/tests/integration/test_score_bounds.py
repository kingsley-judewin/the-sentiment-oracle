"""
test_score_bounds.py — Score Boundary Invariant Verification
===============================================================
Validates the system guarantee: score is ALWAYS in [-100, +100].
No combination of inputs should ever produce an out-of-bounds value.
"""

import pytest
from app.scoring.vibe_score import compute
from app.scoring.smoothing import Smoother
from app.config import MIN_SCORE, MAX_SCORE


class TestAllPositive:
    def test_all_max_positive(self, make_analyzed_post):
        """Maximum positive input should not exceed MAX_SCORE."""
        posts = [
            make_analyzed_post(f"post {i}", engagement=10000, label="POSITIVE", confidence=1.0)
            for i in range(100)
        ]
        result = compute(posts)
        assert result["raw_score"] <= MAX_SCORE
        assert result["raw_score"] == MAX_SCORE  # Should clamp to exactly 100


class TestAllNegative:
    def test_all_max_negative(self, make_analyzed_post):
        """Maximum negative input should not go below MIN_SCORE."""
        posts = [
            make_analyzed_post(f"post {i}", engagement=10000, label="NEGATIVE", confidence=1.0)
            for i in range(100)
        ]
        result = compute(posts)
        assert result["raw_score"] >= MIN_SCORE
        assert result["raw_score"] == MIN_SCORE  # Should clamp to exactly -100


class TestSmoothedBounds:
    def test_smoothed_never_exceeds_raw_bounds(self, make_analyzed_post):
        """EMA smoothing should never push score beyond [-100, +100]."""
        smoother = Smoother(alpha=0.3)

        # Start positive
        pos_posts = [make_analyzed_post(f"good {i}", 500, "POSITIVE", 0.95) for i in range(10)]
        result = compute(pos_posts)
        smoothed = smoother.smooth(result["raw_score"])
        assert MIN_SCORE <= smoothed <= MAX_SCORE

        # Swing to negative
        neg_posts = [make_analyzed_post(f"bad {i}", 500, "NEGATIVE", 0.95) for i in range(10)]
        result = compute(neg_posts)
        smoothed = smoother.smooth(result["raw_score"])
        assert MIN_SCORE <= smoothed <= MAX_SCORE


class TestMixedExtremes:
    def test_mixed_extreme_inputs(self, make_analyzed_post):
        """Mixed extreme positive and negative should stay in bounds."""
        posts = []
        for i in range(50):
            posts.append(make_analyzed_post(f"good {i}", 9999, "POSITIVE", 1.0))
        for i in range(50):
            posts.append(make_analyzed_post(f"bad {i}", 9999, "NEGATIVE", 1.0))

        result = compute(posts)
        assert MIN_SCORE <= result["raw_score"] <= MAX_SCORE


class TestEdgeWeights:
    def test_zero_engagement_in_bounds(self, make_analyzed_post):
        posts = [make_analyzed_post("zero eng", 0, "POSITIVE", 0.9)]
        result = compute(posts)
        assert MIN_SCORE <= result["raw_score"] <= MAX_SCORE

    def test_zero_confidence_in_bounds(self, make_analyzed_post):
        posts = [make_analyzed_post("zero conf", 100, "POSITIVE", 0.0)]
        result = compute(posts)
        assert MIN_SCORE <= result["raw_score"] <= MAX_SCORE

    def test_single_post_in_bounds(self, make_analyzed_post):
        posts = [make_analyzed_post("one post", 1, "NEGATIVE", 0.5)]
        result = compute(posts)
        assert MIN_SCORE <= result["raw_score"] <= MAX_SCORE


class TestScoreTypeInvariant:
    def test_raw_score_is_float(self, make_analyzed_post):
        posts = [make_analyzed_post("test", 100, "POSITIVE", 0.8)]
        result = compute(posts)
        assert isinstance(result["raw_score"], (int, float))

    def test_smoothed_is_float(self, make_analyzed_post):
        smoother = Smoother(alpha=0.3)
        posts = [make_analyzed_post("test", 100, "POSITIVE", 0.8)]
        result = compute(posts)
        smoothed = smoother.smooth(result["raw_score"])
        assert isinstance(smoothed, (int, float))
