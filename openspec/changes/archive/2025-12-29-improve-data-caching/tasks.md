# Tasks: Improve Data Caching

## Implementation Checklist

### Phase 1: Cache Metadata Foundation

- [x] **Create cache index module** (`utils/cache_index.py`)
  - Define `CacheEntry` dataclass with: ticker, start_date, end_date, file_path, download_time, row_count, checksum
  - Implement `CacheIndex` class to read/write `.cache_index.json` in datas folder
  - Add methods: `add_entry()`, `get_entry()`, `remove_entry()`, `list_entries()`

- [x] **Add checksum calculation**
  - Implement MD5 hash of CSV content for integrity validation
  - Store checksum in cache index on save
  - Validate checksum on cache hit

### Phase 2: Smart Caching Logic

- [x] **Add date range overlap detection**
  - Find existing cache entries that overlap with requested date range
  - If existing cache fully covers requested range → use cache
  - If partial overlap → fetch only missing date ranges and merge

- [x] **Implement cache validation**
  - Verify file exists and checksum matches on cache hit
  - If validation fails, remove entry and re-fetch
  - Log validation failures for debugging

### Phase 3: Cache Management

- [x] **Add cache listing function**
  - `list_cached_data()` returns all entries with metadata
  - Include file size, download time, coverage info

- [x] **Add cache clearing function**
  - `clear_cache(ticker=None, before_date=None)` for selective clearing
  - Remove both files and index entries

- [x] **Add cache info function**
  - `get_cache_info(ticker, start, end)` shows what's cached for a request

- [x] **Implement storage limit enforcement**
  - Track `last_accessed` timestamp in cache entries
  - Calculate total cache size before adding new entries
  - Evict LRU (least recently used) entries when limit exceeded
  - Default limit: 100 MB, configurable via parameter

- [x] **Add cache enable/disable option**
  - Add `use_cache` parameter to `fetch_and_save_data()` for per-call control
  - Add `enabled` setting in `.cache_index.json` for persistent disable
  - When disabled, bypass all cache logic and always download fresh

### Phase 4: MCP Integration

- [x] **Add MCP tool: list_cached_data**
  - Returns cached files with metadata
  - Useful for understanding cache state

- [x] **Add MCP tool: clear_cache**
  - Clears cache files (all or by ticker)
  - Returns count of removed files

- [x] **Add MCP tool: get_cache_stats**
  - Total cache size, entry count, oldest/newest entries

### Phase 5: Testing & Documentation

- [x] **Write unit tests** (`tests/test_cache.py`)
  - Test cache index CRUD operations
  - Test checksum validation
  - Test date range overlap detection
  - Test storage limit enforcement

- [x] **Update data-layer spec**
  - Add requirements for new cache behaviors
  - Document storage limit defaults
  - Add scenarios for overlap detection

## Dependencies

- Phase 2 depends on Phase 1 (cache index must exist)
- Phase 3 depends on Phase 2 (management uses same index)
- Phase 4 depends on Phase 3 (MCP exposes management functions)
- Phase 5 can proceed in parallel with implementation phases

## Verification

Each task verified by:
1. Unit test passes
2. Manual MCP tool invocation works
3. Cache files have correct metadata
