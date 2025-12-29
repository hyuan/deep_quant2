# cli-interface Specification

## Purpose
TBD - created by archiving change add-core-infrastructure-specs. Update Purpose after archive.
## Requirements
### Requirement: CLI Argument Parsing
The system SHALL provide a command-line interface that accepts configuration via arguments and config files.

#### Scenario: Parse config file path
- **WHEN** user provides `--config path/to/config.yaml`
- **THEN** system loads configuration from the specified YAML file

#### Scenario: Parse strategy selection
- **WHEN** user provides `--strategy StrategyName`
- **THEN** system uses the specified strategy for backtesting

#### Scenario: Parse date range
- **WHEN** user provides `--start-date 2024-01-01 --end-date 2024-12-31`
- **THEN** system uses the specified date range for data fetching and backtesting

#### Scenario: Parse tickers
- **WHEN** user provides `--tickers AAPL,MSFT,GOOG`
- **THEN** system parses comma-separated tickers and processes each

#### Scenario: Parse sizer percentage
- **WHEN** user provides `--sizer-percent 95`
- **THEN** system configures PercentSizerInt with the specified percentage

#### Scenario: Show help when no arguments
- **WHEN** user runs CLI with no arguments
- **THEN** system displays help message and exits

### Requirement: CLI Override Priority
The system SHALL prioritize CLI arguments over config file values when both are provided.

#### Scenario: CLI overrides config file
- **WHEN** config file contains `strategy: StrategyA` AND user provides `--strategy StrategyB`
- **THEN** system uses `StrategyB` for backtesting

#### Scenario: Config file provides defaults
- **WHEN** config file contains `tickers: AAPL` AND user does not provide `--tickers`
- **THEN** system uses `AAPL` from config file

### Requirement: Dynamic Parameter Parsing
The system SHALL accept dynamic parameters using dot-notation format `--key=value`.

#### Scenario: Parse indicator parameters
- **WHEN** user provides `--indicator.sma.period=20`
- **THEN** system applies the parameter override to indicator configuration

#### Scenario: Multiple dynamic parameters
- **WHEN** user provides `--indicator.sma.period=20 --strategy_param.threshold=0.05`
- **THEN** system collects all dynamic parameters and applies them to configuration

### Requirement: Required Field Validation
The system SHALL validate that required fields are present before execution.

#### Scenario: Missing required fields
- **WHEN** configuration is missing any of: strategy, start_date, end_date, tickers
- **THEN** system reports the missing fields and exits with error

#### Scenario: All required fields present
- **WHEN** configuration contains all required fields
- **THEN** system proceeds with backtest execution

### Requirement: Analysis and Output Options
The system SHALL support optional analysis and output configuration.

#### Scenario: Enable analysis
- **WHEN** user provides `--analysis`
- **THEN** system runs analyzers and includes metrics in results

#### Scenario: Enable plotting
- **WHEN** user provides `--plot`
- **THEN** system generates charts after backtest completion

#### Scenario: Enable JSON output
- **WHEN** user provides `--json-output`
- **THEN** system saves results to JSON file in output directory

#### Scenario: Set initial cash
- **WHEN** user provides `--initial-cash 50000`
- **THEN** system uses specified initial cash amount (default: 100000)

