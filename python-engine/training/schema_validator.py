"""
training/schema_validator.py — Dataset Type Detection Layer
===========================================================
Automatically detects dataset schema and classifies as TEXT or FINANCIAL.
"""

import pandas as pd
from enum import Enum
from typing import Tuple


class DatasetType(Enum):
    """Supported dataset types."""
    TEXT = "TEXT"
    FINANCIAL = "FINANCIAL"
    UNKNOWN = "UNKNOWN"


def detect_dataset_type(df: pd.DataFrame) -> Tuple[DatasetType, dict]:
    """
    Inspect column names and detect dataset type.
    
    Returns:
        (DatasetType, metadata_dict)
    """
    cols = set(df.columns)
    
    # Check for TEXT dataset indicators
    text_indicators = {"text", "content", "message", "tweet"}
    if any(indicator in cols for indicator in text_indicators):
        metadata = {
            "detected_type": "TEXT",
            "text_column": next((col for col in cols if col in text_indicators), None),
            "columns_found": list(cols)
        }
        return DatasetType.TEXT, metadata
    
    # Check for FINANCIAL dataset indicators
    financial_indicators = {
        "social_sentiment_score",
        "news_sentiment_score",
        "current_price_usd",
        "price_change_24h_percent",
        "trading_volume_24h",
        "market_cap_usd"
    }
    
    if financial_indicators.intersection(cols):
        metadata = {
            "detected_type": "FINANCIAL",
            "financial_columns": list(financial_indicators.intersection(cols)),
            "columns_found": list(cols)
        }
        return DatasetType.FINANCIAL, metadata
    
    # Unknown type
    metadata = {
        "detected_type": "UNKNOWN",
        "columns_found": list(cols)
    }
    return DatasetType.UNKNOWN, metadata


def validate_text_dataset(df: pd.DataFrame) -> bool:
    """Validate TEXT dataset has required columns."""
    required = {"text"}
    return required.issubset(set(df.columns))


def validate_financial_dataset(df: pd.DataFrame) -> bool:
    """Validate FINANCIAL dataset has required columns."""
    required = {
        "social_sentiment_score",
        "news_sentiment_score",
        "price_change_24h_percent"
    }
    return required.issubset(set(df.columns))
