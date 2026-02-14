"""
test_high_volume.py — Volume Stress Verification
====================================================
Ensures the pipeline handles large post volumes without
crashing, hanging, or reloading the model per-row.
"""

import time
import pytest
from app.ingestion.aggregator import aggregate
from app.nlp.cleaner import clean_posts
from app.nlp.sentiment import analyze_posts
from app.scoring.vibe_score import compute
from app.scoring.smoothing import Smoother
from app.config import MIN_SCORE, MAX_SCORE


def _generate_posts(count: int) -> list[dict]:
    """Generate a large batch of diverse synthetic posts."""
    templates = [
        "This project is really exciting and the team keeps delivering great results",
        "Worst investment decision I have ever made the price keeps dropping badly",
        "The market is sideways and there is nothing to do but wait patiently now",
        "Amazing partnership announcement today this will change everything for us",
        "Do not buy this token it is a scam and the developers are scammers here",
        "Interesting developments in the ecosystem but still too early to tell clearly",
        "The staking rewards are decent but the risk profile seems a bit high overall",
        "Community is growing fast and the governance is working really well now today",
        "This is a slow rug pull and the team knows exactly what they are doing here",
        "Neutral observation about the price action and volume trends this week honestly",
    ]
    posts = []
    for i in range(count):
        posts.append({
            "text": f"{templates[i % len(templates)]} post number {i}",
            "engagement": (i % 500) + 10,
            "timestamp": "2025-01-01T00:00:00",
            "author": f"stress_user_{i}",
        })
    return posts


class TestHighVolume:
    def test_1000_posts_completes(self, mock_model):
        """Pipeline should handle 1000 posts without crashing."""
        posts = _generate_posts(1000)
        aggregated = aggregate(posts)
        cleaned = clean_posts(aggregated)
        analyzed = analyze_posts(cleaned)
        result = compute(analyzed)

        assert result["post_count"] > 0
        assert MIN_SCORE <= result["raw_score"] <= MAX_SCORE

    def test_1000_posts_under_time_limit(self, mock_model):
        """
        With mocked model, 1000 posts should process in under 5 seconds.
        This validates no per-row model reloading.
        """
        posts = _generate_posts(1000)

        start = time.perf_counter()
        aggregated = aggregate(posts)
        cleaned = clean_posts(aggregated)
        analyzed = analyze_posts(cleaned)
        result = compute(analyzed)
        smoother = Smoother(alpha=0.3)
        smoother.smooth(result["raw_score"])
        elapsed = time.perf_counter() - start

        assert elapsed < 5.0, f"Pipeline took {elapsed:.2f}s — too slow for 1000 posts"

    def test_5000_posts_no_crash(self, mock_model):
        """Even 5000 posts should not cause memory issues or crashes."""
        posts = _generate_posts(5000)
        aggregated = aggregate(posts)
        cleaned = clean_posts(aggregated)
        analyzed = analyze_posts(cleaned)
        result = compute(analyzed)

        assert isinstance(result["raw_score"], float)
        assert result["post_count"] > 0


class TestModelSingleton:
    def test_model_not_reloaded(self, mock_model):
        """
        The model singleton should be the same object across calls.
        This prevents GPU/CPU thrashing.
        """
        from app.nlp.model import get_model

        model_a = get_model()
        model_b = get_model()
        assert model_a is model_b, "Model should be singleton — same object reference"


class TestAggregatorScaling:
    def test_aggregator_truncates_to_max(self, mock_model):
        """Even with huge input, aggregator should truncate to MAX_POSTS."""
        from app.config import MAX_POSTS
        posts = _generate_posts(500)
        aggregated = aggregate(posts)
        assert len(aggregated) <= MAX_POSTS


class TestSmootherStabilityUnderLoad:
    def test_many_cycles_no_drift(self):
        """Smoother should remain stable over many cycles."""
        smoother = Smoother(alpha=0.3)

        # Feed constant value — should converge and stay
        for _ in range(1000):
            result = smoother.smooth(50.0)

        assert abs(result - 50.0) < 0.01, "Smoother should converge to stable value"

    def test_alternating_no_explosion(self):
        """Rapidly alternating values should not cause explosion."""
        smoother = Smoother(alpha=0.3)

        for i in range(1000):
            val = 100.0 if i % 2 == 0 else -100.0
            result = smoother.smooth(val)

        assert MIN_SCORE <= result <= MAX_SCORE
