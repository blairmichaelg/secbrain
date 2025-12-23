"""Performance monitoring and metrics collection."""

import time
import logging
from contextlib import contextmanager
from typing import Any, Generator

logger = logging.getLogger(__name__)


class MetricsCollector:
    """Collect and report performance metrics."""
    
    def __init__(self):
        self.timings: dict[str, list[float]] = {}
        self.counters: dict[str, int] = {}
    
    @contextmanager
    def measure(self, operation: str) -> Generator[None, None, None]:
        """Context manager to measure operation duration."""
        start = time.perf_counter()
        try:
            yield
        finally:
            duration = time.perf_counter() - start
            if operation not in self.timings:
                self.timings[operation] = []
            self.timings[operation].append(duration)
    
    def increment(self, counter: str, value: int = 1) -> None:
        """Increment a counter."""
        self.counters[counter] = self.counters.get(counter, 0) + value
    
    def report(self) -> dict[str, Any]:
        """Generate performance report."""
        report = {
            "timings": {},
            "counters": self.counters.copy(),
        }
        
        for operation, durations in self.timings.items():
            report["timings"][operation] = {
                "count": len(durations),
                "total": sum(durations),
                "avg": sum(durations) / len(durations),
                "min": min(durations),
                "max": max(durations),
            }
        
        return report


# Global metrics collector
metrics = MetricsCollector()


# Usage example:
async def example_monitored_function():
    with metrics.measure("http_request"):
        # ... do work ...
        pass
    
    metrics.increment("requests_total")
