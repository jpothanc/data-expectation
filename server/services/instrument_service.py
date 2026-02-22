"""Service for instrument data operations."""

import logging
import time

import pandas as pd
from loaders.csv_loader import CSVDataLoader
from loaders.database_loader import DatabaseDataLoader
from .constants import DEFAULT_EXCHANGE_MAP

logger = logging.getLogger(__name__)


class InstrumentService:
    """Manages instrument data retrieval and search operations."""

    def __init__(self, loader, exchange_map=None, product_type='stock'):
        self.loader = loader
        self.product_type = product_type
        self._is_csv = isinstance(loader, CSVDataLoader)
        self._is_db = isinstance(loader, DatabaseDataLoader)
        self.exchange_map = self._init_exchange_map(exchange_map, product_type)
        self.ALL_EXCHANGES = list(self.exchange_map)

    # ------------------------------------------------------------------
    # Initialisation helpers
    # ------------------------------------------------------------------

    def _init_exchange_map(self, exchange_map, product_type):
        resolved = self._extract_product_map(exchange_map, product_type)
        default = DEFAULT_EXCHANGE_MAP.get(product_type, DEFAULT_EXCHANGE_MAP['stock'])

        if self._is_csv:
            return resolved or default

        if self._is_db:
            if resolved:
                return resolved
            return {code: code for code in default}

        return resolved or default

    @staticmethod
    def _extract_product_map(exchange_map, product_type):
        if not exchange_map:
            return None
        if isinstance(exchange_map, dict) and product_type in exchange_map:
            return exchange_map[product_type]
        # Flat map (all values are strings)
        if isinstance(exchange_map, dict) and all(isinstance(v, str) for v in exchange_map.values()):
            return exchange_map
        return exchange_map

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def get_all_exchanges(self):
        """Return metadata for every configured exchange."""
        exchanges = [
            {"exchange": code, "data_source": src, "available": True}
            for code, src in self.exchange_map.items()
        ]
        return {
            "exchanges": sorted(exchanges, key=lambda x: x["exchange"]),
            "count": len(exchanges),
        }

    def get_by_exchange(self, exchange, limit=None, offset=0):
        """Return all instruments for *exchange*, with optional pagination."""
        t0 = time.perf_counter()
        df = self.load_exchange_data(exchange, limit=limit, offset=offset)
        logger.info("[TIMING] get_by_exchange %s: %.1f ms (%d rows)", exchange,
                    (time.perf_counter() - t0) * 1000, len(df))
        return {
            "exchange": exchange,
            "count": len(df),
            "instruments": _df_to_records(df),
        }

    def find_by_ric(self, ric, exchange=None):
        """Find instruments matching *ric* in one exchange or all."""
        match = lambda df: df[df["RIC"] == ric]
        if exchange:
            return self._find_in_exchange(exchange, match, multiple=True)
        return self._search_all(match, multiple=True)

    def find_by_id(self, instrument_id, exchange=None):
        return self.find_by_masterid(instrument_id, exchange)

    def find_by_masterid(self, master_id, exchange=None):
        """Find an instrument by its MasterId."""
        id_str = str(master_id)
        match = lambda df: df[df["MasterId"].astype(str) == id_str]
        if exchange:
            return self._find_in_exchange(exchange, match, multiple=False)
        return self._search_all(match, multiple=False)

    def filter_by_column_values(self, exchange, column, values=None, include_missing=False):
        """
        Return only the instruments from *exchange* where *column* matches one of
        *values*, or where *column* is null/empty when *include_missing* is True.

        This avoids serialising and transmitting the full exchange dataset when the
        caller only needs a small subset (e.g. the 2 instruments that failed a check).
        """
        t0 = time.perf_counter()
        df = self.load_exchange_data(exchange)
        logger.debug("[TIMING] load_exchange_data for filter on %s: %.1f ms", exchange,
                     (time.perf_counter() - t0) * 1000)

        if df is None or df.empty:
            return {"exchange": exchange, "column": column, "count": 0, "instruments": []}

        if column not in df.columns:
            return {"exchange": exchange, "column": column, "count": 0, "instruments": []}

        mask = pd.Series(False, index=df.index)

        if values:
            str_values = [str(v) for v in values]
            mask |= df[column].astype(str).isin(str_values)

        if include_missing:
            null_mask = df[column].isna() | (df[column].astype(str).str.strip() == '')
            mask |= null_mask

        matched = df[mask]
        return {
            "exchange": exchange,
            "column": column,
            "count": len(matched),
            "instruments": _df_to_records(matched),
        }

    # ------------------------------------------------------------------
    # Data loading
    # ------------------------------------------------------------------

    def load_exchange_data(self, exchange, limit=None, offset=0):
        """Load raw DataFrame for *exchange*, applying pagination where appropriate."""
        self._validate_exchange(exchange)

        if self._is_csv:
            df = self.loader.load(self.exchange_map[exchange])
            if offset:
                df = df.iloc[offset:]
            if limit:
                df = df.iloc[:limit]
            return df

        if self._is_db:
            return self.loader.load(
                exchange, product_type=self.product_type, limit=limit, offset=offset
            )

        # Fallback for other loader types
        df = self.loader.load(self.exchange_map[exchange])
        if offset:
            df = df.iloc[offset:]
        if limit:
            df = df.iloc[:limit]
        return df

    # ------------------------------------------------------------------
    # Search helpers
    # ------------------------------------------------------------------

    def _find_in_exchange(self, exchange, match_fn, multiple=False):
        df = self.load_exchange_data(exchange)
        hits = match_fn(df)
        if hits.empty:
            return [] if multiple else None
        records = _df_to_records(hits)
        return records if multiple else records[0]

    def _search_all(self, match_fn, multiple=False):
        if not self.ALL_EXCHANGES:
            raise ValueError(
                "Cannot search all exchanges: exchange parameter is required for database loaders"
            )
        results = []
        for exchange in self.ALL_EXCHANGES:
            try:
                df = self.load_exchange_data(exchange)
                hits = match_fn(df)
                if not hits.empty:
                    records = _df_to_records(hits)
                    if multiple:
                        results.extend(records)
                    else:
                        return records[0]
            except Exception:
                continue
        return results if multiple else None

    def _validate_exchange(self, exchange):
        if exchange not in self.exchange_map:
            raise ValueError(
                f"Exchange '{exchange}' not found. Available: {', '.join(self.ALL_EXCHANGES)}"
            )


# ------------------------------------------------------------------
# Module-level utility
# ------------------------------------------------------------------

def _df_to_records(df):
    """Convert a DataFrame to a list of dicts with NaN replaced by None.

    Uses pandas vectorised operations instead of a recursive Python loop,
    which is orders of magnitude faster for wide/tall DataFrames.

    astype(object) widens every column to object dtype so that pandas can
    store Python None (not numpy nan) when where() substitutes missing values.
    """
    cleaned = df.astype(object).where(pd.notnull(df), other=None)
    return cleaned.to_dict(orient='records')
