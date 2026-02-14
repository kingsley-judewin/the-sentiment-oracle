"""
training/preprocess.py — Preprocessing Layer
============================================
Reuses runtime cleaner for consistency. No duplicate logic.
"""

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.nlp.cleaner import clean_text
from training.config import MIN_POST_WORD_COUNT
import pandas as pd


def preprocess_text_dataset(df: pd.DataFrame) -> pd.DataFrame:
    """
    Preprocess text dataset for evaluation.
    
    Applies:
    - Text cleaning (via runtime cleaner)
    - Word count filtering
    - Duplicate removal
    
    Args:
        df: DataFrame with 'text' column
    
    Returns:
        Cleaned DataFrame with 'cleaned_text' column
    """
    # Create copy to avoid modifying original
    df = df.copy()
    
    # Apply cleaning to each text
    df['cleaned_text'] = df['text'].astype(str).apply(clean_text)
    
    # Filter by word count
    df['word_count'] = df['cleaned_text'].str.split().str.len()
    df = df[df['word_count'] >= MIN_POST_WORD_COUNT].copy()
    
    # Drop duplicates by cleaned text
    df = df.drop_duplicates(subset=['cleaned_text'])
    
    return df.reset_index(drop=True)


def preprocess_financial_dataset(df: pd.DataFrame) -> pd.DataFrame:
    """
    Preprocess financial dataset.
    
    Ensures:
    - Numeric columns are float
    - No NaN values in critical fields
    - Optional: outlier removal
    
    Args:
        df: DataFrame with financial metrics
    
    Returns:
        Cleaned DataFrame
    """
    df = df.copy()
    
    # Ensure critical numeric columns
    numeric_cols = [
        'social_sentiment_score',
        'news_sentiment_score',
        'price_change_24h_percent',
        'trading_volume_24h',
        'volatility_index'
    ]
    
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
    
    # Drop rows with NaN in critical columns
    df = df.dropna(subset=numeric_cols, how='any')
    
    # Optional: Remove extreme outliers (3 std devs)
    for col in numeric_cols:
        if col in df.columns:
            mean = df[col].mean()
            std = df[col].std()
            if std > 0:
                df = df[
                    (df[col] >= mean - 3*std) &
                    (df[col] <= mean + 3*std)
                ]
    
    return df.reset_index(drop=True)
