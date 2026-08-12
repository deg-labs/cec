from fastapi import APIRouter, HTTPException, Query, Response
import pandas as pd
from typing import Optional, List

from app.services.csv_reader import load_and_clean_data
from app.services.data_filter import format_response
from app.utils.date_utils import parse_date_param
from app.models.etf_data import ETFRecord
from app.models.response import ETFDataResponse

router = APIRouter()

@router.get(
    "/{coin_type}",
    response_model=List[ETFRecord], # Updated response model
    summary="Get ETF data with filtering and pagination",
    tags=["ETF Data"],
)
async def get_etf_data(
    coin_type: str,
    limit: Optional[int] = Query(30, ge=1, le=100, description="Number of recent records to return (1-100)."),
    offset: Optional[int] = Query(0, ge=0, description="Offset for pagination."),
    from_date: Optional[str] = Query(None, alias="from", description="Start date (YYYY-MM-DD)."),
    to_date: Optional[str] = Query(None, alias="to", description="End date (YYYY-MM-DD)."),
) -> List[ETFRecord]:
    """
    Retrieves ETF flow data for a specific coin with advanced filtering options.
    - **Pagination**: Use `limit` and `offset` to page through results.
    - **Date Filtering**: Use `from` and `to` to select a specific date range.
    """
    allowed_coins = ["btc", "eth", "sol"]
    if coin_type not in allowed_coins:
        raise HTTPException(status_code=400, detail=f"Invalid coin type. Please use one of {allowed_coins}.")

    df = load_and_clean_data(coin_type, include_seed=False)
    if df is None:
        raise HTTPException(status_code=404, detail=f"Data for '{coin_type}' not found.")

    # Apply date range filtering
    if from_date:
        from_dt = parse_date_param(from_date, "from")
        df = df[df['Date'] >= from_dt]
    if to_date:
        to_dt = parse_date_param(to_date, "to")
        df = df[df['Date'] <= to_dt]
            
    # Apply pagination
    df = df.iloc[offset : offset + limit]

    # Format and return
    json_output = format_response(df)
    return json_output


@router.get(
    "/{coin_type}/latest",
    response_model=ETFRecord, # Updated response model
    summary="Get the latest ETF data",
    tags=["ETF Data"],
)
async def get_latest_etf_data(coin_type: str) -> ETFRecord: # Updated return type hint
    """
    Retrieves the most recent day's ETF flow data.
    """
    allowed_coins = ["btc", "eth", "sol"]
    if coin_type not in allowed_coins:
        raise HTTPException(status_code=400, detail=f"Invalid coin type. Please use one of {allowed_coins}.")

    df = load_and_clean_data(coin_type, include_seed=False)
    if df is None or df.empty:
        raise HTTPException(status_code=404, detail=f"No data available for '{coin_type}'.")

    # The dataframe is already sorted by date, descending
    latest_df = df.head(1)
    
    # Format and return
    json_output = format_response(latest_df)
    # The result is a list with one item, so we return the item directly
    return json_output[0]

# Add a root endpoint for general information
@router.get("/", include_in_schema=False)
async def root():
    return {"message": "Welcome to the ETF Data API."}
