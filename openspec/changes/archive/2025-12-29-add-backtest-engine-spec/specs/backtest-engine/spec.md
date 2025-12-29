# backtest-engine Specification

## Purpose
The backtest engine orchestrates the entire backtesting process using Backtrader's Cerebro. It handles strategy resolution, data feed management, position sizing, analyzer setup, optimization, and result processing.

## ADDED Requirements

### Requirement: Backtest Orchestration
The system SHALL orchestrate backtests using Backtrader's Cerebro engine.

#### Scenario: Run standard backtest
- **WHEN** `run_backtest()` is called with valid strategy, data files, and config
- **THEN** system creates Cerebro instance with `maxcpus=1`
- **AND** resolves strategy class
- **AND** adds data feeds, sizer, and analyzers
- **AND** executes backtest via `cerebro.run()`
- **AND** returns result dictionary

#### Scenario: Set initial cash
- **WHEN** `initial_cash` parameter is provided
- **THEN** system sets broker cash via `cerebro.broker.setcash()`
- **AND** logs starting portfolio value

#### Scenario: Log portfolio values
- **WHEN** backtest starts and completes
- **THEN** system logs initial and final portfolio values

### Requirement: Strategy Resolution
The system SHALL resolve strategy classes from names or YAML definitions.

#### Scenario: Find pre-implemented strategy
- **WHEN** strategy name matches a class in `strategy_v2/` or `strategy/`
- **THEN** system returns that strategy class
- **AND** logs strategy class being used

#### Scenario: Create strategy from YAML
- **WHEN** strategy name not found and strategy definition provided
- **THEN** system creates strategy class using `strategy.factory.create_strategy()`
- **AND** logs that strategy is being created from YAML

#### Scenario: Strategy not found
- **WHEN** strategy name not found and no definition provided
- **THEN** system raises `ValueError` with descriptive message

### Requirement: Data Feed Management
The system SHALL add CSV data feeds to Cerebro for backtesting.

#### Scenario: Add single data feed
- **WHEN** single CSV file path provided in `data_files` list
- **THEN** system creates `YahooFinanceCSVData` feed from file
- **AND** adds feed to Cerebro via `cerebro.adddata()`

#### Scenario: Add multiple data feeds
- **WHEN** multiple CSV file paths provided
- **THEN** system creates and adds each data feed sequentially

### Requirement: Position Sizer Configuration
The system SHALL configure position sizing based on config.

#### Scenario: Configure sizer from config
- **WHEN** config contains `sizer` section
- **THEN** system parses sizer type and parameters via `setup_sizer()`
- **AND** adds sizer to strategy via `cerebro.addsizer_byidx()`

#### Scenario: Use default sizer
- **WHEN** sizer config missing or invalid
- **THEN** system uses `PercentSizerInt` with 95% as default

### Requirement: Analyzer Setup
The system SHALL add performance analyzers when analysis is enabled.

#### Scenario: Enable analysis
- **WHEN** `analysis=True` parameter passed to `run_backtest()`
- **THEN** system adds SharpeRatio, DrawDown, SQN, TradeAnalyzer, Transactions analyzers
- **AND** adds ResultCollector for optimization results

#### Scenario: Skip analyzers
- **WHEN** `analysis=False`
- **THEN** system does not add analyzers

### Requirement: Optimization Mode
The system SHALL support parameter optimization via Cerebro's optstrategy.

#### Scenario: Enable optimization
- **WHEN** config contains non-empty `optimizing_params` list
- **THEN** system uses `cerebro.optstrategy()` instead of `cerebro.addstrategy()`
- **AND** passes parameter list for grid search
- **AND** logs "Starting optimization mode"

#### Scenario: Validate optimization parameter
- **WHEN** optimization parameter value is not a list
- **THEN** system raises `ValueError` indicating parameter must be list of values

#### Scenario: Find best optimization result
- **WHEN** optimization completes
- **THEN** system finds result with highest portfolio value
- **AND** logs best parameter value and portfolio value

### Requirement: Result Processing
The system SHALL process backtest results into a structured dictionary.

#### Scenario: Build basic result dict
- **WHEN** backtest completes
- **THEN** system returns dict with `results`, `initial_value`, `final_value`, `profit`, `profit_percent`

#### Scenario: Include analyzer results
- **WHEN** analysis enabled and not optimizing
- **THEN** result dict includes `analyzers` with sharpe, drawdown, sqn, trades data
- **AND** logs formatted analyzer results

#### Scenario: Include optimization results
- **WHEN** optimization mode and results available
- **THEN** result dict includes `optimization_results` list and `best_optimization`

### Requirement: JSON Output
The system SHALL optionally save results to JSON file.

#### Scenario: Save JSON output
- **WHEN** `json_output=True` and not optimizing
- **THEN** system creates `output/json/` directory if needed
- **AND** saves results to `{strategy}_{ticker}_results.json`
- **AND** includes strategy, ticker, dates, cash, return, analyzers

#### Scenario: Handle JSON save error
- **WHEN** JSON save fails
- **THEN** system logs error but does not raise exception

### Requirement: Plot Generation
The system SHALL optionally generate charts.

#### Scenario: Enable plotting
- **WHEN** `plot=True` and not optimizing
- **THEN** system calls `cerebro.plot()` after backtest completes

#### Scenario: Skip plot in optimization
- **WHEN** `plot=True` but optimization mode active
- **THEN** system skips plotting

### Requirement: ResultCollector Analyzer
The system SHALL collect optimization results via custom analyzer.

#### Scenario: Collect optimization data
- **WHEN** ResultCollector.stop() is called
- **THEN** analyzer captures `optimizing_param`, parameter value, and final portfolio value

#### Scenario: Return collected analysis
- **WHEN** `get_analysis()` is called
- **THEN** analyzer returns dict with `optresult` key containing collected data
