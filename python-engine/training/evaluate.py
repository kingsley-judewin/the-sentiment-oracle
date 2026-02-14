"""
training/evaluate.py — Intelligent Evaluation Router
===================================================
Main entry point for dataset evaluation.

Usage:
    python training/evaluate.py --dataset sentiment140
    python training/evaluate.py --dataset crypto
"""

import sys
import os
import json
import argparse
import time
from typing import Dict, Any

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from training.dataset_loader import load_dataset
from training.schema_validator import detect_dataset_type, DatasetType
from training.experiment_logger import ExperimentLogger
from training.config import TEXT_EVAL_OUTPUT_FILE, FINANCIAL_EVAL_OUTPUT_FILE


def evaluate_dataset(dataset_name: str, verbose: bool = True) -> Dict[str, Any]:
    """
    Load dataset, detect type, route to appropriate evaluator.
    
    Args:
        dataset_name: 'sentiment140' or 'crypto'
        verbose: Print progress messages
    
    Returns:
        Metrics dictionary
    """
    start_time = time.time()
    
    try:
        # Step 1: Load dataset
        if verbose:
            print(f"\n📊 Loading {dataset_name}...")
        
        df, display_name = load_dataset(dataset_name)
        
        if verbose:
            print(f"   ✓ Loaded {len(df)} rows")
        
        # Step 2: Validate schema
        if verbose:
            print(f"\n🔍 Detecting dataset type...")
        
        dataset_type, metadata = detect_dataset_type(df)
        
        if dataset_type == DatasetType.UNKNOWN:
            raise ValueError(f"Unknown dataset type. Columns: {metadata['columns_found']}")
        
        if verbose:
            print(f"   ✓ Detected: {dataset_type.value}")
        
        # Step 3: Route to appropriate evaluator
        if dataset_type == DatasetType.TEXT:
            if verbose:
                print(f"\n🧠 Running text classification evaluation...")
            
            # Import here to avoid loading transformers unless needed
            from training.text_evaluator import evaluate_text_dataset
            metrics = evaluate_text_dataset()
            output_file = TEXT_EVAL_OUTPUT_FILE
            
        elif dataset_type == DatasetType.FINANCIAL:
            if verbose:
                print(f"\n💰 Running financial oracle alignment evaluation...")
            
            from training.financial_evaluator import evaluate_financial_dataset
            metrics = evaluate_financial_dataset()
            output_file = FINANCIAL_EVAL_OUTPUT_FILE
        
        # Step 4: Log experiment
        runtime = time.time() - start_time
        
        if verbose:
            print(f"\n📝 Logging experiment...")
        
        ExperimentLogger.log_experiment(
            dataset_name=display_name,
            dataset_type=dataset_type.value,
            metrics=metrics,
            runtime_seconds=runtime
        )
        
        # Step 5: Save metrics to output file
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        with open(output_file, 'w') as f:
            json.dump(metrics, f, indent=2)
        
        if verbose:
            print(f"   ✓ Saved to: {output_file}")
        
        # Step 6: Display results
        if verbose:
            print(f"\n✅ Evaluation complete in {runtime:.2f}s\n")
            print("📈 Results:")
            print(json.dumps(metrics, indent=2))
        
        return metrics
    
    except Exception as e:
        print(f"\n❌ Error during evaluation: {str(e)}", file=sys.stderr)
        raise


def main():
    """CLI interface for evaluation."""
    parser = argparse.ArgumentParser(
        description="Evaluate Sentiment Oracle models on different datasets"
    )
    parser.add_argument(
        '--dataset',
        type=str,
        choices=['sentiment140', 'crypto', 'sentiment', 'financial', 'text'],
        required=True,
        help='Dataset to evaluate: sentiment140/sentiment/text or crypto/financial'
    )
    parser.add_argument(
        '--quiet',
        action='store_true',
        help='Suppress progress messages'
    )
    
    args = parser.parse_args()
    
    # Normalize dataset name
    if args.dataset in ['sentiment', 'text']:
        dataset_name = 'sentiment140'
    elif args.dataset in ['financial']:
        dataset_name = 'crypto'
    else:
        dataset_name = args.dataset
    
    # Run evaluation
    try:
        metrics = evaluate_dataset(dataset_name, verbose=not args.quiet)
        
        # For quiet mode, just output JSON
        if args.quiet:
            print(json.dumps(metrics))
        
        return 0
    except Exception as e:
        if args.quiet:
            print(json.dumps({"error": str(e)}))
        return 1


if __name__ == "__main__":
    sys.exit(main())
