# Proposal: Improve Data Caching Mechanism

## Summary

Enhance the market data caching system to support cache expiration, date range overlap detection, partial cache reuse, and cache metadata management.

## Problem Statement

The current data caching mechanism has several limitations:

1. **No date range overlap detection** - Requesting AAPL 2024-01-01 to 2024-03-01 and then AAPL 2024-02-01 to 2024-04-01 downloads twice instead of reusing overlapping data
2. **No cache metadata** - No way to track when data was downloaded, source, or data quality
3. **No cache validation** - No integrity checks for corrupted files
4. **No cache cleanup** - Old/unused cache files accumulate indefinitely

## Proposed Solution

Implement a smarter caching layer with:

1. **Cache metadata storage** - Track download timestamps, row counts, and checksums in a JSON index file
2. **Date range coalescing** - Detect overlapping date ranges and reuse/extend existing cache files
3. **Cache validation** - Verify file integrity before serving cached data
4. **Cache management commands** - Clear, list, and inspect cached data

> **Note**: Historical market data is immutable once downloaded, so cache expiration is not needed.

## Impact Analysis

### Files Changed

| File | Change Type | Description |
|------|-------------|-------------|
| `utils/yf_utils.py` | Modified | Add CacheManager class and metadata handling |
| `mcp_server/server.py` | Modified | Add cache management MCP tools |
| `utils/cache_index.py` | New | Cache index file management |
| `tests/test_cache.py` | New | Unit tests for caching |

### Breaking Changes

None. Existing behavior preserved - enhancements are additive.

### Dependencies

No new dependencies required. Uses standard library (json, hashlib, datetime).

## Success Criteria

- [ ] Cache files have metadata tracking download time
- [ ] Overlapping date ranges reuse cached data where possible
- [ ] Cache validation detects corrupted files
- [ ] MCP tools available to list/clear cache

## Alternatives Considered

1. **Database-backed cache** - Overkill for file-based data; CSV files are sufficient
2. **External caching library (diskcache)** - Adds dependency; custom solution fits better
3. **In-memory caching only** - Loses data between sessions; disk cache needed

## Timeline

Estimated: 2-3 hours implementation + testing
