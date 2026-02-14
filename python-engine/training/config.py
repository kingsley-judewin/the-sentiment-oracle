"""
training/config.py — Training Configuration
=============================================
All tunable parameters for evaluation pipeline.
"""

import os

# ─── Paths ──────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "..", "app", "data")
MODELS_DIR = os.path.join(BASE_DIR, "..", "models", "baseline")

# Ensure models directory exists
os.makedirs(MODELS_DIR, exist_ok=True)

# ─── Model Configuration ────────────────────────────────────
MODEL_NAME = "distilbert-base-uncased-finetuned-sst-2-english"

# ─── Dataset Paths ──────────────────────────────────────────
SENTIMENT140_PATH = os.path.join(DATA_DIR, "training.1600000.processed.noemoticon.csv")
CRYPTO_SENTIMENT_PATH = os.path.join(DATA_DIR, "crypto_sentiment_prediction_dataset.csv")

# ─── Text Evaluation Parameters ──────────────────────────────
TEXT_BATCH_SIZE = 32
TEXT_MAX_SAMPLES = None  # Set to None to use all samples, or limit for testing

# ─── Financial Evaluation Parameters ────────────────────────
FINANCIAL_BATCH_SIZE = 64
FINANCIAL_MAX_SAMPLES = None  # Set to None to use all samples

# Financial score weights
SOCIAL_SENTIMENT_WEIGHT = 0.6
NEWS_SENTIMENT_WEIGHT = 0.4

# Market direction threshold
PRICE_CHANGE_THRESHOLD = 0.0  # 0% change = neutral

# ─── Data Processing ────────────────────────────────────────
MIN_POST_WORD_COUNT = 5
RANDOM_SEED = 42

# ─── Experiment Logging ─────────────────────────────────────
EXPERIMENT_LOG_FILE = os.path.join(MODELS_DIR, "experiment_log.json")
TEXT_EVAL_OUTPUT_FILE = os.path.join(MODELS_DIR, "text_eval.json")
FINANCIAL_EVAL_OUTPUT_FILE = os.path.join(MODELS_DIR, "financial_eval.json")

# ─── Numeric Stability ──────────────────────────────────────
CORRELATION_MIN_SAMPLES = 10
CORRELATION_EPSILON = 1e-10
