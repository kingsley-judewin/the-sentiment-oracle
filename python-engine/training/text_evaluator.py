"""
training/text_evaluator.py — Sentiment Classification Evaluator
===============================================================
Evaluates NLP model accuracy on Sentiment140 dataset.
"""

import sys
import os
import numpy as np
from typing import Dict, Any, List

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.nlp.model import get_model
from training.dataset_loader import load_dataset
from training.preprocess import preprocess_text_dataset
from training.metrics import classification_metrics
from training.config import TEXT_BATCH_SIZE


def evaluate_text_dataset() -> Dict[str, Any]:
    """
    Evaluate sentiment classification model on Sentiment140.
    
    Pipeline:
    1. Load Sentiment140 dataset
    2. Apply cleaning and preprocessing
    3. Batch inference using runtime model
    4. Map predictions (0 = negative, 1 = positive)
    5. Compute metrics
    
    Returns:
        Structured metrics dictionary with:
        - accuracy, precision, recall, f1
        - confusion matrix
        - class imbalance ratio
        - sample statistics
    """
    # Load dataset
    raw_df, dataset_name = load_dataset('sentiment140')
    
    # Preprocess
    df = preprocess_text_dataset(raw_df)
    
    total_samples = len(df)
    
    if total_samples == 0:
        raise ValueError("No valid samples after preprocessing")
    
    # Load model
    model = get_model()
    
    # Batch inference
    texts = df['cleaned_text'].tolist()
    predictions = []
    
    for i in range(0, len(texts), TEXT_BATCH_SIZE):
        batch = texts[i:i + TEXT_BATCH_SIZE]
        batch_predictions = model(batch)
        
        # Map predictions: NEGATIVE -> 0, POSITIVE -> 1
        for pred in batch_predictions:
            label = 1 if pred['label'] == 'POSITIVE' else 0
            predictions.append(label)
    
    # Ground truth labels (already normalized: 0 = negative, 1 = positive)
    ground_truth = df['label'].tolist()
    
    # Compute metrics
    metrics = classification_metrics(
        y_true=ground_truth,
        y_pred=predictions,
        total_samples=total_samples
    )
    
    return metrics


if __name__ == "__main__":
    result = evaluate_text_dataset()
    import json
    print(json.dumps(result, indent=2))
