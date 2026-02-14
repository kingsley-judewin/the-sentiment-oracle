"""
twitter_dataset.py — Sentiment140 CSV Sampling Layer (Production-Grade)
==========================================================================
Loads the 1.6M tweet Sentiment140 dataset once into memory,
then returns rolling samples on each call to simulate streaming.

Production Features:
  - Singleton pattern (loads 238MB CSV only once)
  - Rolling sample mode (pointer-based iteration, not random)
  - Engagement proxy with variance
  - Standardized output format matching RSS schema
"""

import random
from datetime import datetime, timezone

import pandas as pd

from app.config import TWITTER_DATASET_PATH, TWITTER_SAMPLE_SIZE
from app.utils.logger import logger


# ── Singleton state ──────────────────────────────────────
_dataset: pd.DataFrame | None = None
_rolling_index: int = 0  # Pointer for rolling sample mode


def _load_dataset() -> pd.DataFrame:
    """
    Load the Sentiment140 CSV into a DataFrame.

    Only loads label (col 0) and text (col 5) to minimize memory.
    The CSV has no header row — columns are specified explicitly.
    """
    df = pd.read_csv(
        TWITTER_DATASET_PATH,
        encoding="latin-1",
        header=None,
        names=["label", "id", "date", "query", "user", "text"],
        usecols=[0, 5],
    )

    df = df.dropna(subset=["text"])
    df["text"] = df["text"].astype(str)

    logger.info(f"Loaded Sentiment140 dataset: {len(df)} tweets")
    return df


def _ensure_loaded() -> pd.DataFrame:
    """Return the singleton DataFrame, loading on first call."""
    global _dataset
    if _dataset is None:
        _dataset = _load_dataset()
    return _dataset


def fetch_twitter_posts() -> list[dict]:
    """
    Sample a batch of posts from the Sentiment140 dataset using rolling mode.
    
    Rolling Mode Strategy:
      - Maintains a pointer (_rolling_index) into the dataset
      - Returns next N tweets starting from pointer
      - Wraps around at dataset end
      - Creates "stream illusion" instead of random sampling
    
    Returns standardized post dicts compatible with the pipeline:
        {id, text, engagement, timestamp, author, source}
    """
    global _rolling_index
    
    try:
        df = _ensure_loaded()
        dataset_size = len(df)
        
        # Determine sample size
        sample_size = min(TWITTER_SAMPLE_SIZE, dataset_size)
        
        # Extract rolling window
        end_index = _rolling_index + sample_size
        
        if end_index <= dataset_size:
            # Normal case: window fits within dataset
            sample = df.iloc[_rolling_index:end_index]
            _rolling_index = end_index
        else:
            # Wrap-around case: take from end + beginning
            first_part = df.iloc[_rolling_index:]
            remaining = sample_size - len(first_part)
            second_part = df.iloc[:remaining]
            sample = pd.concat([first_part, second_part])
            _rolling_index = remaining
        
        # Wrap pointer at dataset end
        if _rolling_index >= dataset_size:
            _rolling_index = 0
        
        now = datetime.now(timezone.utc).isoformat()

        posts = []
        for idx, row in sample.iterrows():
            # Engagement proxy with slight variance (5-25 range)
            engagement = random.randint(5, 25)
            
            posts.append({
                "id": f"twitter_{idx}",
                "text": row["text"],
                "engagement": engagement,
                "timestamp": now,
                "author": None,
                "source": "twitter",
            })

        logger.info(
            f"Twitter dataset: sampled {len(posts)} posts "
            f"(rolling index: {_rolling_index}/{dataset_size})"
        )
        return posts

    except Exception as e:
        logger.warning(f"Twitter dataset ingestion failed: {e}")
        return []


def reset_rolling_index() -> None:
    """Reset the rolling index to 0 (useful for testing)."""
    global _rolling_index
    _rolling_index = 0
    logger.info("Twitter dataset: rolling index reset to 0")
