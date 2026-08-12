import pandas as pd
import math
from typing import List
from app.models.etf_data import ETFRecord
from app.utils.date_utils import format_date_to_string
from app.services.errors import MalformedDataError

def _to_float(value) -> float:
    """Convert a trusted financial value without changing invalid data to zero."""
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise MalformedDataError("Financial value is not numeric") from exc
    if pd.isna(number) or not math.isfinite(number):
        raise MalformedDataError("Financial value is not finite")
    return number

def format_response(df: pd.DataFrame) -> List[ETFRecord]:
    """Formats the DataFrame into a list of ETFRecord objects."""
    output = []
    
    non_flow_columns = {'Date', 'Total'}
    
    for _, row in df.iterrows():
        flows = {
            col: _to_float(row[col])
            for col in df.columns if col not in non_flow_columns
        }

        record = ETFRecord(
            date=format_date_to_string(row['Date']),
            total=_to_float(row['Total']),
            flows=flows,
        )
        output.append(record)
        
    return output
