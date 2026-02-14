"""
logger.py — Transparency Layer
=================================
Structured logging for every pipeline step.
Proves reproducibility for judges and debugging.
"""

import logging
import sys

# ── Configure root logger ───────────────────────────────────
_handler = logging.StreamHandler(sys.stdout)
_handler.setFormatter(
    logging.Formatter(
        fmt="%(asctime)s │ %(levelname)-7s │ %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
)

logger = logging.getLogger("sentiment_oracle")
logger.setLevel(logging.INFO)
logger.addHandler(_handler)
logger.propagate = False


# ── Convenience helpers ─────────────────────────────────────
def log_pipeline_start(post_count: int) -> None:
    logger.info("═══════════════════════════════════════")
    logger.info("  SENTIMENT ORACLE — Pipeline Cycle")
    logger.info("═══════════════════════════════════════")
    logger.info(f"Ingested posts          : {post_count}")


def log_aggregation(before: int, after: int) -> None:
    logger.info(f"After aggregation       : {after}  (dropped {before - after})")


def log_cleaning(before: int, after: int) -> None:
    logger.info(f"After cleaning          : {after}  (filtered {before - after})")


def log_sentiment_distribution(positive: int, negative: int) -> None:
    total = positive + negative
    logger.info(f"Sentiment distribution  : +{positive} / -{negative}  (total {total})")


def log_scores(raw: float, smoothed: float) -> None:
    logger.info(f"Raw vibe score          : {raw}")
    logger.info(f"Smoothed vibe score     : {smoothed}")
    logger.info("═══════════════════════════════════════")
