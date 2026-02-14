"""
test_determinism.py — Reproducibility Verification
=====================================================
Validates that the same input always produces the same output.
The oracle must be predictable and auditable.
"""

import pytest
from app.ingestion.aggregator import aggregate
from app.nlp.cleaner import clean_posts
from app.nlp.sentiment import analyze_posts
from app.scoring.vibe_score import compute
from app.scoring.smoothing import Smoother


def _run_pipeline(posts: list[dict]) -> dict:
    """Run the full pipeline without global state side effects."""
    aggregated = aggregate(posts)
    cleaned = clean_posts(aggregated)
    analyzed = analyze_posts(cleaned)
    return compute(analyzed)


class TestRawScoreDeterminism:
    def test_identical_input_identical_output(self, mock_model, positive_posts):
        """Same posts fed twice → identical raw_score."""
        result1 = _run_pipeline(positive_posts)
        result2 = _run_pipeline(positive_posts)
        assert result1["raw_score"] == result2["raw_score"]

    def test_identical_counts(self, mock_model, positive_posts):
        result1 = _run_pipeline(positive_posts)
        result2 = _run_pipeline(positive_posts)
        assert result1["post_count"] == result2["post_count"]
        assert result1["positive_count"] == result2["positive_count"]
        assert result1["negative_count"] == result2["negative_count"]

    def test_mixed_input_determinism(self, mock_model, positive_posts, negative_posts):
        combined = positive_posts + negative_posts
        result1 = _run_pipeline(combined)
        result2 = _run_pipeline(combined)
        assert result1["raw_score"] == result2["raw_score"]


class TestSmoothedScoreDeterminism:
    def test_isolated_smoother_determinism(self, mock_model, positive_posts):
        """
        With a fresh smoother each time, same input → same smoothed output.
        """
        score = _run_pipeline(positive_posts)

        s1 = Smoother(alpha=0.3)
        s2 = Smoother(alpha=0.3)

        smoothed1 = s1.smooth(score["raw_score"])
        smoothed2 = s2.smooth(score["raw_score"])

        assert smoothed1 == smoothed2

    def test_sequence_determinism(self, mock_model, positive_posts, negative_posts):
        """Same sequence of scores → same sequence of smoothed values."""
        score_pos = _run_pipeline(positive_posts)
        score_neg = _run_pipeline(negative_posts)

        s1 = Smoother(alpha=0.3)
        s2 = Smoother(alpha=0.3)

        seq1 = [s1.smooth(score_pos["raw_score"]), s1.smooth(score_neg["raw_score"])]
        seq2 = [s2.smooth(score_pos["raw_score"]), s2.smooth(score_neg["raw_score"])]

        assert seq1 == seq2


class TestAggregatorDeterminism:
    def test_dedup_order_stable(self, mock_model):
        """Aggregator should produce stable ordering regardless of duplicates."""
        posts = [
            {"text": "This project has amazing potential and great community", "engagement": 100, "timestamp": "t", "author": "a"},
            {"text": "This project has amazing potential and great community", "engagement": 100, "timestamp": "t", "author": "b"},
            {"text": "Terrible scam that will steal your money stay away now", "engagement": 200, "timestamp": "t", "author": "c"},
        ]
        result1 = aggregate(posts)
        result2 = aggregate(posts)
        assert len(result1) == len(result2)
        for p1, p2 in zip(result1, result2):
            assert p1["text"] == p2["text"]


class TestCleanerDeterminism:
    def test_cleaner_idempotent(self):
        """Cleaning the same posts twice produces the same result."""
        from app.nlp.cleaner import clean_text
        text = "Check https://example.com this is GREAT!!! so amaaaaazing today"
        assert clean_text(text) == clean_text(text)
