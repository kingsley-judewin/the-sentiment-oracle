"""
training/experiment_logger.py — Structured Experiment Tracking
=============================================================
Logs experiment metadata and metrics in JSON format.
"""

import json
import os
from datetime import datetime
from typing import Dict, Any
from training.config import EXPERIMENT_LOG_FILE, RANDOM_SEED, MODEL_NAME


class ExperimentLogger:
    """Handles structured logging of experiments."""
    
    def __init__(self):
        """Initialize logger."""
        pass
    
    @staticmethod
    def _ensure_log_file_exists():
        """Create log file if it doesn't exist."""
        os.makedirs(os.path.dirname(EXPERIMENT_LOG_FILE), exist_ok=True)
    
    @staticmethod
    def log_experiment(
        dataset_name: str,
        dataset_type: str,
        metrics: Dict[str, Any],
        runtime_seconds: float
    ) -> None:
        """
        Log experiment metadata and metrics.
        
        Args:
            dataset_name: Display name of dataset (e.g., "Sentiment140")
            dataset_type: "TEXT" or "FINANCIAL"
            metrics: Metrics dictionary from evaluator
            runtime_seconds: Evaluation runtime in seconds
        """
        ExperimentLogger._ensure_log_file_exists()
        
        # Create experiment entry
        entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "dataset_name": dataset_name,
            "dataset_type": dataset_type,
            "model_name": MODEL_NAME,
            "random_seed": RANDOM_SEED,
            "runtime_seconds": round(runtime_seconds, 2),
            "metrics": metrics
        }
        
        # Read existing log or start new
        try:
            if os.path.exists(EXPERIMENT_LOG_FILE):
                with open(EXPERIMENT_LOG_FILE, 'r') as f:
                    log_data = json.load(f)
                    if not isinstance(log_data, list):
                        log_data = [log_data]
            else:
                log_data = []
        except (json.JSONDecodeError, FileNotFoundError):
            log_data = []
        
        # Append new entry
        log_data.append(entry)
        
        # Write back
        with open(EXPERIMENT_LOG_FILE, 'w') as f:
            json.dump(log_data, f, indent=2)
    
    @staticmethod
    def get_latest_experiment() -> Dict[str, Any]:
        """
        Get the most recent experiment entry.
        
        Returns:
            Latest experiment dictionary or None
        """
        try:
            if not os.path.exists(EXPERIMENT_LOG_FILE):
                return None
            
            with open(EXPERIMENT_LOG_FILE, 'r') as f:
                log_data = json.load(f)
                if isinstance(log_data, list) and len(log_data) > 0:
                    return log_data[-1]
                return None
        except (json.JSONDecodeError, FileNotFoundError):
            return None
    
    @staticmethod
    def get_all_experiments() -> list:
        """
        Get all experiment entries.
        
        Returns:
            List of experiment dictionaries
        """
        try:
            if not os.path.exists(EXPERIMENT_LOG_FILE):
                return []
            
            with open(EXPERIMENT_LOG_FILE, 'r') as f:
                log_data = json.load(f)
                if isinstance(log_data, list):
                    return log_data
                return [log_data]
        except (json.JSONDecodeError, FileNotFoundError):
            return []
