"""
main.py — Orchestrator + API Exposure
========================================
Coordinates the entire Sentiment Oracle pipeline and exposes it via FastAPI.

Pipeline:
  Ingestion → Aggregation → Cleaning → Sentiment → Scoring → Smoothing → API
"""

from datetime import datetime, timezone
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.ingestion.source_router import get_posts
from app.ingestion.aggregator import aggregate
from app.nlp.cleaner import clean_posts
from app.nlp.sentiment import analyze_posts
from app.nlp.model import get_model
from app.scoring.vibe_score import compute
from app.scoring.smoothing import smooth
from app.utils.logger import (
    log_pipeline_start,
    log_aggregation,
    log_cleaning,
    log_sentiment_distribution,
    log_scores,
    logger,
)
from app.monitoring import get_metrics, get_health_status


# ── Response cache: keeps last successful result ─────────────
_last_sentiment_response: dict | None = None
_last_oracle_response: dict | None = None


# ── Lifespan: pre-load model at startup ─────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Loading NLP model (one-time startup)...")
    get_model()
    logger.info("Model loaded ✓ — Oracle is ready.")
    yield


app = FastAPI(
    title="Sentiment Oracle",
    description="NLP-powered community sentiment oracle for on-chain integration",
    version="1.0.0",
    lifespan=lifespan,
)

import os

# ── CORS Configuration ───────────────────────────────────────
_frontend_url = os.getenv("FRONTEND_URL", "http://localhost:5173")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[_frontend_url, "http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/oracle")
def run_pipeline():
    """
    Execute the full sentiment oracle pipeline and return structured results.

    Caches last successful result so the oracle bridge always has data.

    Returns JSON:
    {
        raw_score, smoothed_score, post_count,
        positive_count, negative_count, last_updated_timestamp
    }
    """
    global _last_oracle_response

    # ── 1. Ingestion ─────────────────────────────────────────
    raw_posts = get_posts()
    log_pipeline_start(len(raw_posts))

    # ── 2. Aggregation ───────────────────────────────────────
    aggregated = aggregate(raw_posts)
    log_aggregation(before=len(raw_posts), after=len(aggregated))

    # ── 3. Cleaning ──────────────────────────────────────────
    cleaned = clean_posts(aggregated)
    log_cleaning(before=len(aggregated), after=len(cleaned))

    # ── 4. Sentiment Inference ───────────────────────────────
    analyzed = analyze_posts(cleaned)

    # ── 5. Scoring ───────────────────────────────────────────
    score_result = compute(analyzed)
    log_sentiment_distribution(
        positive=score_result["positive_count"],
        negative=score_result["negative_count"],
    )

    # ── 6. Smoothing ─────────────────────────────────────────
    smoothed_score = smooth(score_result["raw_score"])
    log_scores(raw=score_result["raw_score"], smoothed=smoothed_score)

    # ── 7. Build response ────────────────────────────────────
    response = {
        "raw_score": score_result["raw_score"],
        "smoothed_score": smoothed_score,
        "post_count": score_result["post_count"],
        "positive_count": score_result["positive_count"],
        "negative_count": score_result["negative_count"],
        "last_updated_timestamp": datetime.now(timezone.utc).isoformat(),
    }

    # ── 8. Cache or fallback ─────────────────────────────────
    if score_result["post_count"] > 0:
        _last_oracle_response = response
        return response
    elif _last_oracle_response is not None:
        logger.info("No new posts from pipeline — returning cached oracle response")
        return _last_oracle_response
    else:
        return response


@app.get("/sentiment")
def get_sentiment():
    """
    Dashboard-friendly endpoint with detailed post information.
    
    Caches the last successful result so the dashboard always has data
    to display, even when the deduplicator filters all posts during
    cooldown windows.
    
    Returns JSON matching dashboard spec:
    {
        community_vibe_score, raw_score, sample_size,
        posts: [{ text, engagement, sentiment: { raw_label, confidence, polarity_score } }]
    }
    """
    global _last_sentiment_response
    
    # ── 1. Ingestion ─────────────────────────────────────────
    raw_posts = get_posts()
    
    # ── 2. Aggregation ───────────────────────────────────────
    aggregated = aggregate(raw_posts)
    
    # ── 3. Cleaning ──────────────────────────────────────────
    cleaned = clean_posts(aggregated)
    
    # ── 4. Sentiment Inference ───────────────────────────────
    analyzed = analyze_posts(cleaned)
    
    # ── 5. Scoring ───────────────────────────────────────────
    score_result = compute(analyzed)
    smoothed_score = smooth(score_result["raw_score"])
    
    # ── 6. Format posts for dashboard ───────────────────────
    formatted_posts = []
    for post in analyzed[:20]:  # Limit to 20 most recent posts
        formatted_posts.append({
            "id": post.get("id", ""),
            "text": post.get("text", ""),
            "engagement": post.get("engagement", 0),
            "sentiment": {
                "raw_label": post.get("label", "UNKNOWN"),
                "confidence": post.get("confidence", 0.0),
                "polarity_score": post.get("polarity_score", 0)
            }
        })
    
    # ── 7. Build response ────────────────────────────────────
    response = {
        "community_vibe_score": smoothed_score,
        "raw_score": score_result["raw_score"],
        "sample_size": score_result["post_count"],
        "posts": formatted_posts
    }
    
    # ── 8. Cache or fallback ─────────────────────────────────
    # If pipeline produced posts, cache this as the latest good response.
    # If no posts (deduplicator filtered all), return the cached version
    # so the dashboard always has data to display.
    if formatted_posts:
        _last_sentiment_response = response
        return response
    elif _last_sentiment_response is not None:
        logger.info("No new posts from pipeline — returning cached response")
        return _last_sentiment_response
    else:
        return response


@app.get("/health")
def health():
    """
    Comprehensive system health check.
    
    Returns:
        - status: "healthy" | "degraded" | "unhealthy"
        - components: NLP model, smoothing, ingestion status
        - last_score: most recent sentiment score
        - last_update_timestamp: when last updated
    """
    return get_health_status()


@app.get("/ingestion-metrics")
def ingestion_metrics():
    """
    Get detailed ingestion performance metrics.
    
    Returns:
        - total_cycles: number of pipeline cycles
        - total_dedup_collapsed: duplicates removed
        - sources: per-source metrics (fetch count, success rate, latency, etc.)
    """
    return get_metrics()


# ── Validation Mode (CLI) ─────────────────────────────────────

def run_validation():
    """
    Run the full pipeline once and print summary metrics.
    No FastAPI — used for demos and system verification.

    Usage:
        python app/main.py --validation-mode
    """
    import time
    import json

    print("=" * 50)
    print("  SENTIMENT ORACLE — Validation Mode")
    print("=" * 50)

    # Load model
    print("\n[1/6] Loading NLP model...")
    start = time.perf_counter()
    get_model()
    model_time = time.perf_counter() - start
    print(f"       Model loaded in {model_time:.2f}s")

    # Ingestion
    print("\n[2/6] Ingesting posts...")
    raw_posts = get_posts()
    print(f"       Ingested: {len(raw_posts)} posts")

    # Aggregation
    print("\n[3/6] Aggregating...")
    aggregated = aggregate(raw_posts)
    print(f"       After aggregation: {len(aggregated)} (dropped {len(raw_posts) - len(aggregated)})")

    # Cleaning
    print("\n[4/6] Cleaning...")
    cleaned = clean_posts(aggregated)
    print(f"       After cleaning: {len(cleaned)} (filtered {len(aggregated) - len(cleaned)})")

    # Sentiment
    print("\n[5/6] Running sentiment inference...")
    inference_start = time.perf_counter()
    analyzed = analyze_posts(cleaned)
    inference_time = time.perf_counter() - inference_start
    print(f"       Inference completed in {inference_time:.2f}s")

    # Scoring + Smoothing
    print("\n[6/6] Computing scores...")
    score_result = compute(analyzed)
    smoothed_score = smooth(score_result["raw_score"])

    total_time = time.perf_counter() - start

    # Summary
    summary = {
        "raw_score": score_result["raw_score"],
        "smoothed_score": smoothed_score,
        "post_count": score_result["post_count"],
        "positive_count": score_result["positive_count"],
        "negative_count": score_result["negative_count"],
        "model_load_time_s": round(model_time, 2),
        "inference_time_s": round(inference_time, 2),
        "total_time_s": round(total_time, 2),
        "last_updated_timestamp": datetime.now(timezone.utc).isoformat(),
    }

    print("\n" + "=" * 50)
    print("  VALIDATION RESULTS")
    print("=" * 50)
    print(json.dumps(summary, indent=2))
    print("=" * 50)

    # Invariant checks
    checks_passed = 0
    checks_total = 5

    def check(name: str, condition: bool):
        nonlocal checks_passed
        status = "PASS" if condition else "FAIL"
        checks_passed += condition
        print(f"  [{status}] {name}")

    print("\n  INVARIANT CHECKS:")
    check("Score in [-100, +100]", -100 <= summary["raw_score"] <= 100)
    check("Smoothed in [-100, +100]", -100 <= summary["smoothed_score"] <= 100)
    check("Post count > 0", summary["post_count"] > 0)
    check("Counts sum matches total", summary["positive_count"] + summary["negative_count"] == summary["post_count"])
    check("Pipeline < 60s", summary["total_time_s"] < 60)

    print(f"\n  Result: {checks_passed}/{checks_total} checks passed")
    print("=" * 50)

    return summary


if __name__ == "__main__":
    import sys

    if "--validation-mode" in sys.argv:
        run_validation()
    else:
        import uvicorn
        uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
