"""Validation summary model."""

from datetime import datetime


class ValidationSummary:
    """Represents validation summary for a region."""
    
    def __init__(self, region, total):
        """Initialize validation summary."""
        self.region = region
        self.started_at = datetime.now().isoformat()
        self.total = total
        self.successful = 0
        self.failed = 0
        self.results = []
        self.error = None
    
    def add_result(self, result):
        """Add a validation result to summary."""
        self.results.append(result)
        if result.success:
            self.successful += 1
        else:
            self.failed += 1
    
    def to_dict(self):
        """Convert summary to dictionary."""
        return {
            "region": self.region,
            "started_at": self.started_at,
            "completed_at": datetime.now().isoformat(),
            "total": self.total,
            "successful": self.successful,
            "failed": self.failed,
            "error": self.error,
            "results": [r.to_dict() if hasattr(r, 'to_dict') else r for r in self.results]
        }

