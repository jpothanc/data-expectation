"""Validation summary model."""

import threading
from datetime import datetime


class ValidationSummary:
    """Aggregates validation results for a region.

    Thread-safe: add_result may be called concurrently from worker threads.
    """

    def __init__(self, region, total):
        self.region = region
        self.started_at = datetime.now().isoformat()
        self.total = total
        self.successful = 0
        self.failed = 0
        self.results = []
        self.error = None
        self._lock = threading.Lock()

    def add_result(self, result):
        """Append *result* and update counters.  Safe to call from multiple threads."""
        with self._lock:
            self.results.append(result)
            if result.success:
                self.successful += 1
            else:
                self.failed += 1

    def to_dict(self):
        return {
            "region": self.region,
            "started_at": self.started_at,
            "completed_at": datetime.now().isoformat(),
            "total": self.total,
            "successful": self.successful,
            "failed": self.failed,
            "error": self.error,
            "results": [r.to_dict() if hasattr(r, 'to_dict') else r for r in self.results],
        }
