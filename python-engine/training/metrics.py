"""
training/metrics.py — Unified Metric Engine
==========================================
Computes structured, JSON-serializable metrics for both text and financial evaluations.
"""

import numpy as np
from typing import Dict, Any, List
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix
from scipy.stats import pearsonr
from training.config import CORRELATION_MIN_SAMPLES, CORRELATION_EPSILON


def classification_metrics(
    y_true: List[int],
    y_pred: List[int],
    total_samples: int
) -> Dict[str, Any]:
    """
    Compute classification metrics for text evaluation.
    
    Metrics:
    - Accuracy
    - Precision
    - Recall
    - F1
    - Confusion Matrix
    - Class imbalance ratio
    
    Args:
        y_true: Ground truth labels
        y_pred: Predicted labels
        total_samples: Total samples processed
    
    Returns:
        Structured metrics dictionary (JSON-serializable)
    """
    y_true = np.array(y_true)
    y_pred = np.array(y_pred)
    
    accuracy = float(accuracy_score(y_true, y_pred))
    precision = float(precision_score(y_true, y_pred, zero_division=0, average='weighted'))
    recall = float(recall_score(y_true, y_pred, zero_division=0, average='weighted'))
    f1 = float(f1_score(y_true, y_pred, zero_division=0, average='weighted'))
    
    # Confusion matrix
    cm = confusion_matrix(y_true, y_pred)
    cm_dict = {
        "true_negatives": int(cm[0, 0]),
        "false_positives": int(cm[0, 1]),
        "false_negatives": int(cm[1, 0]),
        "true_positives": int(cm[1, 1])
    }
    
    # Class imbalance
    positive_ratio = float(np.mean(y_true))
    
    return {
        "dataset_type": "TEXT",
        "accuracy": round(accuracy, 4),
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1": round(f1, 4),
        "confusion_matrix": cm_dict,
        "total_samples": total_samples,
        "positive_ratio": round(positive_ratio, 4)
    }


def directional_accuracy(
    market_direction: np.ndarray,
    sentiment_direction: np.ndarray
) -> float:
    """
    Calculate directional accuracy.
    
    Args:
        market_direction: Binary array (1 = up, 0 = down/flat)
        sentiment_direction: Binary array (1 = bullish, 0 = bearish)
    
    Returns:
        Directional accuracy (0-1)
    """
    if len(market_direction) < CORRELATION_MIN_SAMPLES:
        return 0.0
    
    accuracy = np.mean(market_direction == sentiment_direction)
    return float(round(accuracy, 4))


def correlation_metrics(
    x: np.ndarray,
    y: np.ndarray
) -> Dict[str, float]:
    """
    Calculate Pearson correlation with numeric stability.
    
    Args:
        x: First numeric array
        y: Second numeric array
    
    Returns:
        {"correlation": float, "p_value": float}
    """
    if len(x) < CORRELATION_MIN_SAMPLES:
        return {"correlation": 0.0, "p_value": 1.0}
    
    try:
        x = np.asarray(x, dtype=float)
        y = np.asarray(y, dtype=float)
        
        # Remove NaN and inf values
        valid_mask = np.isfinite(x) & np.isfinite(y)
        x = x[valid_mask]
        y = y[valid_mask]
        
        if len(x) < CORRELATION_MIN_SAMPLES:
            return {"correlation": 0.0, "p_value": 1.0}
        
        # Check for sufficient variance
        if np.std(x) < CORRELATION_EPSILON or np.std(y) < CORRELATION_EPSILON:
            return {"correlation": 0.0, "p_value": 1.0}
        
        corr, p_value = pearsonr(x, y)
        return {
            "correlation": round(float(corr), 4),
            "p_value": round(float(p_value), 4)
        }
    except Exception:
        return {"correlation": 0.0, "p_value": 1.0}


def weighted_correlation(
    x: np.ndarray,
    y: np.ndarray,
    weights: np.ndarray
) -> Dict[str, float]:
    """
    Calculate weighted correlation using volume or confidence weights.
    
    Args:
        x: First numeric array
        y: Second numeric array
        weights: Weight array (e.g., trading volume, confidence)
    
    Returns:
        {"weighted_correlation": float}
    """
    if len(x) < CORRELATION_MIN_SAMPLES:
        return {"weighted_correlation": 0.0}
    
    try:
        x = np.asarray(x, dtype=float)
        y = np.asarray(y, dtype=float)
        weights = np.asarray(weights, dtype=float)
        
        # Normalize weights
        weights = weights / (np.sum(weights) + CORRELATION_EPSILON)
        
        # Calculate weighted mean
        x_mean = np.sum(x * weights)
        y_mean = np.sum(y * weights)
        
        # Calculate weighted covariance and std
        cov = np.sum(weights * (x - x_mean) * (y - y_mean))
        std_x = np.sqrt(np.sum(weights * (x - x_mean) ** 2))
        std_y = np.sqrt(np.sum(weights * (y - y_mean) ** 2))
        
        if std_x < CORRELATION_EPSILON or std_y < CORRELATION_EPSILON:
            return {"weighted_correlation": 0.0}
        
        w_corr = cov / (std_x * std_y)
        return {"weighted_correlation": round(float(w_corr), 4)}
    except Exception:
        return {"weighted_correlation": 0.0}


def financial_metrics(
    directional_accuracy: float,
    sentiment_price_correlation: float,
    weighted_correlation: float,
    average_volatility: float,
    sample_size: int
) -> Dict[str, Any]:
    """
    Compile financial evaluation metrics.
    
    Args:
        directional_accuracy: Percentage of correct price direction predictions
        sentiment_price_correlation: Pearson correlation between sentiment and price change
        weighted_correlation: Volume-weighted correlation
        average_volatility: Mean volatility index
        sample_size: Number of samples evaluated
    
    Returns:
        Structured metrics dictionary (JSON-serializable)
    """
    return {
        "dataset_type": "FINANCIAL",
        "directional_accuracy": round(directional_accuracy, 4),
        "sentiment_price_correlation": round(sentiment_price_correlation, 4),
        "weighted_correlation": round(weighted_correlation, 4),
        "average_volatility": round(average_volatility, 4),
        "sample_size": int(sample_size)
    }
