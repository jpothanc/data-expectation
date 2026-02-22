"""CSV file data loader with a thread-safe in-memory DataFrame cache.

DataFrames are held in memory for `cache_ttl` seconds.  Concurrent requests
for the same file share a single cached copy — no repeated disk I/O or
CSV parsing within the TTL window.
"""

import time
import threading
import logging

import pandas as pd
from pathlib import Path

from .base import DataLoader

logger = logging.getLogger(__name__)

_DEFAULT_TTL = 300   # seconds before a cached DataFrame is considered stale


class CSVDataLoader(DataLoader):
    """Load CSV files from disk, returning cached DataFrames on subsequent calls."""

    def __init__(self, data_folder="data", cache_ttl=_DEFAULT_TTL):
        self.data_folder = Path(data_folder)
        self.cache_ttl = cache_ttl
        # { resolved_path_str: (DataFrame, loaded_at_monotonic) }
        self._cache = {}
        self._lock = threading.Lock()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def load(self, filename):
        """Return a DataFrame for *filename*, reading from cache when warm.

        Raises:
            FileNotFoundError: file does not exist on disk.
            pd.errors.EmptyDataError: file exists but contains no data.
            pd.errors.ParserError: file cannot be parsed as CSV.
        """
        file_path = self._resolve(filename)
        cache_key = str(file_path)
        now = time.monotonic()

        # Fast path — cheap dict lookup under lock
        with self._lock:
            entry = self._cache.get(cache_key)
            if entry is not None:
                df, loaded_at = entry
                if now - loaded_at < self.cache_ttl:
                    logger.debug("CSV cache HIT: %s", cache_key)
                    return df.copy()

        # Slow path — read from disk, then update cache
        logger.debug("CSV cache MISS: %s", cache_key)
        df = self._read(file_path)

        with self._lock:
            self._cache[cache_key] = (df, time.monotonic())

        return df.copy()

    def warm_up(self, filenames):
        """Pre-load a list of filenames into the cache.

        Safe to call from a background thread.  Errors for individual files
        are logged as warnings rather than raised so that one bad file does
        not abort the whole warm-up.
        """
        for filename in filenames:
            try:
                self.load(filename)
                logger.info("CSV warm-up loaded: %s", filename)
            except Exception as exc:
                logger.warning("CSV warm-up skipped %s: %s", filename, exc)

    def invalidate(self, filename=None):
        """Evict one entry from the cache, or the whole cache if *filename* is None."""
        with self._lock:
            if filename is None:
                self._cache.clear()
                logger.info("CSV cache fully cleared")
            else:
                key = str(self._resolve(filename))
                self._cache.pop(key, None)
                logger.debug("CSV cache evicted: %s", key)

    def cache_stats(self):
        """Return a snapshot of current cache state (useful for health checks)."""
        with self._lock:
            now = time.monotonic()
            entries = []
            for path, (_, loaded_at) in self._cache.items():
                age = now - loaded_at
                entries.append({
                    "path": path,
                    "age_seconds": round(age, 1),
                    "stale": age >= self.cache_ttl,
                })
            return {"entry_count": len(entries), "ttl_seconds": self.cache_ttl, "entries": entries}

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _resolve(self, filename):
        """Return an absolute Path for *filename*."""
        p = Path(filename)
        return p if p.is_absolute() else (self.data_folder / filename).resolve()

    def _read(self, file_path):
        """Read a CSV from *file_path* and return a non-empty DataFrame."""
        if not file_path.exists():
            raise FileNotFoundError(f"CSV file not found: {file_path}")
        try:
            df = pd.read_csv(file_path)
        except pd.errors.EmptyDataError:
            raise pd.errors.EmptyDataError(f"CSV file is empty: {file_path}")
        except pd.errors.ParserError as exc:
            raise pd.errors.ParserError(f"Error parsing CSV file {file_path}: {exc}")
        except Exception as exc:
            raise Exception(f"Unexpected error loading CSV file {file_path}: {exc}")

        if df.empty:
            raise pd.errors.EmptyDataError(f"CSV file is empty: {file_path}")

        return df
