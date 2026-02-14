"""
sentiment.py — Sentiment Inference Layer
==========================================
Converts cleaned text into structured sentiment signals.
Does NOT normalize — only produces raw directional signals.
"""

from app.nlp.model import get_model


def analyze(text: str) -> dict:
    """
    Run sentiment inference on a single cleaned text.

    Returns:
        {
            "raw_label": "POSITIVE" | "NEGATIVE",
            "confidence": float (0-1),
            "polarity_score": +1 | -1
        }
    """
    model = get_model()
    result = model(text)[0]

    label = result["label"]       # "POSITIVE" or "NEGATIVE"
    confidence = result["score"]  # float 0-1

    polarity_score = 1 if label == "POSITIVE" else -1

    return {
        "raw_label": label,
        "confidence": round(confidence, 4),
        "polarity_score": polarity_score,
    }


def analyze_posts(posts: list[dict]) -> list[dict]:
    """
    Run sentiment analysis on a list of cleaned posts.
    Attaches sentiment data to each post dict.

    Returns list of posts with added 'sentiment' field.
    """
    analyzed: list[dict] = []

    for post in posts:
        sentiment = analyze(post["cleaned_text"])
        analyzed.append({**post, "sentiment": sentiment})

    return analyzed
