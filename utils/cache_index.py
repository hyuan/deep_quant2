"""Cache index management for market data files."""

import hashlib
import json
import logging
from dataclasses import dataclass, field, asdict
from datetime import datetime, date
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# Default cache size limit: 100 MB
DEFAULT_MAX_SIZE_MB = 100
CACHE_INDEX_FILENAME = ".cache_index.json"


@dataclass
class CacheEntry:
    """Metadata for a cached data file."""

    ticker: str
    start_date: str  # YYYY-MM-DD
    end_date: str  # YYYY-MM-DD
    file_path: str
    download_time: str  # ISO format
    last_accessed: str  # ISO format
    file_size_bytes: int
    row_count: int
    checksum: str
    source: str = "yfinance"

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "CacheEntry":
        """Create from dictionary."""
        return cls(**data)


class CacheIndex:
    """Manages the cache index file for market data."""

    def __init__(self, datas_folder: str = "datas", max_size_mb: int = DEFAULT_MAX_SIZE_MB, enabled: bool = True):
        """
        Initialize the cache index.

        Args:
            datas_folder: Path to the data folder
            max_size_mb: Maximum cache size in MB (0 for unlimited)
            enabled: Whether caching is enabled (can be overridden by .cache_index.json)
        """
        self.datas_folder = Path(datas_folder)
        self.index_path = self.datas_folder / CACHE_INDEX_FILENAME
        self.max_size_mb = max_size_mb
        self.enabled = enabled
        self._entries: dict[str, CacheEntry] = {}
        self._load()

    def _load(self) -> None:
        """Load the cache index from disk."""
        if not self.index_path.exists():
            logger.debug(f"Cache index not found at {self.index_path}, starting fresh")
            return

        try:
            with open(self.index_path, "r") as f:
                data = json.load(f)

            # Load settings
            settings = data.get("settings", {})
            if "max_size_mb" in settings:
                self.max_size_mb = settings["max_size_mb"]
            if "enabled" in settings:
                self.enabled = settings["enabled"]

            # Load entries
            entries_data = data.get("entries", {})
            for filename, entry_data in entries_data.items():
                try:
                    self._entries[filename] = CacheEntry.from_dict(entry_data)
                except (TypeError, KeyError) as e:
                    logger.warning(f"Invalid cache entry {filename}: {e}")

            logger.debug(f"Loaded {len(self._entries)} cache entries")
        except (json.JSONDecodeError, IOError) as e:
            logger.warning(f"Failed to load cache index: {e}")
            self._entries = {}

    def _save(self) -> None:
        """Save the cache index to disk atomically."""
        self.datas_folder.mkdir(parents=True, exist_ok=True)

        data = {
            "version": 1,
            "settings": {"max_size_mb": self.max_size_mb, "enabled": self.enabled},
            "entries": {filename: entry.to_dict() for filename, entry in self._entries.items()},
        }

        # Write to temp file then rename for atomicity
        temp_path = self.index_path.with_suffix(".tmp")
        try:
            with open(temp_path, "w") as f:
                json.dump(data, f, indent=2)
            temp_path.replace(self.index_path)
            logger.debug(f"Saved cache index with {len(self._entries)} entries")
        except IOError as e:
            logger.error(f"Failed to save cache index: {e}")
            if temp_path.exists():
                temp_path.unlink()
            raise

    def add_entry(self, entry: CacheEntry) -> None:
        """
        Add or update a cache entry.

        Args:
            entry: The cache entry to add
        """
        filename = Path(entry.file_path).name
        self._entries[filename] = entry
        self._save()

    def get_entry(self, filename: str) -> Optional[CacheEntry]:
        """
        Get a cache entry by filename.

        Args:
            filename: The filename (without path) to look up

        Returns:
            The cache entry or None if not found
        """
        return self._entries.get(filename)

    def get_entry_by_range(
        self, ticker: str, start_date: str, end_date: str
    ) -> Optional[CacheEntry]:
        """
        Get a cache entry by ticker and exact date range.

        Args:
            ticker: Stock ticker symbol
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format

        Returns:
            The cache entry or None if not found
        """
        filename = f"{ticker}-{start_date}-to-{end_date}.csv"
        return self.get_entry(filename)

    def remove_entry(self, filename: str) -> bool:
        """
        Remove a cache entry.

        Args:
            filename: The filename to remove

        Returns:
            True if entry was removed, False if not found
        """
        if filename in self._entries:
            del self._entries[filename]
            self._save()
            return True
        return False

    def list_entries(self) -> list[CacheEntry]:
        """
        List all cache entries.

        Returns:
            List of all cache entries
        """
        return list(self._entries.values())

    def get_entries_for_ticker(self, ticker: str) -> list[CacheEntry]:
        """
        Get all cache entries for a specific ticker.

        Args:
            ticker: Stock ticker symbol

        Returns:
            List of cache entries for the ticker
        """
        return [e for e in self._entries.values() if e.ticker == ticker]

    def find_overlapping_entries(
        self, ticker: str, start_date: str, end_date: str
    ) -> list[CacheEntry]:
        """
        Find cache entries that overlap with the requested date range.

        Args:
            ticker: Stock ticker symbol
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format

        Returns:
            List of overlapping cache entries
        """
        start = datetime.strptime(start_date, "%Y-%m-%d").date()
        end = datetime.strptime(end_date, "%Y-%m-%d").date()

        overlapping = []
        for entry in self.get_entries_for_ticker(ticker):
            entry_start = datetime.strptime(entry.start_date, "%Y-%m-%d").date()
            entry_end = datetime.strptime(entry.end_date, "%Y-%m-%d").date()

            # Check for any overlap
            if entry_start <= end and entry_end >= start:
                overlapping.append(entry)

        return overlapping

    def find_covering_entry(
        self, ticker: str, start_date: str, end_date: str
    ) -> Optional[CacheEntry]:
        """
        Find a single cache entry that fully covers the requested date range.

        Args:
            ticker: Stock ticker symbol
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format

        Returns:
            A cache entry that covers the range, or None
        """
        start = datetime.strptime(start_date, "%Y-%m-%d").date()
        end = datetime.strptime(end_date, "%Y-%m-%d").date()

        for entry in self.get_entries_for_ticker(ticker):
            entry_start = datetime.strptime(entry.start_date, "%Y-%m-%d").date()
            entry_end = datetime.strptime(entry.end_date, "%Y-%m-%d").date()

            # Check if entry fully covers requested range
            if entry_start <= start and entry_end >= end:
                return entry

        return None

    def update_last_accessed(self, filename: str) -> None:
        """
        Update the last_accessed timestamp for an entry.

        Args:
            filename: The filename to update
        """
        if filename in self._entries:
            self._entries[filename].last_accessed = datetime.now().isoformat()
            self._save()

    def get_total_size_bytes(self) -> int:
        """
        Get the total size of all cached files.

        Returns:
            Total size in bytes
        """
        return sum(e.file_size_bytes for e in self._entries.values())

    def enforce_storage_limit(self) -> list[str]:
        """
        Evict LRU entries until cache is under the size limit.

        Returns:
            List of evicted file paths
        """
        if self.max_size_mb == 0:
            return []  # Unlimited

        max_size_bytes = self.max_size_mb * 1024 * 1024
        total_size = self.get_total_size_bytes()

        if total_size <= max_size_bytes:
            return []

        # Sort by last_accessed ascending (oldest first)
        sorted_entries = sorted(
            self._entries.values(),
            key=lambda e: datetime.fromisoformat(e.last_accessed),
        )

        evicted = []
        for entry in sorted_entries:
            if total_size <= max_size_bytes:
                break

            total_size -= entry.file_size_bytes
            filename = Path(entry.file_path).name

            # Remove the file
            file_path = Path(entry.file_path)
            if file_path.exists():
                file_path.unlink()
                logger.info(f"Evicted cache file: {file_path}")

            # Remove from index
            del self._entries[filename]
            evicted.append(entry.file_path)

        if evicted:
            self._save()

        return evicted

    def get_stats(self) -> dict:
        """
        Get cache statistics.

        Returns:
            Dictionary with cache stats
        """
        entries = list(self._entries.values())
        if not entries:
            return {
                "enabled": self.enabled,
                "entry_count": 0,
                "total_size_bytes": 0,
                "total_size_mb": 0.0,
                "max_size_mb": self.max_size_mb,
                "oldest_entry": None,
                "newest_entry": None,
                "tickers": [],
            }

        total_size = self.get_total_size_bytes()
        sorted_by_download = sorted(entries, key=lambda e: e.download_time)

        return {
            "enabled": self.enabled,
            "entry_count": len(entries),
            "total_size_bytes": total_size,
            "total_size_mb": round(total_size / (1024 * 1024), 2),
            "max_size_mb": self.max_size_mb,
            "oldest_entry": sorted_by_download[0].download_time,
            "newest_entry": sorted_by_download[-1].download_time,
            "tickers": list(set(e.ticker for e in entries)),
        }

    def clear(self, ticker: Optional[str] = None) -> int:
        """
        Clear cache entries.

        Args:
            ticker: If provided, only clear entries for this ticker

        Returns:
            Number of entries removed
        """
        to_remove = []

        for filename, entry in self._entries.items():
            if ticker is None or entry.ticker == ticker:
                # Remove the file
                file_path = Path(entry.file_path)
                if file_path.exists():
                    file_path.unlink()
                to_remove.append(filename)

        for filename in to_remove:
            del self._entries[filename]

        if to_remove:
            self._save()
            logger.info(f"Cleared {len(to_remove)} cache entries")

        return len(to_remove)


def calculate_checksum(file_path: str) -> str:
    """
    Calculate MD5 checksum of a file.

    Args:
        file_path: Path to the file

    Returns:
        MD5 hex digest
    """
    hasher = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def validate_cache_entry(entry: CacheEntry) -> bool:
    """
    Validate a cache entry.

    Checks that the file exists and checksum matches.

    Args:
        entry: The cache entry to validate

    Returns:
        True if valid, False otherwise
    """
    file_path = Path(entry.file_path)

    # Check file exists
    if not file_path.exists():
        logger.warning(f"Cache file missing: {file_path}")
        return False

    # Validate checksum
    actual_checksum = calculate_checksum(str(file_path))
    if actual_checksum != entry.checksum:
        logger.warning(
            f"Checksum mismatch for {file_path}: expected {entry.checksum}, got {actual_checksum}"
        )
        return False

    return True
