"""
model.py — Model Loader Layer (Singleton)
============================================
Loads the HuggingFace transformer once on first request and reuses the instance.
Prevents GPU/CPU thrashing from repeated model loading.
Heavy imports (torch, transformers) are deferred to keep server startup fast.
"""

from app.config import MODEL_NAME

_model_instance = None


def get_model():
    """
    Returns the singleton sentiment-analysis pipeline.
    Loads the model on first call, reuses on subsequent calls.
    Heavy imports happen here (not at module level) so the server
    can bind to its port immediately on Render/Railway.
    """
    global _model_instance

    if _model_instance is None:
        from transformers import pipeline as hf_pipeline
        _model_instance = hf_pipeline(
            "sentiment-analysis",
            model=MODEL_NAME,
            truncation=True,
        )

    return _model_instance

