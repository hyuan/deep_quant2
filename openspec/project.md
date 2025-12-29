# Project Context

## Purpose

My Quant V2 is a YAML-driven quantitative trading backtest framework built on Backtrader. The project enables users to:

- Define trading strategies via YAML configuration files (no Python coding required)
- Run backtests with customizable parameters against historical market data
- Optimize strategy parameters to find best-performing configurations
- Analyze results with comprehensive metrics (Sharpe Ratio, Max Drawdown, SQN)
- Expose capabilities via MCP (Model Context Protocol) for AI assistant integration

## Tech Stack

### Core Technologies
- **Python 3.10+** - Primary language
- **Backtrader ~1.9.78** - Core backtesting engine
- **PyYAML >=6.0.2** - YAML configuration parsing
- **yfinance ~0.2.49** - Yahoo Finance market data fetching
- **Pydantic >=2.0.0** - Data validation and settings management
- **MCP >=1.0.0** - Model Context Protocol server for AI integration

### Development Tools
- **uv** - Package manager and virtual environment
- **pytest >=7.0.0** - Testing framework
- **pytest-cov >=4.0.0** - Coverage reporting
- **black >=23.0.0** - Code formatter (line-length: 100)
- **ruff >=0.1.0** - Linter (line-length: 100, target: py310)

### Supporting Libraries
- **Jinja2 ~3.1.4** - Template engine for code generation
- **matplotlib ~3.9.2** - Chart plotting
- **numpy 2.1.3** - Numerical operations
- **python-dateutil ~2.9.0** - Date parsing

## Project Conventions

### Code Style

- **Formatter**: Black with 100-character line length
- **Linter**: Ruff with Python 3.10 target
- **Docstrings**: Triple-quoted strings at module, class, and function level
- **Type Hints**: Use typing annotations for all function signatures
- **Naming**:
  - Classes: `PascalCase` (e.g., `BaseStrategy`, `TriggerSystem`)
  - Functions/Methods: `snake_case` (e.g., `setup_indicators`, `run_backtest`)
  - Constants: `UPPER_SNAKE_CASE`
  - Private members: Prefix with underscore (e.g., `_internal_method`)
- **Imports**: Group stdlib, third-party, then local imports with blank lines between

### Architecture Patterns

```
CLI Layer → Core Backtest Engine → Strategy Framework → Indicators → Utilities
```

- **YAML-First Configuration**: Strategy definitions and runtime configs are YAML files
- **Factory Pattern**: `strategy/factory.py` dynamically creates strategy classes from YAML
- **Expression Evaluation System**: Custom tokenizer/parser/evaluator for condition strings
- **Trigger-Action Pattern**: Strategies use triggers (conditions) that fire actions (trades)
- **Abstract Base Classes**: `BaseStrategy` defines the contract for all strategies

### Key Directories

| Directory | Purpose |
|-----------|---------|
| `cli/` | Command-line interface entry points |
| `core/` | Backtest orchestration (Cerebro setup, analyzers) |
| `strategy/` | BaseStrategy, TriggerSystem, expression evaluators |
| `indicator/` | Custom Backtrader indicators (VolumeSpike, ZigZag, etc.) |
| `utils/` | Config loading, Yahoo Finance, analysis formatting |
| `strategies/` | Strategy YAML definitions |
| `conf/` | Runtime configuration YAML files |
| `mcp_server/` | MCP server for AI assistant integration |
| `tests/` | Unit tests |

### Testing Strategy

- **Framework**: pytest with pytest-cov for coverage
- **Test Location**: All tests in `tests/` directory
- **Test Naming**: `test_*.py` files with `test_*` functions
- **Coverage Target**: Run with `pytest tests/ --cov=. --cov-report=term-missing`
- **Test Categories**:
  - Expression evaluators (condition parsing, math expressions)
  - Configuration loading and validation
  - Strategy factory (dynamic class generation)
  - Trigger system logic
  - Parameter mapping

### Git Workflow

- **Branch Naming**: Use descriptive names with prefixes (`feature/`, `fix/`, `refactor/`)
- **Commits**: Write clear, concise commit messages describing the change
- **OpenSpec Integration**: Use OpenSpec for spec-driven development on significant changes

## Domain Context

### Trading Concepts

- **Strategy**: A set of rules defining when to buy/sell securities
- **Backtest**: Simulating strategy performance against historical data
- **Trigger**: A condition that, when true, fires one or more actions
- **Action**: A trade operation (buy/sell) with specific order parameters
- **Sizer**: Determines position size (PercentSizerInt, AllInSizerInt, FixedSize)

### Order Types

| Type | Description |
|------|-------------|
| `Market` | Execute immediately at current price |
| `Limit` | Execute only at specified price or better |
| `StopLimit` | Limit order activated when stop price reached |
| `StopTrail` | Trailing stop that follows price movement |
| `StopTrailLimit` | Trailing stop with limit price |

### Expression Language

Strategies use a simple expression language for conditions:
- **Comparison**: `>`, `<`, `>=`, `<=`, `==`, `!=`
- **Logical**: `and`, `or`
- **Math**: `+`, `-`, `*`, `/`
- **Variables**: `open`, `high`, `low`, `close`, `volume`, `indicators.*`, `tickers[0]`

### Custom Indicators

| Indicator | Purpose |
|-----------|---------|
| `VolumeSpike` | Detects volume spikes using MACD on volume |
| `ZigZag` | Identifies trend reversals |
| `LocalPeakTrough` | Finds local highs/lows |
| `Fractals` | Bill Williams fractals pattern |

## Important Constraints

- **Python Version**: Requires Python 3.10 or later
- **Rate Limiting**: Yahoo Finance fetching is rate-limited (1 req/sec) to avoid throttling
- **Data Caching**: Market data is cached locally in `datas/` folder
- **Single-Threaded Backtest**: Backtrader runs backtests in a single thread
- **MCP Jobs**: Backtest jobs run asynchronously, max 100 jobs retained in memory

## External Dependencies

### Yahoo Finance (yfinance)
- **Purpose**: Fetch historical OHLCV market data
- **Rate Limit**: 1 request per second enforced by framework
- **Caching**: Data cached in `datas/` as CSV files

### Backtrader
- **Purpose**: Core backtesting engine
- **Version**: ~1.9.78.123 (pinned for stability)
- **Documentation**: https://www.backtrader.com/docu/

### MCP (Model Context Protocol)
- **Purpose**: Expose tools/resources to AI assistants (Claude, etc.)
- **Entry Point**: `my-quant-v2-mcp` command or `mcp_server/server.py`
