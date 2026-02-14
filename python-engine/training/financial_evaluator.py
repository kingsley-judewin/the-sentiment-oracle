"""
training/financial_evaluator.py — Oracle Alignment Evaluator
===========================================================
Evaluates sentiment oracle alignment with actual market movements.
"""

import sys
import os
import numpy as np
import pandas as pd
from typing import Dict, Any

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from training.dataset_loader import load_dataset
from training.preprocess import preprocess_financial_dataset
from training.metrics import (
    directional_accuracy,
    correlation_metrics,
    weighted_correlation,
    financial_metrics
)
from training.config import (
    SOCIAL_SENTIMENT_WEIGHT,
    NEWS_SENTIMENT_WEIGHT,
    PRICE_CHANGE_THRESHOLD
)


def evaluate_financial_dataset() -> Dict[str, Any]:
    """
    Evaluate sentiment oracle alignment with market data.
    
    Financial Evaluation Logic:
    
    Step 1: Create Oracle Score Proxy
        combined_sentiment = (0.6 * social_sentiment_score) + (0.4 * news_sentiment_score)
    
    Step 2: Define Market Direction Label
        market_direction = 1 if price_change_24h_percent > 0 else 0
    
    Step 3: Convert Sentiment into Prediction
        sentiment_direction = 1 if combined_sentiment > 0 else 0
    
    Step 4: Evaluate Predictive Alignment
        - Directional accuracy
        - Sentiment-price correlation
        - Volume-weighted correlation
        - Volatility-adjusted signal strength
    
    Returns:
        Structured metrics dictionary with:
        - directional_accuracy
        - sentiment_price_correlation
        - weighted_correlation
        - average_volatility
        - sample_size
    """
    # Load dataset
    raw_df, dataset_name = load_dataset('crypto')
    
    # Preprocess
    df = preprocess_financial_dataset(raw_df)
    
    sample_size = len(df)
    
    if sample_size == 0:
        raise ValueError("No valid samples after preprocessing")
    
    # Step 1: Create unified sentiment metric (Oracle Score Proxy)
    df['combined_sentiment'] = (
        SOCIAL_SENTIMENT_WEIGHT * df['social_sentiment_score'] +
        NEWS_SENTIMENT_WEIGHT * df['news_sentiment_score']
    )
    
    # Step 2: Define Market Direction (Ground Truth)
    # 1 = price went up, 0 = price went down or stayed flat
    df['market_direction'] = (df['price_change_24h_percent'] > PRICE_CHANGE_THRESHOLD).astype(int)
    
    # Step 3: Convert Sentiment into Direction Prediction
    # 1 = bullish (positive sentiment), 0 = bearish (negative sentiment)
    df['sentiment_direction'] = (df['combined_sentiment'] > 0).astype(int)
    
    # Step 4: Evaluate Predictive Alignment
    
    # Metric 1: Directional Accuracy
    market_dir = df['market_direction'].values
    sentiment_dir = df['sentiment_direction'].values
    dir_accuracy = directional_accuracy(market_dir, sentiment_dir)
    
    # Metric 2: Sentiment-Price Correlation
    # Correlation between combined sentiment score and actual price change
    sentiment_corr_dict = correlation_metrics(
        x=df['combined_sentiment'].values,
        y=df['price_change_24h_percent'].values
    )
    sentiment_price_corr = sentiment_corr_dict['correlation']
    
    # Metric 3: Volume-Weighted Correlation
    # Weight correlation by trading volume (higher volume = more reliable signal)
    if 'trading_volume_24h' in df.columns:
        volume_weights = df['trading_volume_24h'].values
        # Normalize volumes to [1, 10] scale for reasonable weights
        volume_min = volume_weights.min()
        volume_max = volume_weights.max()
        if volume_max > volume_min:
            volume_weights = 1 + 9 * (volume_weights - volume_min) / (volume_max - volume_min)
        else:
            volume_weights = np.ones_like(volume_weights)
    else:
        volume_weights = np.ones(len(df))
    
    weighted_corr_dict = weighted_correlation(
        x=df['combined_sentiment'].values,
        y=df['price_change_24h_percent'].values,
        weights=volume_weights
    )
    weighted_corr = weighted_corr_dict['weighted_correlation']
    
    # Metric 4: Average Volatility (Signal Strength Context)
    if 'volatility_index' in df.columns:
        avg_volatility = float(df['volatility_index'].mean())
    else:
        avg_volatility = 0.0
    
    # Compile metrics
    metrics = financial_metrics(
        directional_accuracy=dir_accuracy,
        sentiment_price_correlation=sentiment_price_corr,
        weighted_correlation=weighted_corr,
        average_volatility=avg_volatility,
        sample_size=sample_size
    )
    
    return metrics


if __name__ == "__main__":
    result = evaluate_financial_dataset()
    import json
    print(json.dumps(result, indent=2))
