"""
test_full_runtime.py — Full Cycle Simulation
================================================
Simulates the complete oracle pipeline end-to-end:
  Ingestion → Aggregation → Cleaning → Sentiment → Scoring → Smoothing

Validates that no step silently fails and all guarantees hold.
"""

import pytest
from app.ingestion.mock_stream import fetch_posts
from app.ingestion.aggregator import aggregate
from app.nlp.cleaner import clean_posts
from app.nlp.sentiment import analyze_posts
from app.scoring.vibe_score import compute
from app.scoring.smoothing import Smoother
from app.config import MIN_SCORE, MAX_SCORE


class TestFullPipelineExecution:
    """Run the real pipeline with mock data (but mocked model for speed)."""

    def test_full_cycle_completes(self, mock_model):
        """All 6 stages complete without exception."""
        raw = fetch_posts()
        aggregated = aggregate(raw)
        cleaned = clean_posts(aggregated)
        analyzed = analyze_posts(cleaned)
        scored = compute(analyzed)
        smoother = Smoother(alpha=0.3)
        smoothed = smoother.smooth(scored["raw_score"])

        assert isinstance(smoothed, float)

    def test_no_data_loss_between_stages(self, mock_model):
        """Each stage should receive and return data — no silent drops to zero."""
        raw = fetch_posts()
        assert len(raw) > 0, "Ingestion should return posts"

        aggregated = aggregate(raw)
        assert len(aggregated) > 0, "Aggregation should return posts"

        cleaned = clean_posts(aggregated)
        assert len(cleaned) > 0, "Cleaning should leave some posts"

        analyzed = analyze_posts(cleaned)
        assert len(analyzed) > 0, "Analysis should annotate posts"
        assert len(analyzed) == len(cleaned), "Analysis should not drop posts"

        scored = compute(analyzed)
        assert scored["post_count"] == len(analyzed)

    def test_output_schema_complete(self, mock_model):
        """Final output should have all required fields."""
        raw = fetch_posts()
        aggregated = aggregate(raw)
        cleaned = clean_posts(aggregated)
        analyzed = analyze_posts(cleaned)
        scored = compute(analyzed)
        smoother = Smoother(alpha=0.3)
        smoothed = smoother.smooth(scored["raw_score"])

        output = {
            "raw_score": scored["raw_score"],
            "smoothed_score": smoothed,
            "post_count": scored["post_count"],
            "positive_count": scored["positive_count"],
            "negative_count": scored["negative_count"],
        }

        assert "raw_score" in output
        assert "smoothed_score" in output
        assert "post_count" in output
        assert "positive_count" in output
        assert "negative_count" in output

    def test_score_bounds_hold(self, mock_model):
        raw = fetch_posts()
        aggregated = aggregate(raw)
        cleaned = clean_posts(aggregated)
        analyzed = analyze_posts(cleaned)
        scored = compute(analyzed)
        smoother = Smoother(alpha=0.3)
        smoothed = smoother.smooth(scored["raw_score"])

        assert MIN_SCORE <= scored["raw_score"] <= MAX_SCORE
        assert MIN_SCORE <= smoothed <= MAX_SCORE


class TestStageIsolation:
    """Verify each pipeline stage transforms data correctly."""

    def test_aggregator_deduplicates(self, mock_model):
        raw = fetch_posts()
        before = len(raw)
        after = len(aggregate(raw))
        # Aggregation should not increase post count
        assert after <= before

    def test_cleaner_adds_cleaned_text(self, mock_model):
        raw = fetch_posts()
        aggregated = aggregate(raw)
        cleaned = clean_posts(aggregated)
        for post in cleaned:
            assert "cleaned_text" in post
            assert isinstance(post["cleaned_text"], str)
            assert len(post["cleaned_text"]) > 0

    def test_analyzer_adds_sentiment(self, mock_model):
        raw = fetch_posts()
        aggregated = aggregate(raw)
        cleaned = clean_posts(aggregated)
        analyzed = analyze_posts(cleaned)
        for post in analyzed:
            assert "sentiment" in post
            s = post["sentiment"]
            assert s["raw_label"] in ("POSITIVE", "NEGATIVE")
            assert 0.0 <= s["confidence"] <= 1.0
            assert s["polarity_score"] in (1, -1)

    def test_scorer_returns_valid_structure(self, mock_model):
        raw = fetch_posts()
        aggregated = aggregate(raw)
        cleaned = clean_posts(aggregated)
        analyzed = analyze_posts(cleaned)
        scored = compute(analyzed)

        assert isinstance(scored["raw_score"], float)
        assert isinstance(scored["post_count"], int)
        assert isinstance(scored["positive_count"], int)
        assert isinstance(scored["negative_count"], int)


class TestMultipleCycles:
    """Simulate multiple sequential oracle cycles."""

    def test_three_consecutive_cycles(self, mock_model):
        """Three full pipeline runs with the same smoother."""
        smoother = Smoother(alpha=0.3)
        scores = []

        for _ in range(3):
            raw = fetch_posts()
            aggregated = aggregate(raw)
            cleaned = clean_posts(aggregated)
            analyzed = analyze_posts(cleaned)
            scored = compute(analyzed)
            smoothed = smoother.smooth(scored["raw_score"])
            scores.append(smoothed)

        # All scores should be valid
        for s in scores:
            assert MIN_SCORE <= s <= MAX_SCORE
            assert isinstance(s, float)

        # History should track all cycles
        assert len(smoother.history) == 3
