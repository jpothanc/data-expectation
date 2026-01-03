"""Shared constants for services."""

# Default exchange to source mapping (for CSV files) by product type
DEFAULT_EXCHANGE_MAP = {
    "stock": {
        "XHKG": "stocks/db_hkg.csv",
        "XNSE": "stocks/db_nse.csv",
        "XTKS": "stocks/db_tks.csv",
        "XLON": "stocks/db_lon.csv",
        "XPAR": "stocks/db_par.csv",
        "XNYS": "stocks/db_nys.csv",
        "XNAS": "stocks/db_nas.csv"
    },
    "option": {
        "XHKG": "options/db_hkg.csv",
        "XTKS": "options/db_tks.csv",
        "XLON": "options/db_lon.csv",
        "XPAR": "options/db_par.csv",
        "XNYS": "options/db_nys.csv",
        "XNAS": "options/db_nas.csv"
    },
    "future": {
        "XHKG": "futures/db_hkg.csv",
        "XTKS": "futures/db_tks.csv",
        "XLON": "futures/db_lon.csv",
        "XPAR": "futures/db_par.csv",
        "XNYS": "futures/db_nys.csv",
        "XNAS": "futures/db_nas.csv"
    }
}

