# Sentiment Oracle Training & Evaluation Pipeline

Comprehensive training/evaluation architecture for the Sentiment Oracle project. This module evaluates the sentiment analysis model on two distinct dataset types with different evaluation frameworks.

## 📊 Dataset Types

### Type A: TEXT - Sentiment140 (Text Classification)
**Purpose:** Validate pure NLP model accuracy on sentiment classification

**Schema:**
```
label,id,date,query,user,text
0,1467810369,...,"@switchfoot http..."
```

**Properties:**
- Binary sentiment labels (0 = negative, 4 = positive)
- Pure text classification dataset
- Tests model accuracy and precision on unseen tweets

**Evaluation Output:**
```json
{
  "dataset_type": "TEXT",
  "accuracy": 0.87,
  "precision": 0.85,
  "recall": 0.88,
  "f1": 0.86,
  "confusion_matrix": {
    "true_negatives": 4200,
    "false_positives": 600,
    "false_negatives": 750,
    "true_positives": 5450
  },
  "total_samples": 11000,
  "positive_ratio": 0.52
}
```

### Type B: FINANCIAL - Crypto Sentiment (Oracle Alignment)
**Purpose:** Validate oracle sentiment signals align with actual market movements

**Schema:**
```
timestamp, cryptocurrency, current_price_usd, price_change_24h_percent,
trading_volume_24h, market_cap_usd, social_sentiment_score, 
news_sentiment_score, news_impact_score, social_mentions_count,
fear_greed_index, volatility_index, rsi_technical_indicator, 
prediction_confidence
```

**Properties:**
- Pre-computed sentiment scores (no raw text)
- Market movement metrics
- Tests predictive alignment with financial data

**Evaluation Output:**
```json
{
  "dataset_type": "FINANCIAL",
  "directional_accuracy": 0.64,
  "sentiment_price_correlation": 0.41,
  "weighted_correlation": 0.46,
  "average_volatility": 0.72,
  "sample_size": 2013
}
```

## 🏗️ Architecture

```
training/
├── __init__.py                      # Package initialization
├── config.py                        # All configuration & thresholds
├── schema_validator.py              # Dataset type detection
├── dataset_loader.py                # Standardized dataset loading
├── preprocess.py                    # Data cleaning & preprocessing
├── metrics.py                       # Unified metric computation
├── text_evaluator.py                # TEXT dataset evaluator
├── financial_evaluator.py           # FINANCIAL dataset evaluator
├── experiment_logger.py             # Structured experiment tracking
└── evaluate.py                      # Main evaluation router (CLI)
```

Output structure:
```
models/baseline/
├── experiment_log.json              # All experiment runs
├── text_eval.json                   # Latest TEXT evaluation
└── financial_eval.json              # Latest FINANCIAL evaluation
```

## 📘 Module Reference

### 1. `config.py` — Centralized Configuration

All thresholds, paths, and tunable parameters:

```python
# Dataset Paths
SENTIMENT140_PATH = "app/data/training.1600000.processed.noemoticon.csv"
CRYPTO_SENTIMENT_PATH = "app/data/crypto_sentiment_prediction_dataset.csv"

# Text Evaluation
TEXT_BATCH_SIZE = 32
TEXT_MAX_SAMPLES = None  # Set to integer to limit

# Financial Evaluation
SOCIAL_SENTIMENT_WEIGHT = 0.6
NEWS_SENTIMENT_WEIGHT = 0.4
PRICE_CHANGE_THRESHOLD = 0.0

# Output
MODELS_DIR = "models/baseline"
EXPERIMENT_LOG_FILE = f"{MODELS_DIR}/experiment_log.json"
```

### 2. `schema_validator.py` — Auto-Detection

Automatically detects dataset type by inspecting columns:

```python
from training.schema_validator import detect_dataset_type, DatasetType

df = pd.read_csv("crypto_data.csv")
dtype, metadata = detect_dataset_type(df)

if dtype == DatasetType.FINANCIAL:
    print("Detected FINANCIAL dataset")
elif dtype == DatasetType.TEXT:
    print("Detected TEXT dataset")
```

**Detection Logic:**
- TEXT: If "text" column exists → `DatasetType.TEXT`
- FINANCIAL: If columns like `social_sentiment_score`, `price_change_24h_percent` exist → `DatasetType.FINANCIAL`
- Unknown: If neither pattern matches → `DatasetType.UNKNOWN`

### 3. `dataset_loader.py` — Standardized Loading

Loads and normalizes datasets:

```python
from training.dataset_loader import load_dataset

# Load by name
df, display_name = load_dataset('sentiment140')  # or 'crypto'

# Returns standardized DataFrame
# For TEXT: columns=['text', 'label', ...]
# For FINANCIAL: columns=['social_sentiment_score', 'news_sentiment_score', ...]
```

### 4. `preprocess.py` — Data Pipeline

Reuses runtime cleaner for consistency:

```python
from training.preprocess import preprocess_text_dataset, preprocess_financial_dataset

# TEXT preprocessing
df_clean = preprocess_text_dataset(df)
# Returns: cleaned_text column, word_count filtering, deduplication

# FINANCIAL preprocessing
df_clean = preprocess_financial_dataset(df)
# Returns: numeric validation, outlier removal, NaN handling
```

### 5. `metrics.py` — Unified Metric Engine

Computes structured, JSON-serializable metrics:

```python
from training.metrics import classification_metrics, directional_accuracy, correlation_metrics

# Text classification metrics
metrics = classification_metrics(
    y_true=[0, 1, 1, 0],
    y_pred=[0, 1, 0, 0],
    total_samples=4
)
# Returns: accuracy, precision, recall, f1, confusion_matrix, class_imbalance

# Financial correlations
corr_dict = correlation_metrics(
    x=sentiment_scores,
    y=price_changes
)
# Returns: {"correlation": 0.41, "p_value": 0.003}
```

**Key Metrics:**

#### Text Classification
- **Accuracy**: % of correct predictions
- **Precision**: True positives / (True positives + False positives)
- **Recall**: True positives / (True positives + False negatives)
- **F1**: Harmonic mean of precision and recall
- **Confusion Matrix**: TN, FP, FN, TP breakdown
- **Class Imbalance**: Positive ratio in dataset

#### Financial Alignment
- **Directional Accuracy**: % of correct price direction predictions
- **Sentiment-Price Correlation**: Pearson correlation between sentiment and price change
- **Volume-Weighted Correlation**: Correlation weighted by trading volume (higher volume = more reliable)
- **Average Volatility**: Mean volatility index (signal strength context)

### 6. `text_evaluator.py` — Sentiment Classification

Evaluates model on Sentiment140:

```python
from training.text_evaluator import evaluate_text_dataset

metrics = evaluate_text_dataset()
# Returns TEXT type metrics dictionary
```

**Pipeline:**
1. Load Sentiment140 (1.6M tweets)
2. Apply text cleaning (reuses runtime cleaner)
3. Batch inference through NLP model
4. Map predictions (NEGATIVE→0, POSITIVE→1)
5. Compute classification metrics

### 7. `financial_evaluator.py` — Oracle Alignment

Evaluates oracle sentiment-price correlation:

```python
from training.financial_evaluator import evaluate_financial_dataset

metrics = evaluate_financial_dataset()
# Returns FINANCIAL type metrics dictionary
```

**Evaluation Logic:**

#### Step 1: Oracle Score Proxy
```
combined_sentiment = (0.6 * social_sentiment_score) + (0.4 * news_sentiment_score)
```

#### Step 2: Market Direction (Ground Truth)
```
market_direction = 1 if price_change_24h_percent > 0 else 0
```

#### Step 3: Sentiment Direction Prediction
```
sentiment_direction = 1 if combined_sentiment > 0 else 0
```

#### Step 4: Compute Metrics
- Directional accuracy between prediction and actual
- Correlation between combined sentiment and price change
- Volume-weighted correlation (more reliable at higher volumes)
- Volatility as signal strength context

### 8. `experiment_logger.py` — Structured Tracking

Logs all experiments to JSON:

```python
from training.experiment_logger import ExperimentLogger

ExperimentLogger.log_experiment(
    dataset_name="Sentiment140",
    dataset_type="TEXT",
    metrics={...},
    runtime_seconds=45.23
)

# Appends to models/baseline/experiment_log.json
```

**Log Entry Format:**
```json
{
  "timestamp": "2026-02-13T18:37:51.858459",
  "dataset_name": "Sentiment140",
  "dataset_type": "TEXT",
  "model_name": "distilbert-base-uncased-finetuned-sst-2-english",
  "random_seed": 42,
  "runtime_seconds": 45.23,
  "metrics": {...}
}
```

### 9. `evaluate.py` — Main Router

Intelligent evaluation orchestrator with CLI:

```bash
# Evaluate text classification
python training/evaluate.py --dataset sentiment140

# Evaluate financial oracle alignment
python training/evaluate.py --dataset crypto

# Quiet mode (JSON only)
python training/evaluate.py --dataset sentiment140 --quiet
```

**Flow:**
1. Load dataset
2. Detect schema (TEXT or FINANCIAL)
3. Route to appropriate evaluator
4. Log experiment metadata
5. Save metrics to output file
6. Display results

## 🚀 Quick Start

### Installation
```bash
# Install dependencies
pip install pandas numpy scikit-learn scipy transformers torch

# Or from local requirements
pip install -r requirements.txt
```

### Run Evaluations

**Financial Oracle Alignment (Fast - 1-2 seconds)**
```bash
cd python-engine
python training/evaluate.py --dataset crypto
```

**Text Classification (Slower - 1-2 minutes, requires GPU)**
```bash
cd python-engine
python training/evaluate.py --dataset sentiment140
```

### Check Results
```bash
# View latest evaluation
cat models/baseline/financial_eval.json

# View all experiments
cat models/baseline/experiment_log.json
```

## 🧪 Testing & Validation

### Test Financial Evaluator
```bash
python -c "
from training.financial_evaluator import evaluate_financial_dataset
import json
metrics = evaluate_financial_dataset()
print(json.dumps(metrics, indent=2))
"
```

### Test Text Evaluator
```bash
python -c "
from training.text_evaluator import evaluate_text_dataset
import json
metrics = evaluate_text_dataset()
print(json.dumps(metrics, indent=2))
"
```

### Check Dataset Detection
```bash
python -c "
from training.dataset_loader import load_dataset
from training.schema_validator import detect_dataset_type

df, name = load_dataset('crypto')
dtype, meta = detect_dataset_type(df)
print(f'Dataset: {name}')
print(f'Type: {dtype.value}')
"
```

## 📈 Expected Results

### Financial Dataset (2013 samples)
- **Directional Accuracy**: 50-65% (random chance is 50%)
- **Correlation**: 0.0-0.5 (depends on social sentiment quality)
- **Volatility**: 60-100 (market conditions)

### Text Dataset (Sentiment140)
- **Accuracy**: 80-90% (industry standard for `distilbert-finetuned-sst-2`)
- **F1**: 0.80-0.90
- **Precision/Recall**: Balanced near accuracy

## 🎯 Design Principles

1. **Modular Architecture**: Each component has single responsibility
2. **Lazy Imports**: Avoid loading transformers unless needed
3. **Reuse Runtime Logic**: Cleaning uses same logic as production
4. **No Globals**: Pure functions with explicit parameters
5. **Structured Output**: JSON-serializable metrics only
6. **Batch Processing**: No per-row inference
7. **Numeric Stability**: Safe correlation with epsilon
8. **Comprehensive Logging**: All experiments tracked

## 📊 Output Files

### `experiment_log.json`
Cumulative log of all evaluation runs. Append-only structure.

**Structure:**
```json
[
  {
    "timestamp": "ISO-8601",
    "dataset_name": "string",
    "dataset_type": "TEXT|FINANCIAL",
    "model_name": "string",
    "random_seed": "integer",
    "runtime_seconds": "float",
    "metrics": {...}
  },
  ...
]
```

### `text_eval.json` / `financial_eval.json`
Latest evaluation metrics for each dataset type.

**Text Format:**
```json
{
  "dataset_type": "TEXT",
  "accuracy": 0.87,
  "precision": 0.85,
  "recall": 0.88,
  "f1": 0.86,
  "confusion_matrix": {...},
  "total_samples": 50000,
  "positive_ratio": 0.52
}
```

**Financial Format:**
```json
{
  "dataset_type": "FINANCIAL",
  "directional_accuracy": 0.64,
  "sentiment_price_correlation": 0.41,
  "weighted_correlation": 0.46,
  "average_volatility": 0.72,
  "sample_size": 2013
}
```

## 🔍 Troubleshooting

### Long Import Time
Transformers takes ~30 seconds to import on first run. Subsequent runs are faster due to caching.

### OutOfMemory on Text Evaluation
Adjust `TEXT_BATCH_SIZE` in `config.py` (default: 32). Try 16 or 8 for memory-constrained systems.

### Missing Dataset Files
Ensure these files exist:
- `app/data/training.1600000.processed.noemoticon.csv` (Sentiment140)
- `app/data/crypto_sentiment_prediction_dataset.csv` (Crypto)

### GPU/CPU Selection
Transformers automatically uses GPU if available. To force CPU:
```python
import os
os.environ["CUDA_VISIBLE_DEVICES"] = ""
```

## 🛠️ Development

### Adding New Metrics
Edit `metrics.py` and create new metric functions:
```python
def my_new_metric(data):
    # Compute metric
    result = ...
    return float(result)  # Must be JSON serializable
```

### Adding New Dataset
1. Add loader to `dataset_loader.py`
2. Update `schema_validator.py` detection
3. Create evaluator file (e.g., `my_evaluator.py`)
4. Update `evaluate.py` routing

## 📝 License
Part of Sentiment Oracle project

## 🔗 Related Documentation
- [Main README](../README.md)
- [NLP Module](../app/nlp/README.md)
- [Configuration](config.py)
