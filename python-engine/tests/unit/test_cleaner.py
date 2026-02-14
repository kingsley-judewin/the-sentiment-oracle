"""
test_cleaner.py — Noise Reduction Verification
=================================================
Validates that the cleaner layer properly strips noise,
normalizes text, and never crashes on adversarial input.
"""

import pytest
from app.nlp.cleaner import clean_text, clean_posts


# ── URL Removal ────────────────────────────────────────────────

class TestURLRemoval:
    def test_https_url_stripped(self):
        result = clean_text("Check this https://example.com/page right now")
        assert "https" not in result
        assert "example.com" not in result

    def test_http_url_stripped(self):
        result = clean_text("Visit http://malicious.site/payload for more info today")
        assert "http" not in result
        assert "malicious" not in result

    def test_www_url_stripped(self):
        result = clean_text("Go to www.somesite.org/path for the latest update here")
        assert "www" not in result
        assert "somesite" not in result

    def test_multiple_urls_stripped(self):
        result = clean_text("Links https://a.com and https://b.com are both bad links today")
        assert "a.com" not in result
        assert "b.com" not in result

    def test_text_only_url(self):
        """A post that is only a URL should produce empty or near-empty text."""
        result = clean_text("https://onlyurl.com/nothing-else")
        assert "onlyurl" not in result


# ── Emoji Removal ──────────────────────────────────────────────

class TestEmojiRemoval:
    def test_basic_emojis_stripped(self):
        result = clean_text("Great project! 🚀🌕💎🙌 Love it very much today")
        assert "\U0001F680" not in result  # rocket
        assert "\U0001F315" not in result  # moon

    def test_only_emojis(self):
        """Post that is only emojis should become empty."""
        result = clean_text("🚀🚀🚀🌕🌕🌕💎💎💎")
        assert result.strip() == ""

    def test_emojis_between_words(self):
        result = clean_text("to 🚀 the 🌕 moon and beyond today for real")
        assert "to" in result
        assert "the" in result
        assert "moon" in result


# ── Case Normalization ─────────────────────────────────────────

class TestCaseNormalization:
    def test_uppercase_lowered(self):
        result = clean_text("THIS IS A Test Of Mixed Case Input Today")
        assert result == "this is a test of mixed case input today"

    def test_already_lowercase(self):
        result = clean_text("already lowercase text stays the same today")
        assert result == "already lowercase text stays the same today"


# ── Whitespace Normalization ───────────────────────────────────

class TestWhitespaceNormalization:
    def test_excess_spaces_collapsed(self):
        result = clean_text("too    many     spaces   in   this   text   here")
        assert "  " not in result

    def test_tabs_and_newlines_collapsed(self):
        result = clean_text("has\ttabs\nand\nnewlines everywhere in this text")
        assert "\t" not in result
        assert "\n" not in result

    def test_leading_trailing_stripped(self):
        result = clean_text("   padded text with spaces around it now   ")
        assert not result.startswith(" ")
        assert not result.endswith(" ")


# ── Repeated Characters ───────────────────────────────────────

class TestRepeatedCharacters:
    def test_excessive_letters_collapsed(self):
        result = clean_text("This is sooooo goooood and amaaaaazing today")
        assert "ooo" not in result
        assert "aaa" not in result

    def test_excessive_symbols_stripped(self):
        result = clean_text("Buy now!!! This is great$$$ and happening today")
        assert "!!!" not in result
        assert "$$$" not in result


# ── Empty and Edge Cases ──────────────────────────────────────

class TestEdgeCases:
    def test_empty_string(self):
        result = clean_text("")
        assert result == ""

    def test_whitespace_only(self):
        result = clean_text("     ")
        assert result == ""

    def test_very_long_text(self):
        """Cleaner should not crash on very long text."""
        long_text = "this is a word " * 5000
        result = clean_text(long_text)
        assert isinstance(result, str)
        assert len(result) > 0

    def test_mixed_language(self):
        """Non-ASCII text should survive cleaning."""
        result = clean_text("El proyecto es increible y tiene mucho potencial hoy")
        assert "increible" in result

    def test_html_tags_stripped(self):
        result = clean_text("<b>bold</b> and <a href='x'>link text</a> are in here today")
        assert "<b>" not in result
        assert "<a " not in result
        assert "bold" in result


# ── Post-Level Filtering (clean_posts) ────────────────────────

class TestCleanPosts:
    def test_all_caps_dropped(self):
        """ALL CAPS posts should be filtered out."""
        posts = [{"text": "BUY THIS TOKEN RIGHT NOW OR YOU WILL MISS OUT", "engagement": 10}]
        result = clean_posts(posts)
        assert len(result) == 0

    def test_short_posts_dropped(self):
        """Posts under MIN_POST_WORD_COUNT words should be filtered."""
        posts = [{"text": "gm", "engagement": 1}]
        result = clean_posts(posts)
        assert len(result) == 0

    def test_valid_post_survives(self):
        """A normal post should pass through with cleaned_text added."""
        posts = [{"text": "This project looks really promising and I am excited about it", "engagement": 100}]
        result = clean_posts(posts)
        assert len(result) == 1
        assert "cleaned_text" in result[0]

    def test_cleaned_text_is_lowercase(self):
        posts = [{"text": "The Fundamentals Are Strong And The Team Is Building Great Things", "engagement": 50}]
        result = clean_posts(posts)
        assert result[0]["cleaned_text"] == result[0]["cleaned_text"].lower()

    def test_original_fields_preserved(self):
        """Original post fields should not be lost after cleaning."""
        posts = [{
            "text": "A valid post with enough words to survive the cleaning filter",
            "engagement": 200,
            "author": "test_author",
        }]
        result = clean_posts(posts)
        assert result[0]["engagement"] == 200
        assert result[0]["author"] == "test_author"

    def test_empty_list(self):
        result = clean_posts([])
        assert result == []

    def test_mixed_batch_filtering(self):
        """Some posts survive, some get filtered."""
        posts = [
            {"text": "This is a totally valid and long enough post for our pipeline", "engagement": 100},
            {"text": "gm", "engagement": 1},
            {"text": "BUY THIS NOW IMMEDIATELY DO IT RIGHT NOW ASAP", "engagement": 5},
            {"text": "Another perfectly valid post with enough content for testing", "engagement": 80},
        ]
        result = clean_posts(posts)
        # Only the two valid posts should survive
        assert len(result) == 2
