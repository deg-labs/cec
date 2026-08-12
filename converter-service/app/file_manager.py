import os
import tempfile
import logging

import pandas as pd

logger = logging.getLogger(__name__)

REQUIRED_COLUMNS = ("Date", "Total")
MIN_ROWS = 1


def ensure_csv_directory_exists(csv_dir: str):
    """Ensures the CSV output directory exists."""
    os.makedirs(csv_dir, exist_ok=True)


def validate_dataframe(dataframe: pd.DataFrame) -> bool:
    """Validates that the DataFrame has the required columns and a minimum number of rows."""
    if dataframe is None or len(dataframe) < MIN_ROWS:
        logger.error(
            "Refusing to save: DataFrame has fewer than %s rows", MIN_ROWS
        )
        return False
    missing = [col for col in REQUIRED_COLUMNS if col not in dataframe.columns]
    if missing:
        logger.error(
            "Refusing to save: DataFrame is missing required columns %s", missing
        )
        return False
    return True


def save_dataframe_to_csv(dataframe: pd.DataFrame, output_filename: str) -> bool:
    """Validates the DataFrame and atomically writes it to a CSV file.

    Writes to a temporary file first and renames it into place with os.replace,
    so the existing CSV is never left in a partially written state. If validation
    fails, the existing CSV is kept untouched. Returns True on success.
    """
    if not validate_dataframe(dataframe):
        logger.error("Validation failed; keeping existing %s", output_filename)
        return False

    output_dir = os.path.dirname(output_filename) or "."
    fd, tmp_path = tempfile.mkstemp(dir=output_dir, suffix=".tmp")
    try:
        with os.fdopen(fd, "w") as tmp_file:
            dataframe.to_csv(tmp_file, index=False)
        os.replace(tmp_path, output_filename)
        logger.info("Final cleaned data saved to %s", output_filename)
        return True
    except Exception:
        os.unlink(tmp_path)
        logger.exception("Failed to save dataframe to %s", output_filename)
        return False
