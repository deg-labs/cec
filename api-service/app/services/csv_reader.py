import os
import logging
import pandas as pd
from typing import Optional
from fastapi import HTTPException
from app import config

logger = logging.getLogger(__name__)

def load_and_clean_data(coin_type: str, include_seed: bool) -> Optional[pd.DataFrame]:
    """Loads, cleans, and pre-processes the ETF data from a CSV file."""
    csv_file = os.path.join(config.CSV_DATA_DIR, f"etf_{coin_type}.csv")
    if not os.path.exists(csv_file):
        return None

    try:
        df = pd.read_csv(csv_file)

        if "Date" not in df.columns:
            raise ValueError(f"CSV {csv_file} is missing the required 'Date' column")

        # Handle "Seed" row
        if not include_seed:
            df = df[df['Date'] != 'Seed']

        # Convert Date column to datetime objects, coercing errors
        # This standardizes the date format for reliable filtering and sorting
        df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
        df.dropna(subset=['Date'], inplace=True) # Drop rows where date conversion failed
        df = df.sort_values(by='Date', ascending=False)

        # Fill NaN values in all columns (except Date) with 0,
        # safely coercing non-numeric values to numeric
        for col in df.columns:
            if col != 'Date':
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

        return df
    except Exception:
        logger.exception("Failed to read or clean CSV %s", csv_file)
        raise HTTPException(
            status_code=404,
            detail=f"Data for '{coin_type}' is malformed or unavailable.",
        )
