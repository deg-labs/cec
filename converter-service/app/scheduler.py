import time
import argparse
import sys
import logging
from app import logging_config
from app.data_processor import process_etfs

logger = logging.getLogger(__name__)

def run_scheduler():
    """
    Runs the ETF data processing scheduler.
    """
    parser = argparse.ArgumentParser(description='Periodically fetch ETF data and convert to CSV.')
    parser.add_argument('--interval', type=int, default=1800, help='Interval in seconds between runs (default: 1800 for 30 minutes).')
    parser.add_argument('--dry-run', action='store_true', help='Run a single check cycle to test if conversion is possible and exit.')
    args = parser.parse_args()

    if args.dry_run:
        logger.info("Performing a dry-run health check for CSV conversion")
        if process_etfs(dry_run=True):
            logger.info("Dry-run successful: all configured ETF data could be fetched and parsed")
            sys.exit(0)
        else:
            logger.error("Dry-run failed: some ETF data could not be fetched or parsed")
            sys.exit(1)
    else:
        while True:
            process_etfs()
            logger.info("Sleeping for %s seconds", args.interval)
            time.sleep(args.interval)

if __name__ == "__main__":
    run_scheduler()
