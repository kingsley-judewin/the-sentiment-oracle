"""
config.py — Centralized Control Layer
======================================
All tunable system parameters for the Sentiment Oracle pipeline.
"""

# ─── NLP Model ──────────────────────────────────────────────
MODEL_NAME = "distilbert-base-uncased-finetuned-sst-2-english"

# ─── Score Bounds (mirrors on-chain SentimentOracle.sol) ────
MIN_SCORE = -100
MAX_SCORE = 100

# ─── Ingestion Limits ──────────────────────────────────────
MAX_POSTS = 50

# ─── Smoothing (EMA) ──────────────────────────────────────
EMA_ALPHA = 0.3

# ─── Scoring Weights ──────────────────────────────────────
ENGAGEMENT_WEIGHT_MULTIPLIER = 1.5

# ─── Anti-Spam / Quality Filters ──────────────────────────
MIN_POST_WORD_COUNT = 5

# ─── Multi-Source Ingestion ──────────────────────────────
SUBREDDITS = ["cryptocurrency", "bitcoin", "ethtrader", "defi"]
INGESTION_MODE = "hybrid"                # "mock" | "rss" | "twitter" | "hybrid"
RSS_FETCH_INTERVAL = 30                 # seconds between RSS fetches
TWITTER_SAMPLE_SIZE = 50                # posts sampled per cycle from Sentiment140
DEDUP_WINDOW_SIZE = 500                 # rolling cross-cycle dedup hash window
USER_AGENT = "SentimentOracle/1.0 (Research Project)"
TWITTER_DATASET_PATH = "app/data/training.1600000.processed.noemoticon.csv"
REDDIT_ENGAGEMENT_BASELINE = 10         # fixed engagement proxy for RSS posts

# ─── Reddit Anti-Spam ────────────────────────────────────
REDDIT_SPAM_PHRASES = [
    "click here",
    "buy now",
    "limited time",
    "act fast",
    "free money",
    "guaranteed profit",
]
