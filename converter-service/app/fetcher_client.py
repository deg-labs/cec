import requests
import logging
from app import config

logger = logging.getLogger(__name__)

def fetch_html_from_deno_api(target_url: str) -> str:
    """Fetches HTML content using the Deno API server."""
    api_url = f"{config.DENO_API_BASE_URL}/fetch?url={target_url}"
    logger.info("Calling Deno API: %s", api_url)
    try:
        response = requests.get(api_url, timeout=30)
        response.raise_for_status()  # Raise an exception for HTTP errors
        return response.text
    except requests.exceptions.RequestException:
        logger.exception("Error fetching from Deno API for %s", target_url)
        return ""
