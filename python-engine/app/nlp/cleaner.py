"""
cleaner.py — Noise Reduction Layer
=====================================
Handles sarcasm proxies, spam, and adversarial manipulation by stripping
URLs, HTML, emojis, repeated characters, and low-effort posts.
"""

import re
from app.config import MIN_POST_WORD_COUNT


def _strip_urls(text: str) -> str:
    return re.sub(r"https?://\S+|www\.\S+", "", text)


def _strip_html(text: str) -> str:
    return re.sub(r"<[^>]+>", "", text)


def _strip_emojis(text: str) -> str:
    emoji_pattern = re.compile(
        "["
        "\U0001F600-\U0001F64F"  # emoticons
        "\U0001F300-\U0001F5FF"  # symbols & pictographs
        "\U0001F680-\U0001F6FF"  # transport & map
        "\U0001F1E0-\U0001F1FF"  # flags
        "\U00002700-\U000027BF"  # dingbats
        "\U0001F900-\U0001F9FF"  # supplemental symbols
        "\U0001FA00-\U0001FA6F"  # chess symbols
        "\U0001FA70-\U0001FAFF"  # symbols extended-A
        "\U00002702-\U000027B0"
        "]+",
        flags=re.UNICODE,
    )
    return emoji_pattern.sub("", text)


def _strip_excessive_symbols(text: str) -> str:
    """Remove strings of 3+ repeated special characters (e.g. !!!, $$$)."""
    return re.sub(r"([^\w\s])\1{2,}", "", text)


def _collapse_repeated_chars(text: str) -> str:
    """Collapse 3+ identical letters to 2 (e.g. 'sooooo' → 'soo')."""
    return re.sub(r"(.)\1{2,}", r"\1\1", text)


def _normalize(text: str) -> str:
    """Lowercase and collapse whitespace."""
    text = text.lower().strip()
    text = re.sub(r"\s+", " ", text)
    return text


def clean_text(text: str) -> str:
    """
    Full cleaning pipeline for a single text string.
    Returns cleaned text.
    """
    text = _strip_urls(text)
    text = _strip_html(text)
    text = _strip_emojis(text)
    text = _strip_excessive_symbols(text)
    text = _collapse_repeated_chars(text)
    text = _normalize(text)
    return text


def clean_posts(posts: list[dict]) -> list[dict]:
    """
    Clean all posts and drop low-quality entries.

    Filters:
      - Posts with fewer than MIN_POST_WORD_COUNT words after cleaning
      - ALL CAPS shouting (original text)

    Returns list of posts with a new 'cleaned_text' field.
    """
    cleaned: list[dict] = []

    for post in posts:
        raw = post.get("text", "")

        # Drop ALL CAPS shouting (check before cleaning)
        alpha_chars = [c for c in raw if c.isalpha()]
        if len(alpha_chars) > 5 and all(c.isupper() for c in alpha_chars):
            continue

        text = clean_text(raw)

        # Drop posts shorter than MIN_POST_WORD_COUNT words
        if len(text.split()) < MIN_POST_WORD_COUNT:
            continue

        cleaned.append({**post, "cleaned_text": text})

    return cleaned
