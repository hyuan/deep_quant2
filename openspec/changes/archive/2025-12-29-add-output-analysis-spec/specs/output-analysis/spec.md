## ADDED Requirements

### Requirement: Console Logging Format
The system SHALL provide consistent console logging for backtest events using Python's logging module.

#### Scenario: Log portfolio values
- **WHEN** backtest starts or completes
- **THEN** system logs portfolio value with format `Starting Portfolio Value: {value:.2f}` or `Ending Portfolio Value: {value:.2f}`

#### Scenario: Log order execution
- **WHEN** an order is executed
- **THEN** system logs with format including order type (BUY/SELL), execution price, and cost

#### Scenario: Log trade profit
- **WHEN** a trade closes
- **THEN** system logs with format `TRADE PROFIT - Gross: {pnl:.2f}, Net: {pnlcomm:.2f}`

#### Scenario: Log trigger activation
- **WHEN** a trigger condition is met
- **THEN** system logs with format `Trigger activated: {trigger_name}`

#### Scenario: Log strategy initialization
- **WHEN** strategy is initialized
- **THEN** system logs with format `Initialized {strategy_class_name}`

### Requirement: Trade Analysis Formatting
The system SHALL format trade analysis results in a human-readable structure.

#### Scenario: Format overall statistics
- **WHEN** `format_trade_analysis()` is called with trade analyzer results
- **THEN** system returns formatted string with total trades count (total, open, closed)

#### Scenario: Format win/loss statistics
- **WHEN** trade analysis results include won/lost data
- **THEN** formatted output includes won trades count, lost trades count, and win rate percentage

#### Scenario: Format win/loss streaks
- **WHEN** trade analysis results include streak data
- **THEN** formatted output includes current and longest winning/losing streaks

#### Scenario: Format profit/loss information
- **WHEN** trade analysis results include PnL data
- **THEN** formatted output includes gross profit, net profit, and average profit per trade

#### Scenario: Format long/short breakdown
- **WHEN** trade analysis results include long/short data
- **THEN** formatted output includes trade counts and win/loss breakdown by direction

#### Scenario: Format trade duration
- **WHEN** trade analysis results include duration data
- **THEN** formatted output includes average, max, and min trade length in bars

### Requirement: Analyzer Results Formatting
The system SHALL format all analyzer results into a consolidated report.

#### Scenario: Format Sharpe Ratio
- **WHEN** analyzers include Sharpe ratio data
- **THEN** formatted output includes `Sharpe Ratio: {value:.4f}` or `N/A` if unavailable

#### Scenario: Format Max Drawdown
- **WHEN** analyzers include drawdown data
- **THEN** formatted output includes max drawdown percentage and drawdown period in bars

#### Scenario: Format SQN
- **WHEN** analyzers include SQN (System Quality Number) data
- **THEN** formatted output includes `SQN: {value:.4f}` or `N/A` if unavailable

#### Scenario: Include trade analysis in report
- **WHEN** analyzers include trade analysis data
- **THEN** formatted report includes full trade analysis section

### Requirement: JSON Output Schema
The system SHALL produce JSON output conforming to a defined schema.

#### Scenario: Include core backtest metadata
- **WHEN** JSON output is generated
- **THEN** output includes `strategy`, `ticker`, `start_date`, `end_date` fields

#### Scenario: Include portfolio performance
- **WHEN** JSON output is generated
- **THEN** output includes `initial_cash`, `final_value`, `return_pct` fields

#### Scenario: Include analyzer metrics
- **WHEN** analysis is enabled and JSON output is generated
- **THEN** output includes `sharpe_ratio`, `max_drawdown`, `sqn`, `trades` fields

#### Scenario: Generate output filename
- **WHEN** saving JSON output
- **THEN** filename follows pattern `{strategy}_{ticker}_results.json` in `output/json/` directory

### Requirement: Logging Configuration
The system SHALL use appropriate logging levels for different event types.

#### Scenario: Use INFO for normal events
- **WHEN** logging portfolio values, order execution, trade completion
- **THEN** system uses INFO level logging

#### Scenario: Use ERROR for failures
- **WHEN** logging strategy errors or failed operations
- **THEN** system uses ERROR level logging

#### Scenario: Use WARNING for non-critical issues
- **WHEN** logging recoverable issues or edge cases
- **THEN** system uses WARNING level logging
