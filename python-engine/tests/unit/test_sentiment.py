"""
test_sentiment.py — Sentiment Inference Verification
=======================================================
Validates the output structure and behavioral guarantees
of the sentiment analysis layer.

Uses the real HuggingFace model — these tests verify
actual NLP behavior, not mocks.
"""

import pytest
from app.nlp.sentiment import analyze, analyze_posts


# ── Output Structure ──────────────────────────────────────────

class TestOutputStructure:
    def test_required_keys_present(self):
        result = analyze("This is a great project with amazing potential")
        assert "raw_label" in result
        assert "confidence" in result
        assert "polarity_score" in result

    def test_label_is_valid_enum(self):
        result = analyze("The fundamentals of this project are excellent and strong")
        assert result["raw_label"] in ("POSITIVE", "NEGATIVE")

    def test_polarity_matches_label(self):
        result = analyze("Everything about this project is wonderful and amazing today")
        if result["raw_label"] == "POSITIVE":
            assert result["polarity_score"] == 1
        else:
            assert result["polarity_score"] == -1


# ── Confidence Bounds ─────────────────────────────────────────

class TestConfidenceBounds:
    def test_confidence_in_range(self):
        result = analyze("Some text for confidence bound testing today here")
        assert 0.0 <= result["confidence"] <= 1.0

    def test_strong_positive_high_confidence(self):
        result = analyze("This is absolutely amazing, the best thing I have ever seen")
        assert result["confidence"] >= 0.7

    def test_strong_negative_high_confidence(self):
        result = analyze("This is a terrible scam and the worst project in existence")
        assert result["confidence"] >= 0.7


# ── Directional Correctness ───────────────────────────────────

class TestDirectionalCorrectness:
    def test_clearly_positive(self):
        result = analyze("I love this project, it is absolutely incredible and amazing")
        assert result["raw_label"] == "POSITIVE"
        assert result["polarity_score"] == 1

    def test_clearly_negative(self):
        result = analyze("This is a terrible scam, avoid at all costs right now")
        assert result["raw_label"] == "NEGATIVE"
        assert result["polarity_score"] == -1

    def test_neutral_still_returns_valid(self):
        """Even ambiguous text must produce a valid structured output."""
        result = analyze("the token price is at five dollars and thirty two cents")
        assert result["raw_label"] in ("POSITIVE", "NEGATIVE")
        assert 0.0 <= result["confidence"] <= 1.0


# ── Batch Analysis ────────────────────────────────────────────

class TestBatchAnalysis:
    def test_analyze_posts_adds_sentiment_field(self):
        posts = [
            {"cleaned_text": "this project is amazing and really impressive today"},
            {"cleaned_text": "this is the worst scam i have ever seen in crypto"},
        ]
        result = analyze_posts(posts)
        assert len(result) == 2
        for post in result:
            assert "sentiment" in post
            assert "raw_label" in post["sentiment"]
            assert "confidence" in post["sentiment"]
            assert "polarity_score" in post["sentiment"]

    def test_analyze_posts_preserves_original_fields(self):
        posts = [{"cleaned_text": "great project here today", "engagement": 500, "author": "test"}]
        result = analyze_posts(posts)
        assert result[0]["engagement"] == 500
        assert result[0]["author"] == "test"

    def test_analyze_posts_empty_list(self):
        result = analyze_posts([])
        assert result == []


# ── Invariant: No Crash on Edge Input ─────────────────────────

class TestEdgeInputs:
    def test_single_word(self):
        result = analyze("good")
        assert result["raw_label"] in ("POSITIVE", "NEGATIVE")

    def test_numbers_only(self):
        result = analyze("12345 67890 11111")
        assert 0.0 <= result["confidence"] <= 1.0

    def test_special_characters(self):
        result = analyze("@#$%^&*()_+ some text here today now")
        assert result["raw_label"] in ("POSITIVE", "NEGATIVE")
