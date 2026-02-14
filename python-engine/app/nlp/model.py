"""
model.py — Model Loader Layer (Singleton)
============================================
Loads the HuggingFace transformer once at startup and reuses the instance.
Prevents GPU/CPU thrashing from repeated model loading.
"""

from transformers import pipeline as hf_pipeline
from app.config import MODEL_NAME

_model_instance = None


def get_model():
    """
    Returns the singleton sentiment-analysis pipeline.
    Loads the model on first call, reuses on subsequent calls.
    """
    global _model_instance

    if _model_instance is None:
        _model_instance = hf_pipeline(
            "sentiment-analysis",
            model=MODEL_NAME,
            truncation=True,
        )

    return _model_instance
