"""
test_adversarial_noise.py — Adversarial Input Verification
=============================================================
Validates that the cleaner and pipeline handle intentionally
malicious, noisy, and adversarial inputs without breaking.
"""

import pytest
from app.nlp.cleaner import clean_text, clean_posts
from app.ingestion.aggregator import aggregate
from app.nlp.sentiment import analyze_posts
from app.scoring.vibe_score import compute


class TestSpamContent:
    def test_repeated_spam_phrases(self):
        """Repeated spam phrases should not crash cleaner."""
        text = "BUY NOW " * 100
        result = clean_text(text)
        assert isinstance(result, str)

    def test_url_spam(self):
        """Mass URLs should all be stripped."""
        text = " ".join([f"https://spam{i}.com" for i in range(50)])
        result = clean_text(text)
        assert "https" not in result
        assert "spam" not in result


class TestAllCaps:
    def test_all_caps_post_filtered(self):
        posts = [{"text": "THIS IS ALL CAPS AND VERY LOUD SHOUTING POST", "engagement": 100}]
        result = clean_posts(posts)
        assert len(result) == 0, "ALL CAPS should be filtered"

    def test_mixed_caps_not_filtered(self):
        posts = [{"text": "This has Mixed Case and should survive the filter today", "engagement": 100}]
        result = clean_posts(posts)
        assert len(result) == 1, "Mixed case should not be filtered"


class TestRepeatedCharacters:
    def test_letter_spam(self):
        text = "aaaaaaaaaaaaaaaaaaaaaa bbbbbbbbbbbb this is goooooood text today"
        result = clean_text(text)
        assert "aaa" not in result
        assert "bbb" not in result

    def test_symbol_storms(self):
        text = "!!!!!!!!!!! $$$$$$$$$ ########## buy this now please today now"
        result = clean_text(text)
        assert "!!!" not in result
        assert "$$$" not in result
        assert "###" not in result


class TestEmojiStorms:
    def test_mass_emojis(self):
        text = "🚀" * 100 + " moon soon " + "💎" * 100 + " diamond hands forever today"
        result = clean_text(text)
        assert "\U0001F680" not in result
        assert "\U0001F48E" not in result
        # Real text should survive
        assert "moon" in result or "diamond" in result

    def test_emoji_only_post_filtered(self):
        posts = [{"text": "🚀🚀🚀🌕🌕🌕💎💎💎🙌🙌🙌", "engagement": 500}]
        result = clean_posts(posts)
        assert len(result) == 0, "Emoji-only post should be filtered (too short after cleaning)"


class TestHTMLInjection:
    def test_html_tags_stripped(self):
        text = "<script>alert('xss')</script> This is a real post with enough words"
        result = clean_text(text)
        assert "<script>" not in result
        assert "</script>" not in result

    def test_nested_html(self):
        text = "<div><p><b>Nested</b></p></div> tags should all be removed from here"
        result = clean_text(text)
        assert "<" not in result
        assert ">" not in result


class TestAdversarialPipelineRun:
    def test_adversarial_batch_no_crash(self, mock_model):
        """Full pipeline with adversarial inputs should not crash."""
        posts = [
            {"text": "🚀" * 200, "engagement": 999, "timestamp": "t", "author": "a"},
            {"text": "BUY NOW " * 50, "engagement": 888, "timestamp": "t", "author": "b"},
            {"text": "https://x.com " * 30, "engagement": 777, "timestamp": "t", "author": "c"},
            {"text": "<script>alert(1)</script>" * 10, "engagement": 666, "timestamp": "t", "author": "d"},
            {"text": "a" * 10000, "engagement": 555, "timestamp": "t", "author": "e"},
            {"text": "", "engagement": 444, "timestamp": "t", "author": "f"},
            {"text": "   \n\t   ", "engagement": 333, "timestamp": "t", "author": "g"},
            {"text": "A normal valid post with enough words to survive", "engagement": 100, "timestamp": "t", "author": "h"},
        ]
        aggregated = aggregate(posts)
        cleaned = clean_posts(aggregated)
        analyzed = analyze_posts(cleaned)
        result = compute(analyzed)
        assert isinstance(result["raw_score"], (int, float))


class TestUnicodeEdgeCases:
    def test_null_bytes(self):
        text = "Contains \x00 null \x00 bytes in this text that is long enough"
        result = clean_text(text)
        assert isinstance(result, str)

    def test_rtl_text(self):
        text = "Some text with arabic chars and right to left markers in it"
        result = clean_text(text)
        assert isinstance(result, str)

    def test_extremely_long_single_word(self):
        text = "a" * 50000
        result = clean_text(text)
        assert isinstance(result, str)
