"""Tests for cache index functionality."""

import json
import os
import tempfile
from datetime import datetime
from pathlib import Path

import pytest

from utils.cache_index import (
    CacheEntry,
    CacheIndex,
    calculate_checksum,
    validate_cache_entry,
    DEFAULT_MAX_SIZE_MB,
)


@pytest.fixture
def temp_datas_folder():
    """Create a temporary data folder for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture
def sample_entry():
    """Create a sample cache entry."""
    now = datetime.now().isoformat()
    return CacheEntry(
        ticker="AAPL",
        start_date="2024-01-01",
        end_date="2024-03-01",
        file_path="datas/AAPL-2024-01-01-to-2024-03-01.csv",
        download_time=now,
        last_accessed=now,
        file_size_bytes=4585,
        row_count=42,
        checksum="abc123def456",
        source="yfinance",
    )


@pytest.fixture
def sample_csv_content():
    """Sample CSV content for testing."""
    return """Date,Open,High,Low,Close,Adj Close,Volume
2024-01-02,100.0,101.0,99.0,100.5,100.5,1000000
2024-01-03,100.5,102.0,100.0,101.0,101.0,1100000
2024-01-04,101.0,103.0,100.5,102.5,102.5,1200000
"""


class TestCacheEntry:
    """Tests for CacheEntry dataclass."""

    def test_to_dict(self, sample_entry):
        """Test converting entry to dictionary."""
        d = sample_entry.to_dict()
        assert d["ticker"] == "AAPL"
        assert d["start_date"] == "2024-01-01"
        assert d["end_date"] == "2024-03-01"
        assert d["row_count"] == 42

    def test_from_dict(self, sample_entry):
        """Test creating entry from dictionary."""
        d = sample_entry.to_dict()
        entry = CacheEntry.from_dict(d)
        assert entry.ticker == sample_entry.ticker
        assert entry.start_date == sample_entry.start_date
        assert entry.checksum == sample_entry.checksum


class TestCacheIndex:
    """Tests for CacheIndex class."""

    def test_init_creates_empty_index(self, temp_datas_folder):
        """Test initialization with empty folder."""
        index = CacheIndex(temp_datas_folder)
        assert len(index.list_entries()) == 0
        assert index.max_size_mb == DEFAULT_MAX_SIZE_MB

    def test_add_entry(self, temp_datas_folder, sample_entry):
        """Test adding a cache entry."""
        index = CacheIndex(temp_datas_folder)
        sample_entry.file_path = f"{temp_datas_folder}/AAPL-2024-01-01-to-2024-03-01.csv"
        index.add_entry(sample_entry)

        assert len(index.list_entries()) == 1
        # Verify persisted
        index2 = CacheIndex(temp_datas_folder)
        assert len(index2.list_entries()) == 1

    def test_get_entry(self, temp_datas_folder, sample_entry):
        """Test retrieving a cache entry by filename."""
        index = CacheIndex(temp_datas_folder)
        sample_entry.file_path = f"{temp_datas_folder}/AAPL-2024-01-01-to-2024-03-01.csv"
        index.add_entry(sample_entry)

        entry = index.get_entry("AAPL-2024-01-01-to-2024-03-01.csv")
        assert entry is not None
        assert entry.ticker == "AAPL"

    def test_get_entry_by_range(self, temp_datas_folder, sample_entry):
        """Test retrieving entry by ticker and date range."""
        index = CacheIndex(temp_datas_folder)
        sample_entry.file_path = f"{temp_datas_folder}/AAPL-2024-01-01-to-2024-03-01.csv"
        index.add_entry(sample_entry)

        entry = index.get_entry_by_range("AAPL", "2024-01-01", "2024-03-01")
        assert entry is not None
        assert entry.ticker == "AAPL"

        # Non-existent range
        entry = index.get_entry_by_range("AAPL", "2024-06-01", "2024-07-01")
        assert entry is None

    def test_remove_entry(self, temp_datas_folder, sample_entry):
        """Test removing a cache entry."""
        index = CacheIndex(temp_datas_folder)
        sample_entry.file_path = f"{temp_datas_folder}/AAPL-2024-01-01-to-2024-03-01.csv"
        index.add_entry(sample_entry)

        result = index.remove_entry("AAPL-2024-01-01-to-2024-03-01.csv")
        assert result is True
        assert len(index.list_entries()) == 0

        # Remove non-existent
        result = index.remove_entry("nonexistent.csv")
        assert result is False

    def test_get_entries_for_ticker(self, temp_datas_folder):
        """Test getting all entries for a specific ticker."""
        index = CacheIndex(temp_datas_folder)
        now = datetime.now().isoformat()

        # Add entries for different tickers
        for ticker, start, end in [
            ("AAPL", "2024-01-01", "2024-03-01"),
            ("AAPL", "2024-04-01", "2024-06-01"),
            ("MSFT", "2024-01-01", "2024-03-01"),
        ]:
            entry = CacheEntry(
                ticker=ticker,
                start_date=start,
                end_date=end,
                file_path=f"{temp_datas_folder}/{ticker}-{start}-to-{end}.csv",
                download_time=now,
                last_accessed=now,
                file_size_bytes=1000,
                row_count=10,
                checksum="test",
            )
            index.add_entry(entry)

        aapl_entries = index.get_entries_for_ticker("AAPL")
        assert len(aapl_entries) == 2

        msft_entries = index.get_entries_for_ticker("MSFT")
        assert len(msft_entries) == 1

    def test_find_overlapping_entries(self, temp_datas_folder):
        """Test finding entries that overlap with a date range."""
        index = CacheIndex(temp_datas_folder)
        now = datetime.now().isoformat()

        # Add entry for Jan-Mar
        entry = CacheEntry(
            ticker="AAPL",
            start_date="2024-01-01",
            end_date="2024-03-31",
            file_path=f"{temp_datas_folder}/AAPL-2024-01-01-to-2024-03-31.csv",
            download_time=now,
            last_accessed=now,
            file_size_bytes=1000,
            row_count=10,
            checksum="test",
        )
        index.add_entry(entry)

        # Should overlap with Feb-Apr
        overlapping = index.find_overlapping_entries("AAPL", "2024-02-01", "2024-04-30")
        assert len(overlapping) == 1

        # Should not overlap with May-Jun
        overlapping = index.find_overlapping_entries("AAPL", "2024-05-01", "2024-06-30")
        assert len(overlapping) == 0

    def test_find_covering_entry(self, temp_datas_folder):
        """Test finding an entry that fully covers a date range."""
        index = CacheIndex(temp_datas_folder)
        now = datetime.now().isoformat()

        # Add entry for Jan-Jun
        entry = CacheEntry(
            ticker="AAPL",
            start_date="2024-01-01",
            end_date="2024-06-30",
            file_path=f"{temp_datas_folder}/AAPL-2024-01-01-to-2024-06-30.csv",
            download_time=now,
            last_accessed=now,
            file_size_bytes=1000,
            row_count=10,
            checksum="test",
        )
        index.add_entry(entry)

        # Should find covering entry for Feb-Mar (within Jan-Jun)
        covering = index.find_covering_entry("AAPL", "2024-02-01", "2024-03-31")
        assert covering is not None
        assert covering.start_date == "2024-01-01"

        # Should not find covering entry for Nov-Dec (outside Jan-Jun)
        covering = index.find_covering_entry("AAPL", "2024-11-01", "2024-12-31")
        assert covering is None

    def test_update_last_accessed(self, temp_datas_folder, sample_entry):
        """Test updating last_accessed timestamp."""
        index = CacheIndex(temp_datas_folder)
        old_time = "2024-01-01T00:00:00"
        sample_entry.last_accessed = old_time
        sample_entry.file_path = f"{temp_datas_folder}/AAPL-2024-01-01-to-2024-03-01.csv"
        index.add_entry(sample_entry)

        index.update_last_accessed("AAPL-2024-01-01-to-2024-03-01.csv")

        entry = index.get_entry("AAPL-2024-01-01-to-2024-03-01.csv")
        assert entry.last_accessed != old_time

    def test_get_total_size_bytes(self, temp_datas_folder):
        """Test calculating total cache size."""
        index = CacheIndex(temp_datas_folder)
        now = datetime.now().isoformat()

        for i, size in enumerate([1000, 2000, 3000]):
            entry = CacheEntry(
                ticker="AAPL",
                start_date=f"2024-0{i+1}-01",
                end_date=f"2024-0{i+1}-28",
                file_path=f"{temp_datas_folder}/AAPL-2024-0{i+1}-01-to-2024-0{i+1}-28.csv",
                download_time=now,
                last_accessed=now,
                file_size_bytes=size,
                row_count=10,
                checksum="test",
            )
            index.add_entry(entry)

        assert index.get_total_size_bytes() == 6000

    def test_enforce_storage_limit(self, temp_datas_folder):
        """Test LRU eviction when storage limit exceeded."""
        # Set a small limit (5 KB)
        index = CacheIndex(temp_datas_folder, max_size_mb=0.005)

        # Create actual files
        for i, (time_offset, size) in enumerate([
            ("2024-01-01T00:00:00", 2000),
            ("2024-01-02T00:00:00", 2000),
            ("2024-01-03T00:00:00", 2000),
        ]):
            filename = f"AAPL-2024-0{i+1}-01-to-2024-0{i+1}-28.csv"
            filepath = Path(temp_datas_folder) / filename

            # Create a file of the specified size
            with open(filepath, "wb") as f:
                f.write(b"x" * size)

            entry = CacheEntry(
                ticker="AAPL",
                start_date=f"2024-0{i+1}-01",
                end_date=f"2024-0{i+1}-28",
                file_path=str(filepath),
                download_time=time_offset,
                last_accessed=time_offset,
                file_size_bytes=size,
                row_count=10,
                checksum="test",
            )
            index.add_entry(entry)

        # Total is 6000 bytes, limit is ~5000 bytes
        # Should evict oldest entry
        evicted = index.enforce_storage_limit()
        assert len(evicted) >= 1
        assert index.get_total_size_bytes() <= 5 * 1024  # 5 KB

    def test_enforce_storage_limit_unlimited(self, temp_datas_folder):
        """Test that unlimited storage (max_size_mb=0) doesn't evict."""
        index = CacheIndex(temp_datas_folder, max_size_mb=0)
        now = datetime.now().isoformat()

        for i in range(10):
            entry = CacheEntry(
                ticker="AAPL",
                start_date=f"2024-{i+1:02d}-01",
                end_date=f"2024-{i+1:02d}-28",
                file_path=f"{temp_datas_folder}/AAPL-2024-{i+1:02d}-01-to-2024-{i+1:02d}-28.csv",
                download_time=now,
                last_accessed=now,
                file_size_bytes=1000000,  # 1 MB each
                row_count=10,
                checksum="test",
            )
            index.add_entry(entry)

        evicted = index.enforce_storage_limit()
        assert len(evicted) == 0
        assert len(index.list_entries()) == 10

    def test_get_stats(self, temp_datas_folder):
        """Test getting cache statistics."""
        index = CacheIndex(temp_datas_folder)
        now = datetime.now().isoformat()

        # Add some entries
        for ticker in ["AAPL", "MSFT"]:
            entry = CacheEntry(
                ticker=ticker,
                start_date="2024-01-01",
                end_date="2024-03-01",
                file_path=f"{temp_datas_folder}/{ticker}-2024-01-01-to-2024-03-01.csv",
                download_time=now,
                last_accessed=now,
                file_size_bytes=5000,
                row_count=50,
                checksum="test",
            )
            index.add_entry(entry)

        stats = index.get_stats()
        assert stats["entry_count"] == 2
        assert stats["total_size_bytes"] == 10000
        assert stats["enabled"] is True
        assert set(stats["tickers"]) == {"AAPL", "MSFT"}

    def test_get_stats_empty(self, temp_datas_folder):
        """Test getting stats for empty cache."""
        index = CacheIndex(temp_datas_folder)
        stats = index.get_stats()

        assert stats["entry_count"] == 0
        assert stats["total_size_bytes"] == 0
        assert stats["enabled"] is True
        assert stats["tickers"] == []

    def test_enabled_setting(self, temp_datas_folder):
        """Test cache enabled/disabled setting."""
        # Default is enabled
        index = CacheIndex(temp_datas_folder)
        assert index.enabled is True

        # Can be disabled
        index.enabled = False
        index._save()

        # Persists across instances
        index2 = CacheIndex(temp_datas_folder)
        assert index2.enabled is False

        # Re-enable
        index2.enabled = True
        index2._save()

        index3 = CacheIndex(temp_datas_folder)
        assert index3.enabled is True

    def test_clear_all(self, temp_datas_folder):
        """Test clearing all cache entries."""
        index = CacheIndex(temp_datas_folder)
        now = datetime.now().isoformat()

        # Add entries and create files
        for ticker in ["AAPL", "MSFT"]:
            filepath = Path(temp_datas_folder) / f"{ticker}-2024-01-01-to-2024-03-01.csv"
            filepath.write_text("test data")

            entry = CacheEntry(
                ticker=ticker,
                start_date="2024-01-01",
                end_date="2024-03-01",
                file_path=str(filepath),
                download_time=now,
                last_accessed=now,
                file_size_bytes=100,
                row_count=10,
                checksum="test",
            )
            index.add_entry(entry)

        count = index.clear()
        assert count == 2
        assert len(index.list_entries()) == 0

    def test_clear_by_ticker(self, temp_datas_folder):
        """Test clearing cache entries for specific ticker."""
        index = CacheIndex(temp_datas_folder)
        now = datetime.now().isoformat()

        # Add entries and create files
        for ticker in ["AAPL", "MSFT"]:
            filepath = Path(temp_datas_folder) / f"{ticker}-2024-01-01-to-2024-03-01.csv"
            filepath.write_text("test data")

            entry = CacheEntry(
                ticker=ticker,
                start_date="2024-01-01",
                end_date="2024-03-01",
                file_path=str(filepath),
                download_time=now,
                last_accessed=now,
                file_size_bytes=100,
                row_count=10,
                checksum="test",
            )
            index.add_entry(entry)

        count = index.clear(ticker="AAPL")
        assert count == 1
        assert len(index.list_entries()) == 1
        assert index.list_entries()[0].ticker == "MSFT"


class TestChecksum:
    """Tests for checksum calculation and validation."""

    def test_calculate_checksum(self, temp_datas_folder, sample_csv_content):
        """Test MD5 checksum calculation."""
        filepath = Path(temp_datas_folder) / "test.csv"
        filepath.write_text(sample_csv_content)

        checksum = calculate_checksum(str(filepath))
        assert len(checksum) == 32  # MD5 hex digest length
        assert checksum.isalnum()

        # Same content should produce same checksum
        filepath2 = Path(temp_datas_folder) / "test2.csv"
        filepath2.write_text(sample_csv_content)
        checksum2 = calculate_checksum(str(filepath2))
        assert checksum == checksum2

    def test_validate_cache_entry_valid(self, temp_datas_folder, sample_csv_content):
        """Test validation passes for valid entry."""
        filepath = Path(temp_datas_folder) / "AAPL-2024-01-01-to-2024-03-01.csv"
        filepath.write_text(sample_csv_content)
        checksum = calculate_checksum(str(filepath))

        entry = CacheEntry(
            ticker="AAPL",
            start_date="2024-01-01",
            end_date="2024-03-01",
            file_path=str(filepath),
            download_time=datetime.now().isoformat(),
            last_accessed=datetime.now().isoformat(),
            file_size_bytes=len(sample_csv_content),
            row_count=3,
            checksum=checksum,
        )

        assert validate_cache_entry(entry) is True

    def test_validate_cache_entry_missing_file(self, temp_datas_folder):
        """Test validation fails for missing file."""
        entry = CacheEntry(
            ticker="AAPL",
            start_date="2024-01-01",
            end_date="2024-03-01",
            file_path=f"{temp_datas_folder}/nonexistent.csv",
            download_time=datetime.now().isoformat(),
            last_accessed=datetime.now().isoformat(),
            file_size_bytes=100,
            row_count=10,
            checksum="abc123",
        )

        assert validate_cache_entry(entry) is False

    def test_validate_cache_entry_bad_checksum(self, temp_datas_folder, sample_csv_content):
        """Test validation fails for checksum mismatch."""
        filepath = Path(temp_datas_folder) / "AAPL-2024-01-01-to-2024-03-01.csv"
        filepath.write_text(sample_csv_content)

        entry = CacheEntry(
            ticker="AAPL",
            start_date="2024-01-01",
            end_date="2024-03-01",
            file_path=str(filepath),
            download_time=datetime.now().isoformat(),
            last_accessed=datetime.now().isoformat(),
            file_size_bytes=len(sample_csv_content),
            row_count=3,
            checksum="wrongchecksum123",  # Invalid checksum
        )

        assert validate_cache_entry(entry) is False


class TestPersistence:
    """Tests for cache index persistence."""

    def test_index_persists_across_instances(self, temp_datas_folder, sample_entry):
        """Test that cache index persists across instances."""
        sample_entry.file_path = f"{temp_datas_folder}/AAPL-2024-01-01-to-2024-03-01.csv"

        # Add entry in first instance
        index1 = CacheIndex(temp_datas_folder)
        index1.add_entry(sample_entry)

        # Load in second instance
        index2 = CacheIndex(temp_datas_folder)
        entry = index2.get_entry("AAPL-2024-01-01-to-2024-03-01.csv")

        assert entry is not None
        assert entry.ticker == "AAPL"

    def test_settings_persist(self, temp_datas_folder):
        """Test that settings persist across instances."""
        index1 = CacheIndex(temp_datas_folder, max_size_mb=50)
        index1._save()  # Force save

        index2 = CacheIndex(temp_datas_folder)
        assert index2.max_size_mb == 50

    def test_corrupt_index_handled(self, temp_datas_folder):
        """Test that corrupt index file is handled gracefully."""
        # Write corrupt JSON
        index_path = Path(temp_datas_folder) / ".cache_index.json"
        index_path.parent.mkdir(parents=True, exist_ok=True)
        index_path.write_text("{ corrupt json")

        # Should not raise, just start fresh
        index = CacheIndex(temp_datas_folder)
        assert len(index.list_entries()) == 0
