# Design: Improve Data Caching

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                     Data Access Layer                            │
├─────────────────────────────────────────────────────────────────┤
│  fetch_and_save_data()                                           │
│       │                                                          │
│       ▼                                                          │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │              CacheManager                                │    │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────────┐  │    │
│  │  │ CacheIndex  │  │ Validator   │  │ DateRangeMerger │  │    │
│  │  │ (.json)     │  │ (checksum)  │  │ (coalesce)      │  │    │
│  │  └─────────────┘  └─────────────┘  └─────────────────┘  │    │
│  └─────────────────────────────────────────────────────────┘    │
│       │                                                          │
│       ▼                                                          │
│  ┌─────────────────┐    ┌─────────────────┐                     │
│  │ Yahoo Finance   │───▶│ CSV Files       │                     │
│  │ (yfinance)      │    │ (datas/*.csv)   │                     │
│  └─────────────────┘    └─────────────────┘                     │
└─────────────────────────────────────────────────────────────────┘
```

## Data Structures

### Cache Index File (`.cache_index.json`)

```json
{
  "version": 1,
  "settings": {
    "max_size_mb": 100,
    "enabled": true
  },
  "entries": {
    "AAPL-2024-01-01-to-2024-03-01.csv": {
      "ticker": "AAPL",
      "start_date": "2024-01-01",
      "end_date": "2024-03-01",
      "file_path": "datas/AAPL-2024-01-01-to-2024-03-01.csv",
      "download_time": "2024-12-28T10:30:00Z",
      "last_accessed": "2024-12-28T14:00:00Z",
      "file_size_bytes": 4585,
      "row_count": 42,
      "checksum": "abc123def456",
      "source": "yfinance"
    }
  }
}
```

### CacheEntry Dataclass

```python
@dataclass
class CacheEntry:
    ticker: str
    start_date: str  # YYYY-MM-DD
    end_date: str    # YYYY-MM-DD
    file_path: str
    download_time: datetime
    last_accessed: datetime
    file_size_bytes: int
    row_count: int
    checksum: str
    source: str = "yfinance"
```

## Key Algorithms

### Cache Lookup Flow

```
Request: fetch_data(AAPL, 2024-01-01, 2024-03-01)
                    │
                    ▼
         ┌─────────────────────┐
         │ Search cache index  │
         │ for overlapping     │
         │ entries             │
         └─────────┬───────────┘
                   │
         ┌─────────┴─────────┐
         │                   │
    Full Match         Partial/No Match
         │                   │
         ▼                   ▼
    ┌─────────┐        ┌─────────────┐
    │ Validate│        │ Fetch from  │
    │ checksum│        │ Yahoo       │
    └────┬────┘        └──────┬──────┘
         │                    │
    Pass │ Fail               │
         │   │                │
         ▼   ▼                ▼
    Return  Re-fetch     Save + Index
    cached
```

> **Note**: No expiration check needed - historical market data is immutable.

### Date Range Overlap Detection

```python
def find_overlapping_entries(ticker: str, start: date, end: date) -> list[CacheEntry]:
    """Find cache entries that overlap with the requested date range."""
    overlapping = []
    for entry in index.get_entries_for_ticker(ticker):
        entry_start = parse_date(entry.start_date)
        entry_end = parse_date(entry.end_date)
        
        # Check for any overlap
        if entry_start <= end and entry_end >= start:
            overlapping.append(entry)
    
    return overlapping

def covers_range(entries: list[CacheEntry], start: date, end: date) -> bool:
    """Check if cache entries fully cover the requested range."""
    if not entries:
        return False
    
    # Sort by start date and check for gaps
    sorted_entries = sorted(entries, key=lambda e: e.start_date)
    covered_until = None
    
    for entry in sorted_entries:
        entry_start = parse_date(entry.start_date)
        entry_end = parse_date(entry.end_date)
        
        if covered_until is None:
            if entry_start > start:
                return False  # Gap at beginning
            covered_until = entry_end
        else:
            if entry_start > covered_until + timedelta(days=1):
                return False  # Gap in middle
            covered_until = max(covered_until, entry_end)
    
    return covered_until >= end
```

## Design Decisions

### Decision 1: Single Index File vs Per-File Metadata

**Choice**: Single `.cache_index.json` file in datas folder

**Rationale**:
- Atomic updates possible (write temp file, rename)
- Easy to inspect entire cache state
- No sidecar files cluttering directory
- Simple backup/restore

### Decision 2: Checksum Algorithm

**Choice**: MD5 hash of file content

**Rationale**:
- Fast to compute for typical CSV sizes
- Sufficient for integrity (not security)
- Standard library support (`hashlib.md5`)
- ~32 hex chars storage

### Decision 3: Date Range Handling

**Choice**: Detect overlap but don't automatically merge/split files

**Rationale**:
- Simpler implementation (no file merging logic)
- Predictable cache file naming
- Can add merging later if needed
- Full-range match is most common case

### Decision 4: Storage Limit with LRU Eviction

**Choice**: Configurable max cache size (default 100 MB) with LRU eviction

**Rationale**:
- Prevents unbounded disk usage over time
- LRU eviction keeps frequently-used data cached
- `last_accessed` timestamp updated on cache hits
- Default 100 MB is sufficient for typical CSV data; set to 0 to disable

```python
def enforce_storage_limit(max_size_bytes: int) -> list[str]:
    """Evict LRU entries until cache is under limit. Returns evicted files."""
    if max_size_bytes == 0:
        return []  # Unlimited
    
    total_size = sum(e.file_size_bytes for e in index.entries.values())
    if total_size <= max_size_bytes:
        return []
    
    # Sort by last_accessed ascending (oldest first)
    sorted_entries = sorted(index.entries.values(), key=lambda e: e.last_accessed)
    evicted = []
    
    for entry in sorted_entries:
        if total_size <= max_size_bytes:
            break
        total_size -= entry.file_size_bytes
        index.remove_entry(entry.file_path)
        Path(entry.file_path).unlink(missing_ok=True)
        evicted.append(entry.file_path)
    
    return evicted
```

## Future Considerations

1. **Async prefetching** - Background fetch for commonly used data
2. **Multiple data sources** - Support other providers beyond yfinance
3. **Compression** - Gzip large CSV files to save disk space
