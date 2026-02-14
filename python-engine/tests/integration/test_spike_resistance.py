"""
test_spike_resistance.py — Oracle Stability Verification
===========================================================
Proves that a single viral extreme post cannot hijack the oracle.
This is the core anti-manipulation guarantee.
"""

import pytest
from app.ingestion.aggregator import aggregate
from app.nlp.cleaner import clean_posts
from app.nlp.sentiment import analyze_posts
from app.scoring.vibe_score import compute
from app.scoring.smoothing import Smoother


def _make_neutral_post(index: int) -> dict:
    return {
        "text": f"The market is holding steady with no major changes today number {index}",
        "engagement": 50,
        "timestamp": "2025-01-01T00:00:00",
        "author": f"user_{index}",
    }


def _make_extreme_negative(engagement: int = 5000) -> dict:
    return {
        "text": "This is the worst scam in crypto history and everyone will lose everything",
        "engagement": engagement,
        "timestamp": "2025-01-01T00:00:00",
        "author": "viral_fud_account",
    }


def _make_extreme_positive(engagement: int = 5000) -> dict:
    return {
        "text": "This is the most incredible project ever built and it will change the world",
        "engagement": engagement,
        "timestamp": "2025-01-01T00:00:00",
        "author": "viral_shill_account",
    }


def _run_pipeline(posts: list[dict]) -> dict:
    aggregated = aggregate(posts)
    cleaned = clean_posts(aggregated)
    analyzed = analyze_posts(cleaned)
    return compute(analyzed)


class TestSingleSpikeResistance:
    def test_one_viral_negative_among_neutrals(self, mock_model):
        """
        49 neutral posts + 1 viral extreme negative.
        Smoothed score should NOT go to the extreme.
        """
        posts = [_make_neutral_post(i) for i in range(49)]
        posts.append(_make_extreme_negative(engagement=5000))

        score = _run_pipeline(posts)
        smoother = Smoother(alpha=0.3)

        # Establish baseline with neutrals
        smoother.smooth(0.0)
        smoothed = smoother.smooth(score["raw_score"])

        # The smoothed score should be dampened — NOT at -100
        assert smoothed > -80, f"Smoothed score {smoothed} too extreme for single spike"

    def test_one_viral_positive_among_neutrals(self, mock_model):
        """
        49 neutral posts + 1 viral extreme positive.
        Should not spike to +100 immediately.
        """
        posts = [_make_neutral_post(i) for i in range(49)]
        posts.append(_make_extreme_positive(engagement=5000))

        score = _run_pipeline(posts)
        smoother = Smoother(alpha=0.3)

        smoother.smooth(0.0)
        smoothed = smoother.smooth(score["raw_score"])

        assert smoothed < 80, f"Smoothed score {smoothed} too extreme for single spike"


class TestSustainedPressure:
    def test_sustained_negative_eventually_reflects(self, mock_model):
        """
        If ALL posts are consistently negative over many cycles,
        the score should eventually reflect that.
        """
        smoother = Smoother(alpha=0.3)
        neg_posts = [
            {
                "text": f"This project is a terrible scam and fraud number {i}",
                "engagement": 200,
                "timestamp": "t",
                "author": f"bear_{i}",
            }
            for i in range(10)
        ]

        for cycle in range(20):
            score = _run_pipeline(neg_posts)
            smoothed = smoother.smooth(score["raw_score"])

        assert smoothed < -50, "Sustained negative pressure should reflect in score"


class TestRawVsSmoothedDivergence:
    def test_raw_reacts_more_than_smoothed(self, mock_model):
        """Raw score should be more volatile than smoothed."""
        smoother = Smoother(alpha=0.3)

        neutral_posts = [_make_neutral_post(i) for i in range(10)]
        neutral_score = _run_pipeline(neutral_posts)
        smoother.smooth(neutral_score["raw_score"])

        # Now inject extreme negative
        extreme_posts = [
            {
                "text": f"Everything about this project is terrible and a scam number {i}",
                "engagement": 500,
                "timestamp": "t",
                "author": f"fud_{i}",
            }
            for i in range(10)
        ]
        extreme_score = _run_pipeline(extreme_posts)
        smoothed = smoother.smooth(extreme_score["raw_score"])

        # Raw should be more extreme than smoothed
        assert abs(extreme_score["raw_score"]) >= abs(smoothed), \
            "Raw score should be at least as extreme as smoothed"
