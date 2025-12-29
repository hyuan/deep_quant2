# data-layer Specification Delta

## ADDED Requirements

### Requirement: Cache Metadata Tracking
The system SHALL maintain a cache index with metadata for each cached data file.

#### Scenario: Record cache entry on download
- **WHEN** data is downloaded and saved for ticker "AAPL"
- **THEN** system creates cache index entry with ticker, date range, download time, row count, and checksum

#### Scenario: Load cache index on startup
- **WHEN** system starts or first cache operation occurs
- **THEN** system loads `.cache_index.json` from datas folder if it exists

#### Scenario: Persist cache index on update
- **WHEN** cache entry is added or removed
- **THEN** system atomically updates `.cache_index.json` file

### Requirement: Cache Validation
The system SHALL validate cached data integrity before use.

#### Scenario: Checksum validation on cache hit
- **WHEN** cache hit occurs
- **THEN** system verifies file checksum matches index entry

#### Scenario: Re-fetch on checksum mismatch
- **GIVEN** checksum validation fails
- **WHEN** data is requested
- **THEN** system removes invalid entry and re-downloads data

#### Scenario: Handle missing cache files
- **GIVEN** cache index entry exists but file is missing
- **WHEN** data is requested
- **THEN** system removes orphan entry and re-downloads data

### Requirement: Cache Management
The system SHALL provide functions to inspect and manage cached data.

#### Scenario: List cached data
- **WHEN** user calls list_cached_data()
- **THEN** system returns all cache entries with metadata

#### Scenario: Clear all cache
- **WHEN** user calls clear_cache()
- **THEN** system removes all cache files and index entries

#### Scenario: Clear cache by ticker
- **WHEN** user calls clear_cache(ticker="AAPL")
- **THEN** system removes only cache entries for specified ticker

#### Scenario: Get cache statistics
- **WHEN** user calls get_cache_stats()
- **THEN** system returns total size, entry count, and date range coverage

### Requirement: Cache Storage Limit
The system SHALL enforce a configurable maximum cache size to prevent unbounded disk usage.

#### Scenario: Enforce storage limit on new download
- **GIVEN** cache storage limit is set to 100 MB
- **AND** current cache size is 95 MB
- **WHEN** new data download would exceed limit
- **THEN** system evicts oldest accessed entries until space is available

#### Scenario: Configure storage limit
- **WHEN** user sets cache_limit_mb parameter
- **THEN** system uses specified limit for eviction decisions

#### Scenario: Default storage limit
- **WHEN** no cache limit is configured
- **THEN** system uses default limit of 100 MB

#### Scenario: Disable storage limit
- **WHEN** user sets cache_limit_mb=0
- **THEN** system allows unlimited cache growth

### Requirement: Cache Enable/Disable
The system SHALL support disabling caching entirely via parameter or persistent setting.

#### Scenario: Disable cache via parameter
- **WHEN** user calls fetch_and_save_data with use_cache=False
- **THEN** system downloads fresh data without checking or updating cache index

#### Scenario: Disable cache via settings
- **WHEN** `.cache_index.json` has settings.enabled=false
- **THEN** system bypasses cache for all data fetches

#### Scenario: Default cache enabled
- **WHEN** no enabled setting is configured
- **THEN** system defaults to enabled=true (caching active)

#### Scenario: Cache stats shows enabled status
- **WHEN** user calls get_cache_stats()
- **THEN** response includes "enabled" field indicating current cache state

## MODIFIED Requirements

### Requirement: Data Caching
The system SHALL cache fetched data to avoid redundant downloads.

#### Scenario: Use cached data (MODIFIED)
- **WHEN** data file exists for ticker and date range
- **AND** cache entry exists in index
- **AND** checksum validation passes
- **THEN** system returns cached file path without re-downloading

> **Delta**: Added conditions for index entry and checksum validation

#### Scenario: Cache file naming
- **WHEN** data is fetched for ticker "AAPL" from "2024-01-01" to "2024-03-01"
- **THEN** system saves to `{datas_folder}/AAPL-2024-01-01-to-2024-03-01.csv`
- **AND** system records entry in `.cache_index.json`

> **Delta**: Added cache index recording
