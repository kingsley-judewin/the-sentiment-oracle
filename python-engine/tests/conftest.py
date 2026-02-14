"""
conftest.py — Shared Fixtures for Oracle System Verification
==============================================================
Provides reusable test data, mocked models, and pipeline helpers
that avoid loading the real transformer during fast test runs.
"""

import pytest


# ── Force mock ingestion mode for all tests ──────────────────

@pytest.fixture(autouse=True)
def _use_mock_ingestion(monkeypatch):
    """Ensure tests always use mock ingestion, never live RSS or CSV loading."""
    monkeypatch.setattr("app.config.INGESTION_MODE", "mock")
    monkeypatch.setattr("app.ingestion.source_router.INGESTION_MODE", "mock")


# ── Synthetic post factories ───────────────────────────────────

def _make_post(text: str, engagement: int = 100, author: str = "test_user") -> dict:
    """Build a minimal post dict matching pipeline expectations."""
    return {
        "text": text,
        "engagement": engagement,
        "timestamp": "2025-01-01T00:00:00",
        "author": author,
    }


@pytest.fixture
def make_post():
    """Factory fixture for creating synthetic posts."""
    return _make_post


@pytest.fixture
def positive_posts():
    """Batch of clearly positive posts with varying engagement."""
    return [
        _make_post("This project is absolutely incredible and the team delivers", 300),
        _make_post("Just went all in the fundamentals are rock solid and clear", 200),
        _make_post("I love how transparent the devs are with weekly updates", 150),
        _make_post("The community around this token is the best I have seen", 180),
        _make_post("Massive partnership coming soon and bullish vibes everywhere", 400),
    ]


@pytest.fixture
def negative_posts():
    """Batch of clearly negative posts with varying engagement."""
    return [
        _make_post("This is a complete scam the devs are dumping on retail", 280),
        _make_post("Worst investment I ever made the token keeps bleeding", 190),
        _make_post("The smart contract has critical vulnerabilities avoid this", 310),
        _make_post("Team went silent for weeks this is a classic rug pull", 260),
        _make_post("Do not trust this project they will steal your money", 220),
    ]


@pytest.fixture
def neutral_posts():
    """Batch of neutral or mixed-signal posts."""
    return [
        _make_post("The token price is holding steady waiting for the next move", 90),
        _make_post("Interesting chart analysis could break in either direction", 130),
        _make_post("New governance proposal is live everyone should take a look", 160),
        _make_post("The staking rewards are decent compared to other protocols", 110),
        _make_post("Market is tough but the project keeps building regardless", 170),
    ]


@pytest.fixture
def spam_posts():
    """Posts designed to test spam and noise resistance."""
    return [
        _make_post("gm", 3),
        _make_post("AAAAAA", 1),
        _make_post("Check out https://scamsite.xyz/mint now", 5),
        _make_post("BUY NOW!!!", 2),
        _make_post("lol", 1),
    ]


# ── Fake sentiment model for fast tests ───────────────────────

class FakeSentimentModel:
    """
    Deterministic mock of the HuggingFace sentiment pipeline.
    Uses keyword matching instead of transformer inference.
    """

    POSITIVE_KEYWORDS = {
        "incredible", "love", "best", "solid", "bullish", "great",
        "amazing", "fantastic", "excellent", "growth", "real",
        "delivers", "transparent", "partnership", "decent",
        "building", "progress", "strong",
    }
    NEGATIVE_KEYWORDS = {
        "scam", "worst", "bleeding", "vulnerabilities", "rug",
        "silent", "dumping", "steal", "terrible", "awful",
        "avoid", "critical", "brutal", "trust",
    }

    def __call__(self, text: str) -> list[dict]:
        lower = text.lower()
        pos_hits = sum(1 for kw in self.POSITIVE_KEYWORDS if kw in lower)
        neg_hits = sum(1 for kw in self.NEGATIVE_KEYWORDS if kw in lower)

        if pos_hits > neg_hits:
            return [{"label": "POSITIVE", "score": 0.92}]
        elif neg_hits > pos_hits:
            return [{"label": "NEGATIVE", "score": 0.95}]
        else:
            # Default: slight positive for ambiguous
            return [{"label": "POSITIVE", "score": 0.55}]


@pytest.fixture
def fake_model():
    return FakeSentimentModel()


@pytest.fixture
def mock_model(monkeypatch, fake_model):
    """Monkeypatch the model singleton so no transformer loads."""
    monkeypatch.setattr("app.nlp.model._model_instance", fake_model)
    return fake_model


# ── Analyzed post factory (post-NLP stage) ─────────────────────

def _make_analyzed_post(
    text: str,
    engagement: int,
    label: str = "POSITIVE",
    confidence: float = 0.9,
) -> dict:
    polarity = 1 if label == "POSITIVE" else -1
    return {
        "text": text,
        "cleaned_text": text.lower(),
        "engagement": engagement,
        "sentiment": {
            "raw_label": label,
            "confidence": confidence,
            "polarity_score": polarity,
        },
    }


@pytest.fixture
def make_analyzed_post():
    return _make_analyzed_post
