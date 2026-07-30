import pandas as pd
import io
import logging

logger = logging.getLogger(__name__)

def html_to_dataframe(html_content: str, coin_type: str) -> pd.DataFrame | None:
    """
    Parses HTML content with a specific table structure for BTC, ETH, or SOL ETFs,
    and cleans the data, returning a pandas DataFrame.
    Returns None if an error occurs or no relevant table is found.
    """
    df = None
    try:
        if coin_type == 'btc':
            tables = pd.read_html(io.StringIO(html_content), flavor='lxml', attrs={'class': 'etf'})
            if not tables:
                logger.warning("No ETF table found in the provided HTML content for BTC")
                return None
            df = tables[0].copy()

            if 'BTC' in df.columns:
                if df['BTC'].isnull().all():
                    df = df.drop(columns=['BTC'])

        elif coin_type == 'eth' or coin_type == 'sol':
            tables = pd.read_html(io.StringIO(html_content), flavor='lxml', attrs={'class': 'etf'}, header=1)
            if not tables:
                logger.warning("No ETF table found in the provided HTML content for %s", coin_type.upper())
                return None
            df = tables[0].copy()

            df.rename(columns={df.columns[0]: 'Date', df.columns[-1]: 'Total'}, inplace=True)

            if 'Date' in df.columns:
                df = df[~df['Date'].astype(str).str.contains('Fee', na=False)]
                if coin_type == 'sol':
                    df = df[~df['Date'].astype(str).str.contains('Staking', na=False)]
        else:
            logger.error("Invalid coin type %r; use btc, eth, or sol", coin_type)
            return None

        df.dropna(how='all', inplace=True)
        df.reset_index(drop=True, inplace=True)

        if 'Date' in df.columns:
            df = df[~df['Date'].astype(str).str.contains('Date', na=False)]

            valid_dates = pd.to_datetime(df['Date'], format='%d %b %Y', errors='coerce')
            last_valid_row = valid_dates.last_valid_index()
            
            if last_valid_row is not None:
                df = df.iloc[:last_valid_row + 1]

        def clean_and_convert(value):
            if isinstance(value, str):
                value = value.replace(',', '').replace('(', '-').replace(')', '')
            try:
                return pd.to_numeric(value, errors='coerce')
            except (ValueError, TypeError):
                return value

        for col in df.columns:
            if col != 'Date':
                df[col] = df[col].apply(clean_and_convert)
        
        return df

    except Exception:
        logger.exception("An error occurred during HTML to DataFrame conversion for %s", coin_type.upper())
        return None
