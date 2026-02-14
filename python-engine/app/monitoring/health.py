"""
health.py — System Health Check Module
========================================
Provides comprehensive health status for the Sentiment Oracle system.
Checks NLP model, smoothing state, ingestion, and recent activity.
"""

from datetime import datetime, timezone
from typing import Dict

from app.nlp.model import get_model
from app.scoring.smoothing import get_last_score, has_history
from app.monitoring.ingestion_metrics import get_metrics


def get_health_status() -> Dict:
    """
    Get comprehensive system health status.
    
    Returns:
        Dict with health indicators:
          - status: "healthy" | "degraded" | "unhealthy"
          - components: individual component statuses
          - last_score: most recent sentiment score
          - last_update_timestamp: when last updated
    """
    health = {
        "status": "healthy",
        "components": {},
        "last_score": None,
        "last_update_timestamp": None,
    }
    
    # Check NLP model
    try:
        model = get_model()
        health["components"]["nlp_model"] = {
            "status": "ok",
            "loaded": model is not None,
        }
    except Exception as e:
        health["components"]["nlp_model"] = {
            "status": "error",
            "loaded": False,
            "error": str(e),
        }
        health["status"] = "degraded"
    
    # Check smoothing state
    try:
        has_data = has_history()
        last_score = get_last_score()
        health["components"]["smoothing"] = {
            "status": "ok",
            "has_history": has_data,
            "last_score": last_score,
        }
        health["last_score"] = last_score
    except Exception as e:
        health["components"]["smoothing"] = {
            "status": "error",
            "error": str(e),
        }
        health["status"] = "degraded"
    
    # Check ingestion metrics
    try:
        metrics = get_metrics()
        total_cycles = metrics.get("total_cycles", 0)
        
        # Determine ingestion health based on success rates
        ingestion_status = "ok"
        for source_name, source_metrics in metrics.get("sources", {}).items():
            success_rate = source_metrics.get("success_rate_percent", 0)
            if success_rate < 50 and source_metrics.get("fetch_count", 0) > 0:
                ingestion_status = "degraded"
        
        health["components"]["ingestion"] = {
            "status": ingestion_status,
            "total_cycles": total_cycles,
            "sources": metrics.get("sources", {}),
        }
        
        if ingestion_status != "ok":
            health["status"] = "degraded"
    
    except Exception as e:
        health["components"]["ingestion"] = {
            "status": "error",
            "error": str(e),
        }
        health["status"] = "degraded"
    
    # Set last update timestamp
    health["last_update_timestamp"] = datetime.now(timezone.utc).isoformat()
    
    return health
