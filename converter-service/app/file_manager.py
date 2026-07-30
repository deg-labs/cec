import os
import logging

logger = logging.getLogger(__name__)

def ensure_csv_directory_exists(csv_dir: str):
    """Ensures the CSV output directory exists."""
    os.makedirs(csv_dir, exist_ok=True)

def save_dataframe_to_csv(dataframe, output_filename: str):
    """Saves a pandas DataFrame to a CSV file."""
    dataframe.to_csv(output_filename, index=False)
    logger.info("Final cleaned data saved to %s", output_filename)
