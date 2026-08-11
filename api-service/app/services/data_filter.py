import pandas as pd
from typing import List
from fastapi import HTTPException
from app.models.etf_data import ETFRecord
from app.utils.date_utils import format_date_to_string

def _to_float(value) -> float:
    """Safely converts a value to float, treating NaN/None as 0.0."""
    try:
        number = float(value)
    except (TypeError, ValueError):
        return 0.0
    if pd.isna(number):
        return 0.0
    return number

def format_response(df: pd.DataFrame) -> List[ETFRecord]:
    """Formats the DataFrame into a list of ETFRecord objects."""
    output = []
    
    non_flow_columns = {'Date', 'Total'}
    
    try:
        for _, row in df.iterrows():
            flows = {
                col: _to_float(row[col])
                for col in df.columns if col not in non_flow_columns
            }
            
            record = ETFRecord(
                date=format_date_to_string(row['Date']),
                total=_to_float(row.get('Total', 0)),
                flows=flows,
            )
            output.append(record)
    except (KeyError, TypeError, ValueError):
        raise HTTPException(
            status_code=404,
            detail="Data is malformed or unavailable.",
        )
        
    return output
