"""
test_pipeline_flow.py — Data Flow Integrity Verification
===========================================================
Runs mock posts through the full pipeline (with mocked NLP model)
and validates that the output structure and constraints are correct.
"""

import pytest
from app.ingestion.aggregator import aggregate
from app.nlp.cleaner import clean_posts
from app.nlp.sentiment import analyze_posts
from app.scoring.vibe_score import compute
from app.scoring.smoothing import Smoother
from app.config import MIN_SCORE, MAX_SCORE


def _run_pipeline(posts: list[dict], smoother: Smoother | None = None) -> dict:
    """Execute the full pipeline with a fresh smoother."""
    aggregated = aggregate(posts)
    cleaned = clean_posts(aggregated)
    analyzed = analyze_posts(cleaned)
    score_result = compute(analyzed)

    if smoother is None:
        smoother = Smoother(alpha=0.3)
    smoothed = smoother.smooth(score_result["raw_score"])

    return {
        "raw_score": score_result["raw_score"],
        "smoothed_score": smoothed,
        "post_count": score_result["post_count"],
        "positive_count": score_result["positive_count"],
        "negative_count": score_result["negative_count"],
    }


class TestPipelineOutputStructure:
    def test_all_required_fields_present(self, mock_model, positive_posts):
        result = _run_pipeline(positive_posts)
        assert "raw_score" in result
        assert "smoothed_score" in result
        assert "post_count" in result
        assert "positive_count" in result
        assert "negative_count" in result

    def test_score_types(self, mock_model, positive_posts):
        result = _run_pipeline(positive_posts)
        assert isinstance(result["raw_score"], (int, float))
        assert isinstance(result["smoothed_score"], (int, float))
        assert isinstance(result["post_count"], int)
        assert isinstance(result["positive_count"], int)
        assert isinstance(result["negative_count"], int)


class TestPipelineScoreBounds:
    def test_raw_score_within_bounds(self, mock_model, positive_posts):
        result = _run_pipeline(positive_posts)
        assert MIN_SCORE <= result["raw_score"] <= MAX_SCORE

    def test_smoothed_score_within_bounds(self, mock_model, positive_posts):
        result = _run_pipeline(positive_posts)
        assert MIN_SCORE <= result["smoothed_score"] <= MAX_SCORE

    def test_negative_posts_negative_score(self, mock_model, negative_posts):
        result = _run_pipeline(negative_posts)
        assert result["raw_score"] < 0, "Negative input should produce negative score"

    def test_positive_posts_positive_score(self, mock_model, positive_posts):
        result = _run_pipeline(positive_posts)
        assert result["raw_score"] > 0, "Positive input should produce positive score"


class TestPipelineCounts:
    def test_post_count_matches_surviving_posts(self, mock_model, positive_posts):
        result = _run_pipeline(positive_posts)
        assert result["post_count"] > 0
        assert result["post_count"] <= len(positive_posts)

    def test_positive_negative_sum_equals_total(self, mock_model, positive_posts, negative_posts):
        combined = positive_posts + negative_posts
        result = _run_pipeline(combined)
        assert result["positive_count"] + result["negative_count"] == result["post_count"]


class TestPipelineWithSpam:
    def test_spam_filtered_out(self, mock_model, spam_posts):
        """Spam posts should be filtered by cleaner, resulting in 0 posts."""
        result = _run_pipeline(spam_posts)
        assert result["post_count"] == 0
        assert result["raw_score"] == 0.0

    def test_mixed_valid_and_spam(self, mock_model, positive_posts, spam_posts):
        """Valid posts should survive even when mixed with spam."""
        combined = positive_posts + spam_posts
        result = _run_pipeline(combined)
        assert result["post_count"] > 0
        assert result["raw_score"] > 0


class TestPipelineNoSilentFailure:
    def test_empty_input(self, mock_model):
        result = _run_pipeline([])
        assert result["raw_score"] == 0.0
        assert result["post_count"] == 0

    def test_all_filtered_posts(self, mock_model):
        """If every post gets filtered, pipeline should return zero gracefully."""
        posts = [
            {"text": "gm", "engagement": 1, "timestamp": "t", "author": "a"},
            {"text": "lol", "engagement": 1, "timestamp": "t", "author": "b"},
        ]
        result = _run_pipeline(posts)
        assert result["raw_score"] == 0.0
        assert result["post_count"] == 0
