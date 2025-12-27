"""Yahoo Finance data fetching and caching utilities."""

import logging
from pathlib import Path
from typing import Optional

import yfinance as yf


logger = logging.getLogger(__name__)


def fetch_and_save_data(
    ticker: str,
    start: str,
    end: str,
    datas_folder: str = "datas",
    force_download: bool = False
) -> str:
    """
    Fetch stock data from Yahoo Finance and save to CSV in Backtrader format.
    
    Args:
        ticker: Stock ticker symbol
        start: Start date in 'YYYY-MM-DD' format
        end: End date in 'YYYY-MM-DD' format
        datas_folder: Path to the folder to save the CSV file
        force_download: If True, re-download even if file exists
        
    Returns:
        Path to the saved CSV file
        
    Raises:
        ValueError: If data fetch fails or returns empty data
    """
    # Ensure data folder exists
    data_path = Path(datas_folder)
    data_path.mkdir(parents=True, exist_ok=True)
    
    # Generate filename
    data_filename = data_path / f'{ticker}-{start}-to-{end}.csv'
    
    # Check if file already exists
    if data_filename.exists() and not force_download:
        logger.info(f"Using cached data: {data_filename}")
        return str(data_filename)
    
    # Fetch the data
    logger.info(f"Fetching data for {ticker} from {start} to {end}")
    data = yf.download(ticker, start=start, end=end, auto_adjust=False, progress=False)
    
    if data.empty:
        raise ValueError(f"Failed to fetch data for {ticker} from Yahoo Finance")
    
    # Extract relevant columns
    data = data[['Open', 'High', 'Low', 'Close', 'Adj Close', 'Volume']]
    
    # Format for Backtrader
    data.index = data.index.strftime('%Y-%m-%d')
    data.index.name = 'Date'
    data.reset_index(inplace=True)
    
    # Remove rows with missing data
    data.dropna(inplace=True)
    
    # Save to CSV in Backtrader format
    data.to_csv(data_filename, index=False)
    
    logger.info(f"Saved data to {data_filename} ({len(data)} rows)")
    return str(data_filename)


def fetch_multiple_tickers(
    tickers: list[str],
    start: str,
    end: str,
    datas_folder: str = "datas",
    force_download: bool = False
) -> dict[str, str]:
    """
    Fetch data for multiple tickers.
    
    Args:
        tickers: List of ticker symbols
        start: Start date in 'YYYY-MM-DD' format
        end: End date in 'YYYY-MM-DD' format
        datas_folder: Path to the folder to save CSV files
        force_download: If True, re-download even if files exist
        
    Returns:
        Dictionary mapping ticker to CSV file path
    """
    results = {}
    for ticker in tickers:
        try:
            results[ticker] = fetch_and_save_data(ticker, start, end, datas_folder, force_download)
        except Exception as e:
            logger.error(f"Failed to fetch data for {ticker}: {e}")
    
    return results
