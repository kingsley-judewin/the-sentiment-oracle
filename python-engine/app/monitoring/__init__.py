"""
__init__.py — Monitoring Package
==================================
Exposes monitoring and health check functionality.
"""

from app.monitoring.ingestion_metrics import (
    record_fetch,
    record_dedup,
    record_cycle,
    get_metrics,
)
from app.monitoring.health import get_health_status

__all__ = [
    "record_fetch",
    "record_dedup",
    "record_cycle",
    "get_metrics",
    "get_health_status",
]
