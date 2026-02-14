"""
training/dataset_loader.py — Dataset Loading Layer
==================================================
Standardizes and loads both TEXT and FINANCIAL datasets.
"""

import pandas as pd
from typing import Optional, Tuple
from training.config import (
    SENTIMENT140_PATH,
    CRYPTO_SENTIMENT_PATH,
    TEXT_MAX_SAMPLES,
    FINANCIAL_MAX_SAMPLES,
    RANDOM_SEED
)


def load_sentiment140() -> pd.DataFrame:
    """
    Load Sentiment140 dataset.
    
    Schema:
        label, id, date, query, user, text
        - label: 0 (negative), 4 (positive)
        - text: raw tweet text
    
    Returns:
        DataFrame with standardized columns: text, label
    """
    df = pd.read_csv(SENTIMENT140_PATH, encoding='latin-1')
    
    # Map original column names to standard names
    if df.columns[0] == 'label' and df.columns[5] == 'text':
        # Original Sentiment140 format
        df = df[['text', 'label']]
        # Normalize labels: 0 -> 0 (negative), 4 -> 1 (positive)
        df['label'] = (df['label'] > 2).astype(int)
    else:
        raise ValueError(f"Unexpected Sentiment140 schema. Columns: {df.columns.tolist()}")
    
    # Limit samples if configured
    if TEXT_MAX_SAMPLES is not None:
        df = df.sample(n=min(len(df), TEXT_MAX_SAMPLES), random_state=RANDOM_SEED)
    
    # Remove rows with missing text
    df = df.dropna(subset=['text'])
    df['text'] = df['text'].astype(str)
    
    return df.reset_index(drop=True)


def load_crypto_sentiment() -> pd.DataFrame:
    """
    Load Crypto Financial Sentiment dataset.
    
    Schema:
        timestamp, cryptocurrency, current_price_usd, price_change_24h_percent,
        trading_volume_24h, market_cap_usd, social_sentiment_score, 
        news_sentiment_score, news_impact_score, social_mentions_count,
        fear_greed_index, volatility_index, rsi_technical_indicator, 
        prediction_confidence
    
    Returns:
        DataFrame with standardized columns for financial evaluation
    """
    df = pd.read_csv(CRYPTO_SENTIMENT_PATH)
    
    # Verify required columns exist
    required_cols = {
        'social_sentiment_score',
        'news_sentiment_score',
        'price_change_24h_percent',
        'trading_volume_24h',
        'volatility_index'
    }
    
    missing_cols = required_cols - set(df.columns)
    if missing_cols:
        raise ValueError(f"Missing required columns: {missing_cols}")
    
    # Limit samples if configured
    if FINANCIAL_MAX_SAMPLES is not None:
        df = df.sample(n=min(len(df), FINANCIAL_MAX_SAMPLES), random_state=RANDOM_SEED)
    
    # Drop rows with missing critical values
    df = df.dropna(subset=list(required_cols))
    
    # Ensure numeric columns are float
    for col in required_cols:
        df[col] = pd.to_numeric(df[col], errors='coerce')
    
    return df.reset_index(drop=True)


def load_dataset(dataset_name: str) -> Tuple[pd.DataFrame, str]:
    """
    Load dataset by name.
    
    Args:
        dataset_name: 'sentiment140' or 'crypto'
    
    Returns:
        (DataFrame, dataset_display_name)
    """
    if dataset_name.lower() in ['sentiment140', 'text', 'sentiment']:
        return load_sentiment140(), 'Sentiment140'
    elif dataset_name.lower() in ['crypto', 'financial', 'crypto_sentiment']:
        return load_crypto_sentiment(), 'Crypto Sentiment'
    else:
        raise ValueError(f"Unknown dataset: {dataset_name}. Use 'sentiment140' or 'crypto'")
