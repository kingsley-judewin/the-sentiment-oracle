"""
training — Model Evaluation Package
===================================
Training and evaluation pipeline for Sentiment Oracle.
"""

# Lazy imports to avoid circular dependencies and long import times
def __getattr__(name):
    if name == 'detect_dataset_type':
        from training.schema_validator import detect_dataset_type
        return detect_dataset_type
    elif name == 'DatasetType':
        from training.schema_validator import DatasetType
        return DatasetType
    elif name == 'load_dataset':
        from training.dataset_loader import load_dataset
        return load_dataset
    elif name == 'evaluate_text_dataset':
        from training.text_evaluator import evaluate_text_dataset
        return evaluate_text_dataset
    elif name == 'evaluate_financial_dataset':
        from training.financial_evaluator import evaluate_financial_dataset
        return evaluate_financial_dataset
    elif name == 'ExperimentLogger':
        from training.experiment_logger import ExperimentLogger
        return ExperimentLogger
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

__all__ = [
    'detect_dataset_type',
    'DatasetType',
    'load_dataset',
    'evaluate_text_dataset',
    'evaluate_financial_dataset',
    'ExperimentLogger'
]
