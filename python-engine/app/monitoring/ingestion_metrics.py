"""
ingestion_metrics.py — Ingestion Health Monitoring
====================================================
Tracks ingestion performance metrics across all sources.
Provides in-memory metrics storage with thread-safe updates.

Metrics Tracked:
  - RSS success rate and latency
  - Twitter dataset fetch latency
  - Posts per cycle (by source)
  - Duplicate collapse count
  - Error counts
"""

import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from threading import Lock
from typing import Dict


@dataclass
class SourceMetrics:
    """Metrics for a single ingestion source."""
    
    fetch_count: int = 0
    success_count: int = 0
    failure_count: int = 0
    total_posts: int = 0
    total_latency_ms: float = 0.0
    last_fetch_time: str | None = None
    last_error: str | None = None
    
    @property
    def success_rate(self) -> float:
        """Success rate as percentage (0-100)."""
        if self.fetch_count == 0:
            return 0.0
        return (self.success_count / self.fetch_count) * 100
    
    @property
    def avg_latency_ms(self) -> float:
        """Average fetch latency in milliseconds."""
        if self.success_count == 0:
            return 0.0
        return self.total_latency_ms / self.success_count
    
    @property
    def avg_posts_per_fetch(self) -> float:
        """Average posts returned per successful fetch."""
        if self.success_count == 0:
            return 0.0
        return self.total_posts / self.success_count


class IngestionMetricsTracker:
    """
    Thread-safe ingestion metrics tracker.
    
    Tracks metrics per source (reddit, twitter, mock) and provides
    aggregated statistics for monitoring endpoints.
    """
    
    def __init__(self):
        self._sources: Dict[str, SourceMetrics] = {}
        self._dedup_count: int = 0
        self._total_cycles: int = 0
        self._lock = Lock()
    
    def record_fetch(
        self,
        source: str,
        success: bool,
        post_count: int,
        latency_ms: float,
        error: str | None = None,
    ) -> None:
        """
        Record a fetch attempt for a source.
        
        Args:
            source: Source name (e.g., "reddit", "twitter")
            success: Whether fetch succeeded
            post_count: Number of posts returned (0 if failed)
            latency_ms: Fetch duration in milliseconds
            error: Error message if failed
        """
        with self._lock:
            if source not in self._sources:
                self._sources[source] = SourceMetrics()
            
            metrics = self._sources[source]
            metrics.fetch_count += 1
            
            if success:
                metrics.success_count += 1
                metrics.total_posts += post_count
                metrics.total_latency_ms += latency_ms
            else:
                metrics.failure_count += 1
                metrics.last_error = error
            
            metrics.last_fetch_time = datetime.now(timezone.utc).isoformat()
    
    def record_dedup(self, collapsed_count: int) -> None:
        """Record deduplication statistics."""
        with self._lock:
            self._dedup_count += collapsed_count
    
    def record_cycle(self) -> None:
        """Increment total pipeline cycles."""
        with self._lock:
            self._total_cycles += 1
    
    def get_metrics(self) -> Dict:
        """
        Get current metrics snapshot.
        
        Returns dict suitable for JSON serialization.
        """
        with self._lock:
            return {
                "total_cycles": self._total_cycles,
                "total_dedup_collapsed": self._dedup_count,
                "sources": {
                    name: {
                        "fetch_count": m.fetch_count,
                        "success_count": m.success_count,
                        "failure_count": m.failure_count,
                        "success_rate_percent": round(m.success_rate, 2),
                        "total_posts": m.total_posts,
                        "avg_posts_per_fetch": round(m.avg_posts_per_fetch, 2),
                        "avg_latency_ms": round(m.avg_latency_ms, 2),
                        "last_fetch_time": m.last_fetch_time,
                        "last_error": m.last_error,
                    }
                    for name, m in self._sources.items()
                },
            }
    
    def reset(self) -> None:
        """Reset all metrics (useful for testing)."""
        with self._lock:
            self._sources.clear()
            self._dedup_count = 0
            self._total_cycles = 0


# ── Global singleton ────────────────────────────────────────
_metrics_tracker = IngestionMetricsTracker()


def record_fetch(
    source: str,
    success: bool,
    post_count: int,
    latency_ms: float,
    error: str | None = None,
) -> None:
    """Record a fetch attempt (global tracker)."""
    _metrics_tracker.record_fetch(source, success, post_count, latency_ms, error)


def record_dedup(collapsed_count: int) -> None:
    """Record deduplication statistics (global tracker)."""
    _metrics_tracker.record_dedup(collapsed_count)


def record_cycle() -> None:
    """Record pipeline cycle (global tracker)."""
    _metrics_tracker.record_cycle()


def get_metrics() -> Dict:
    """Get current metrics snapshot (global tracker)."""
    return _metrics_tracker.get_metrics()


def get_tracker() -> IngestionMetricsTracker:
    """Return global tracker for testing."""
    return _metrics_tracker
