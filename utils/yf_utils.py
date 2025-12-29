"""Yahoo Finance data fetching and caching utilities."""

import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

import pandas as pd
import yfinance as yf

from .cache_index import (
    CacheIndex,
    CacheEntry,
    calculate_checksum,
    validate_cache_entry,
    DEFAULT_MAX_SIZE_MB,
)


logger = logging.getLogger(__name__)

# Module-level cache index instance (lazy loaded)
_cache_index: Optional[CacheIndex] = None


def get_cache_index(datas_folder: str = "datas") -> CacheIndex:
    """
    Get or create the cache index singleton.

    Args:
        datas_folder: Path to the data folder

    Returns:
        The CacheIndex instance
    """
    global _cache_index
    if _cache_index is None or str(_cache_index.datas_folder) != datas_folder:
        _cache_index = CacheIndex(datas_folder)
    return _cache_index


def _fetch_and_save_raw(ticker: str, start: str, end: str, data_filename: Path) -> str:
    """
    Fetch data from Yahoo Finance and save to CSV without cache indexing.

    Args:
        ticker: Stock ticker symbol
        start: Start date in 'YYYY-MM-DD' format
        end: End date in 'YYYY-MM-DD' format
        data_filename: Path to save the CSV file

    Returns:
        Path to the saved CSV file

    Raises:
        ValueError: If data fetch fails or returns empty data
    """
    data = yf.download(ticker, start=start, end=end, auto_adjust=False, progress=False)

    if data.empty:
        raise ValueError(f"Failed to fetch data for {ticker} from Yahoo Finance")

    # Handle multi-level columns (when multiple tickers downloaded)
    if isinstance(data.columns, pd.MultiIndex):
        data.columns = data.columns.droplevel(1)

    # Extract relevant columns
    data = data[["Open", "High", "Low", "Close", "Adj Close", "Volume"]]

    # Format for Backtrader
    data.index = data.index.strftime("%Y-%m-%d")
    data.index.name = "Date"
    data.reset_index(inplace=True)

    # Remove rows with missing data
    data.dropna(inplace=True)

    # Save to CSV in Backtrader format
    data.to_csv(data_filename, index=False)

    logger.info(f"Saved data to {data_filename} ({len(data)} rows)")
    return str(data_filename)


def fetch_and_save_data(
    ticker: str,
    start: str,
    end: str,
    datas_folder: str = "datas",
    force_download: bool = False,
    max_cache_size_mb: int = DEFAULT_MAX_SIZE_MB,
    use_cache: bool = True,
) -> str:
    """
    Fetch stock data from Yahoo Finance and save to CSV in Backtrader format.

    Args:
        ticker: Stock ticker symbol
        start: Start date in 'YYYY-MM-DD' format
        end: End date in 'YYYY-MM-DD' format
        datas_folder: Path to the folder to save the CSV file
        force_download: If True, re-download even if file exists
        max_cache_size_mb: Maximum cache size in MB (0 for unlimited)
        use_cache: If False, always download fresh data and skip cache indexing

    Returns:
        Path to the saved CSV file

    Raises:
        ValueError: If data fetch fails or returns empty data
    """
    # Ensure data folder exists
    data_path = Path(datas_folder)
    data_path.mkdir(parents=True, exist_ok=True)

    # Generate filename
    data_filename = data_path / f"{ticker}-{start}-to-{end}.csv"

    # If cache is disabled via parameter, always download fresh
    if not use_cache:
        logger.info(f"Cache disabled via parameter, fetching fresh data for {ticker} from {start} to {end}")
        return _fetch_and_save_raw(ticker, start, end, data_filename)

    # Get or create cache index
    cache_index = get_cache_index(datas_folder)
    cache_index.max_size_mb = max_cache_size_mb

    # If cache is disabled via .cache_index.json settings, always download fresh
    if not cache_index.enabled:
        logger.info(f"Cache disabled via settings, fetching fresh data for {ticker} from {start} to {end}")
        return _fetch_and_save_raw(ticker, start, end, data_filename)

    filename_key = data_filename.name

    # Check cache index for exact match
    cached_entry = cache_index.get_entry(filename_key)

    if cached_entry and not force_download:
        # Validate cached entry
        if validate_cache_entry(cached_entry):
            logger.info(f"Using cached data: {data_filename}")
            cache_index.update_last_accessed(filename_key)
            return str(data_filename)
        else:
            # Invalid cache entry, remove it
            logger.warning(f"Cache validation failed for {filename_key}, re-fetching")
            cache_index.remove_entry(filename_key)

    # Check if file exists but not in index (legacy cache)
    if data_filename.exists() and not force_download and not cached_entry:
        logger.info(f"Found legacy cached data: {data_filename}, adding to index")
        # Add to index
        row_count = sum(1 for _ in open(data_filename)) - 1
        checksum = calculate_checksum(str(data_filename))
        file_size = data_filename.stat().st_size
        now = datetime.now().isoformat()

        entry = CacheEntry(
            ticker=ticker,
            start_date=start,
            end_date=end,
            file_path=str(data_filename),
            download_time=now,
            last_accessed=now,
            file_size_bytes=file_size,
            row_count=row_count,
            checksum=checksum,
            source="yfinance",
        )
        cache_index.add_entry(entry)
        return str(data_filename)

    # Check for a covering entry (larger date range that includes this request)
    covering_entry = cache_index.find_covering_entry(ticker, start, end)
    if covering_entry and not force_download:
        if validate_cache_entry(covering_entry):
            logger.info(f"Using covering cache: {covering_entry.file_path} for {ticker} {start} to {end}")
            cache_index.update_last_accessed(Path(covering_entry.file_path).name)
            return covering_entry.file_path
        else:
            cache_index.remove_entry(Path(covering_entry.file_path).name)

    # Enforce storage limit before downloading new data
    evicted = cache_index.enforce_storage_limit()
    if evicted:
        logger.info(f"Evicted {len(evicted)} cache entries to free space")

    # Fetch the data
    logger.info(f"Fetching data for {ticker} from {start} to {end}")
    data = yf.download(ticker, start=start, end=end, auto_adjust=False, progress=False)
    
    if data.empty:
        raise ValueError(f"Failed to fetch data for {ticker} from Yahoo Finance")
    
    # Handle multi-level columns (when multiple tickers downloaded)
    if isinstance(data.columns, pd.MultiIndex):
        data.columns = data.columns.droplevel(1)
    
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

    # Calculate checksum and add to cache index
    checksum = calculate_checksum(str(data_filename))
    file_size = data_filename.stat().st_size
    now = datetime.now().isoformat()

    entry = CacheEntry(
        ticker=ticker,
        start_date=start,
        end_date=end,
        file_path=str(data_filename),
        download_time=now,
        last_accessed=now,
        file_size_bytes=file_size,
        row_count=len(data),
        checksum=checksum,
        source="yfinance",
    )
    cache_index.add_entry(entry)

    logger.info(f"Saved data to {data_filename} ({len(data)} rows)")
    return str(data_filename)


def fetch_multiple_tickers(
    tickers: list[str],
    start: str,
    end: str,
    datas_folder: str = "datas",
    force_download: bool = False,
    max_cache_size_mb: int = DEFAULT_MAX_SIZE_MB,
    use_cache: bool = True,
) -> dict[str, str]:
    """
    Fetch data for multiple tickers.

    Args:
        tickers: List of ticker symbols
        start: Start date in 'YYYY-MM-DD' format
        end: End date in 'YYYY-MM-DD' format
        datas_folder: Path to the folder to save CSV files
        force_download: If True, re-download even if files exist
        max_cache_size_mb: Maximum cache size in MB (0 for unlimited)
        use_cache: If False, always download fresh data and skip cache indexing

    Returns:
        Dictionary mapping ticker to CSV file path
    """
    results = {}
    for ticker in tickers:
        try:
            results[ticker] = fetch_and_save_data(
                ticker, start, end, datas_folder, force_download, max_cache_size_mb, use_cache
            )
        except Exception as e:
            logger.error(f"Failed to fetch data for {ticker}: {e}")

    return results


# Cache management functions


def list_cached_data(datas_folder: str = "datas") -> list[dict]:
    """
    List all cached data files with metadata.

    Args:
        datas_folder: Path to the data folder

    Returns:
        List of cache entry dictionaries
    """
    cache_index = get_cache_index(datas_folder)
    return [entry.to_dict() for entry in cache_index.list_entries()]


def clear_cache(datas_folder: str = "datas", ticker: Optional[str] = None) -> int:
    """
    Clear cached data files.

    Args:
        datas_folder: Path to the data folder
        ticker: If provided, only clear entries for this ticker

    Returns:
        Number of entries removed
    """
    cache_index = get_cache_index(datas_folder)
    return cache_index.clear(ticker)


def get_cache_stats(datas_folder: str = "datas") -> dict:
    """
    Get cache statistics.

    Args:
        datas_folder: Path to the data folder

    Returns:
        Dictionary with cache stats
    """
    cache_index = get_cache_index(datas_folder)
    return cache_index.get_stats()
