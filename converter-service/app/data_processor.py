import os
import logging
import sys
from app import config
from app import fetcher_client
from app.html_converter import html_to_dataframe
from app import file_manager

logger = logging.getLogger(__name__)

def process_etfs(dry_run: bool = False) -> bool:
    """
    Fetches HTML and converts it to CSV for each coin type.
    Returns True if all conversions were successful, False otherwise.
    If dry_run is True, no CSV files are actually written.
    """
    logger.info("Starting ETF CSV generation cycle dry_run=%s", dry_run)
    file_manager.ensure_csv_directory_exists(config.CSV_DIR)
    all_successful = True

    urls_to_process = config.URLS if not dry_run else {k: v for k, v in config.URLS.items() if v}

    if dry_run and not urls_to_process:
        logger.error("No URLs configured for dry-run")
        return False

    for coin_type, url in urls_to_process.items():
        if not url:
            logger.warning("Skipping %s because its URL is not configured", coin_type.upper())
            all_successful = False
            continue
        logger.info("Processing %s", coin_type.upper())
        html_content = fetcher_client.fetch_html_from_deno_api(url)
        if html_content:
            output_filename = os.path.join(config.CSV_DIR, f"etf_{coin_type}.csv")
            try:
                df = html_to_dataframe(html_content, coin_type)
                if df is not None:
                    if not dry_run:
                        if not file_manager.save_dataframe_to_csv(df, output_filename):
                            all_successful = False
                else:
                    all_successful = False
            except Exception:
                logger.exception("Error converting %s HTML to CSV", coin_type.upper())
                all_successful = False
        else:
            logger.warning("Skipping %s due to failed HTML fetch", coin_type.upper())
            all_successful = False
    logger.info("ETF CSV generation cycle completed")
    return all_successful
