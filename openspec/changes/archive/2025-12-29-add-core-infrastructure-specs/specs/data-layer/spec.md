## ADDED Requirements

### Requirement: Market Data Fetching
The system SHALL fetch historical market data from Yahoo Finance.

#### Scenario: Fetch single ticker data
- **WHEN** user requests data for ticker "AAPL" from "2024-01-01" to "2024-03-01"
- **THEN** system downloads OHLCV data from Yahoo Finance

#### Scenario: Handle empty data response
- **WHEN** Yahoo Finance returns empty data
- **THEN** system raises ValueError with descriptive error message

#### Scenario: Format data for Backtrader
- **WHEN** data is successfully fetched
- **THEN** system formats columns as Date, Open, High, Low, Close, Adj Close, Volume


### Requirement: Data Caching
The system SHALL cache fetched data to avoid redundant downloads.

#### Scenario: Use cached data
- **WHEN** data file already exists for ticker and date range
- **THEN** system returns cached file path without re-downloading

#### Scenario: Force re-download
- **WHEN** user sets force_download=True
- **THEN** system re-downloads data even if cache exists

#### Scenario: Cache file naming
- **WHEN** data is fetched for ticker "AAPL" from "2024-01-01" to "2024-03-01"
- **THEN** system saves to `{datas_folder}/AAPL-2024-01-01-to-2024-03-01.csv`


### Requirement: Data Directory Management
The system SHALL manage the data storage directory.

#### Scenario: Create data directory
- **WHEN** data directory does not exist
- **THEN** system creates the directory before saving data

#### Scenario: Custom data folder
- **WHEN** user specifies custom datas_folder path
- **THEN** system uses specified path for data storage


### Requirement: Multiple Ticker Support
The system SHALL support fetching data for multiple tickers.

#### Scenario: Fetch multiple tickers
- **WHEN** user provides list of tickers ["AAPL", "MSFT", "GOOG"]
- **THEN** system fetches and caches data for each ticker

#### Scenario: Partial failure handling
- **WHEN** one ticker fails to fetch but others succeed
- **THEN** system continues fetching remaining tickers and reports failures

#### Scenario: Return ticker to file mapping
- **WHEN** multiple tickers are fetched successfully
- **THEN** system returns dictionary mapping ticker to file path


### Requirement: Data Quality
The system SHALL ensure data quality before saving.

#### Scenario: Remove missing data rows
- **WHEN** fetched data contains NaN values
- **THEN** system removes rows with missing data before saving

#### Scenario: Date formatting
- **WHEN** data is saved to CSV
- **THEN** dates are formatted as YYYY-MM-DD strings
