import os
import logging
import math
import pandas as pd
from typing import Optional
from app import config
from app.services.errors import MalformedDataError

logger = logging.getLogger(__name__)

def load_and_clean_data(coin_type: str, include_seed: bool) -> Optional[pd.DataFrame]:
    """Loads, cleans, and pre-processes the ETF data from a CSV file."""
    csv_file = os.path.join(config.CSV_DATA_DIR, f"etf_{coin_type}.csv")
    if not os.path.exists(csv_file):
        return None

    try:
        df = pd.read_csv(csv_file)
    except (pd.errors.EmptyDataError, pd.errors.ParserError, UnicodeDecodeError) as exc:
        logger.warning("Malformed CSV %s: %s", csv_file, exc)
        raise MalformedDataError(f"CSV {csv_file} is malformed") from exc

    if "Date" not in df.columns or "Total" not in df.columns:
        raise MalformedDataError(
            f"CSV {csv_file} is missing the required Date or Total column"
        )

    # Handle "Seed" row
    if not include_seed:
        df = df[df['Date'] != 'Seed']

    # Convert Date column to datetime objects, coercing errors. Invalid date
    # rows are excluded, but financial cells are never silently rewritten.
    df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
    df.dropna(subset=['Date'], inplace=True)
    df = df.sort_values(by='Date', ascending=False)

    for col in df.columns:
        if col == 'Date':
            continue
        raw = df[col]
        numeric = pd.to_numeric(raw, errors='coerce')
        invalid = raw.isna() | numeric.isna() | ~numeric.map(math.isfinite)
        if invalid.any():
            row_number = int(invalid[invalid].index[0]) + 2
            raise MalformedDataError(
                f"CSV {csv_file} has an invalid financial value in {col} at row {row_number}"
            )
        df[col] = numeric

    return df
