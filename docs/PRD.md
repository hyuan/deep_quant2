# Product Requirements Document: Quant Backtest Application v2

## Overview

A YAML-driven quantitative trading backtest framework built on Backtrader. Users define trading strategies via configuration files, run backtests with customizable parameters, and analyze results with optimization support.

---

## Architecture

```
┌──────────────────────────────────────────────────────────────────────┐
│                            CLI Layer                                  │
│  cli/main.py (v2)  │  cli/main_v1.py (v1)  │  cli/generate_strategy  │
└────────────────┬─────────────────────────────────────────────────────┘
                 │
                 ▼
┌──────────────────────────────────────────────────────────────────────┐
│                         Core Backtest Engine                          │
│                        core/backtest.py                               │
│    (Cerebro orchestration, analyzers, data feeds, sizer setup)        │
└────────────────┬─────────────────────────────────────────────────────┘
                 │
                 ▼
┌──────────────────────────────────────────────────────────────────────┐
│                      Strategy Framework (v2)                          │
│  ┌────────────────┐    ┌────────────────┐    ┌──────────────────┐   │
│  │  BaseStrategy  │    │ TriggerSystem  │    │ Strategy Factory │   │
│  │  (strategy/    │◄───│ (Condition +   │    │ (Dynamic class   │   │
│  │   base.py)     │    │  Actions)      │    │  generation)     │   │
│  └────────────────┘    └────────────────┘    └──────────────────┘   │
│          ▲                      │                      │             │
│          │                      ▼                      │             │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │                  Expression Evaluator System                    │  │
│  │  ConditionEvaluator │ ExpressionEvaluator │ ExpressionTokenizer │  │
│  └───────────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────────┘
                 │
                 ▼
┌──────────────────────────────────────────────────────────────────────┐
│                      Technical Indicators                             │
│   indicator/volume_spike.py │ zig_zag.py │ fractals.py │ etc.        │
└──────────────────────────────────────────────────────────────────────┘
                 │
                 ▼
┌──────────────────────────────────────────────────────────────────────┐
│                         Utilities Layer                               │
│  yf_utils (Yahoo Finance) │ config │ parameters │ analysis_utils     │
└──────────────────────────────────────────────────────────────────────┘
```

---

## CLI Interface

### Entry Point
```bash
python -m cli.main [options]
```

### Arguments

| Argument | Type | Description |
|----------|------|-------------|
| `--config` | string | Path to YAML configuration file |
| `--strategy` | string | Strategy name (e.g., `VolumeSpikeBasedStrategy`) |
| `--start-date` | string | Start date `YYYY-MM-DD` |
| `--end-date` | string | End date `YYYY-MM-DD` |
| `--tickers` | string | Comma-separated ticker symbols |
| `--sizer-percent` | int | Percentage of cash per trade (default: 95) |
| `--optimize` | string | Comma-separated parameters to optimize |
| `--analysis` | bool | Enable result analysis |
| `--indicator.*` | dynamic | Override indicator parameters via dot notation |

### Priority
CLI arguments override config file values.

---

## Configuration Schema

### Runtime Config (conf/*.yaml)

```yaml
# Strategy Selection
strategy: VolumeSpikeBasedStrategy

# Date Range
start_date: "2024-05-01"
end_date: "2025-05-01"

# Tickers
tickers: TSLA

# Position Sizing
sizer:
  PercentSizerInt:
    percents: 95

# Strategy Parameters
strategy_parameters:
  vs_macd_fast_period: 12
  vs_macd_slow_period: 26
  vs_macd_signal_period: 9

# Output Options
plot:
  enabled: True
analysis: True

# Optimization (optional)
optimizing_params:
  - stop_loss_percent
```

### Strategy Definition (strategies/*.yaml)

```yaml
name: ExampleStrategy

indicators:
  sma:
    type: SMA
    period: ind_sma_period

triggers:
  - name: CrossoverTrigger
    condition: indicators.sma > close
    actions:
      - name: main
        type: TradeAction
        ticker: tickers[0]
        signal: Long
        orderType: Limit
        price: close * 1.02
        valid: 7
      - name: stop_loss
        type: TradeAction
        ticker: tickers[0]
        signal: Short
        orderType: StopTrailLimit
        price: close
        trailpercent: 0.02
        plimit: close * 0.8

sizer:
  PercentSizerInt:
    percents: 95

plot:
  enabled: false

parameters:
  ind_sma_period: 5
```

### Supported Sizers
- `PercentSizerInt` - Percentage of portfolio (params: `percents`)
- `AllInSizerInt` - Use all available cash
- `FixedSize` - Fixed position size

---

## Strategy Interface

### BaseStrategy Contract

```python
class BaseStrategy(bt.Strategy):
    # Abstract methods to implement
    def setup_indicators(self) -> None:
        """Set up technical indicators. Store in self.indicators dict."""
        pass
    
    def setup_trigger_system(self) -> None:
        """Configure triggers with conditions and actions."""
        pass
```

### Key Properties

| Property | Type | Description |
|----------|------|-------------|
| `indicators` | `Dict` | Dictionary of indicator instances |
| `trigger_system` | `TriggerSystem` | Manages all triggers |
| `condition_evaluator` | `ConditionEvaluator` | Evaluates condition strings |
| `expression_evaluator` | `ExpressionEvaluator` | Evaluates math expressions |
| `orders` | `Dict` | Tracks orders by trigger/action |
| `pending_actions` | `List` | Actions waiting to execute |
| `active_triggers` | `Set` | Currently active trigger names |

### Lifecycle

1. `__init__` → Sets up indicators, trigger system
2. `next` → Called each bar; evaluates trigger conditions
3. `notify_order` → Handles order completion/failure
4. `notify_trade` → Handles trade completion
5. `stop` → Final cleanup, logs results

---

## Trigger System

### TriggerAction

```python
@dataclass
class TriggerAction:
    name: str                           # Unique action name
    type: str                           # "TradeAction"
    parameters: Dict[str, Any]          # Action parameters
```

### Action Parameters

| Parameter | Values | Description |
|-----------|--------|-------------|
| `ticker` | `tickers[0]`, symbol | Target ticker |
| `signal` | `Long`, `Short` | Trade direction |
| `orderType` | `Market`, `Limit`, `StopLimit`, `StopTrail`, `StopTrailLimit` | Order type |
| `price` | expression | Order price (e.g., `close * 1.02`) |
| `valid` | int | Order validity in days |
| `trailpercent` | float | Trail percentage for stop orders |
| `trailamount` | float | Trail amount for stop orders |
| `plimit` | expression | Limit price for stop-limit orders |

### Trigger

```python
@dataclass
class Trigger:
    name: str                           # Unique trigger name
    condition: Callable | str           # Condition to evaluate
    actions: List[TriggerAction]        # Actions to execute
    enabled: bool = True                # Enable/disable flag
```

---

## Expression System

### Supported Operators

| Type | Operators |
|------|-----------|
| Comparison | `>`, `<`, `>=`, `<=`, `==`, `!=` |
| Logical | `and`, `or` |
| Math | `+`, `-`, `*`, `/` |

### Supported Variables

| Variable | Description |
|----------|-------------|
| `open`, `high`, `low`, `close`, `volume` | Current bar OHLCV |
| `indicators.*` | Indicator values (e.g., `indicators.sma`) |
| `tickers[0]`, etc. | Multi-ticker data access |

### Example Conditions
```
indicators.sma > close
indicators.vs == 1
close > 100 and volume > 1000000
(high - low) / close > 0.05
```

---

## Indicators

### Custom Indicators

| Indicator | File | Description |
|-----------|------|-------------|
| `VolumeSpike` | `indicator/volume_spike.py` | Detects volume spikes using MACD on volume |
| `ZigZag` | `indicator/zig_zag.py` | Identifies trend reversals |
| `LocalPeakTrough` | `indicator/local_peak_trough.py` | Finds local highs/lows |
| `LocalPeakTroughBreak` | `indicator/local_peak_trough_break.py` | Breakout detection |
| `Fractals` | `indicator/fractals.py` | Bill Williams fractals |

### VolumeSpike Parameters

```python
params = (
    ('macd_fast', 12),
    ('macd_slow', 26),
    ('macd_signal', 9),
    ('macd_hist_mean_period', 9),
    ('macd_hist_mean_threshold', 4000000.0),
)
```

---

## Data Flow

```
CLI Args → Config File → Merged Config
                              ↓
                        parse_args()
                              ↓
                    load_strategy_def()
                              ↓
              fetch_and_save_data() (yf_utils)
                              ↓
                       run_backtest()
            ┌─────────────────┴─────────────────┐
            ↓                                   ↓
    find_strategy_class()              create_strategy()
            └─────────────────┬─────────────────┘
                              ↓
                  Setup Cerebro + Analyzers
                              ↓
                        cerebro.run()
                              ↓
              ┌───────────────┼───────────────┐
              ↓               ↓               ↓
         Console Log      JSON Output      Plot
```

---

## Optimization

### Configuration

```yaml
optimizing_params:
  - stop_loss_percent

strategy_parameters:
  stop_loss_percent:
    - 0.05
    - 0.10
    - 0.15
    - 0.20
    - 0.25
```

### Execution

Uses `cerebro.optstrategy()` instead of `cerebro.addstrategy()`.

---

## Output Formats

### Console Logging

```
2025-05-17 11:03:14 - INFO - Starting Portfolio Value: 100000.00
2025-05-17 11:03:14 - INFO - BUY EXECUTED, Price: 234.50, Cost: 95000.00
2025-05-17 11:03:14 - INFO - TRADE PROFIT, GROSS: 5432.10, NET: 5337.10
2025-05-17 11:03:14 - INFO - Ending Portfolio Value: 146547.16
```

### Analysis Output

- Sharpe Ratio
- Max Drawdown
- SQN (System Quality Number)
- Trade Analysis (win/loss stats, streaks, PnL breakdown)

### JSON Output

```json
{
  "strategy": "VolumeSpikeBasedStrategy",
  "ticker": "MSFT",
  "start_date": "2019-12-01",
  "end_date": "2024-12-01",
  "initial_cash": 100000,
  "final_value": 246547.16,
  "return_pct": 146.55,
  "sharpe_ratio": 0.68,
  "max_drawdown": 29.18,
  "sqn": 0.67,
  "trades": 2
}
```

---

## Dependencies

- `backtrader~=1.9.78.123` - Core backtesting engine
- `yfinance~=0.2.49` - Yahoo Finance data fetching
- `pyyaml>=6.0.2` - YAML parsing
- `jinja2~=3.1.4` - Template engine for code generation
- `matplotlib~=3.9.2` - Plotting
- `numpy==2.1.3` - Numerical operations
- `python-dateutil~=2.9.0` - Date parsing

---

## File Structure

```
my_quant/
├── cli/
│   ├── main.py                   # v2 entry point
│   ├── main_v1.py                # v1 entry point
│   ├── generate_strategy.py      # Strategy code generator
│   ├── strategy_generator.py     # Generator implementation
│   └── optimizing_settings.py    # Optimization dataclass
├── core/
│   └── backtest.py               # Backtest orchestration
├── strategy/
│   ├── base.py                   # BaseStrategy class
│   ├── factory.py                # Dynamic strategy creation
│   ├── trigger_system.py         # Trigger/Action system
│   └── expression/               # Expression parsing
├── strategy_v2/                  # v2 strategy implementations
├── indicator/                    # Custom indicators
├── utils/
│   ├── config.py                 # Config loading
│   ├── parameters.py             # Parameter mapping
│   ├── yf_utils.py               # Yahoo Finance
│   ├── bt_utils.py               # Backtrader utilities
│   └── analysis_utils.py         # Analysis formatting
├── strategies/                   # Strategy YAML definitions
├── conf/                         # Runtime configurations
├── templates/                    # Jinja2 templates
├── datas/                        # Data files
└── output/                       # Output files
```

---

## Rebuild Implementation Plan

### Phase 1: Core Infrastructure

1. **CLI Argument Parser**
   - Implement argparse with all required arguments
   - Support dynamic `--indicator.*` parameter parsing
   - Priority: CLI args override config file

2. **Configuration Loader**
   - YAML parsing for runtime config
   - Schema validation
   - Config merging logic

3. **Data Layer**
   - Yahoo Finance data fetching
   - CSV storage and caching
   - Date range handling

### Phase 2: Strategy Framework

4. **BaseStrategy Abstract Class**
   - Abstract `setup_indicators()` and `setup_trigger_system()`
   - Order lifecycle management (`notify_order`, `notify_trade`)
   - Trigger evaluation in `next()`
   - Order tracking dictionaries

5. **Expression System**
   - Tokenizer for parsing expressions
   - AST nodes (BinaryOp, Comparison, Logical, Variable, Number)
   - ConditionEvaluator for boolean conditions
   - ExpressionEvaluator for math expressions
   - Variable resolution (OHLCV, indicators, tickers)

6. **Trigger System**
   - `Trigger` dataclass with name, condition, actions
   - `TriggerAction` dataclass with parameters
   - `TriggerSystem` for managing triggers
   - Support all order types (Market, Limit, StopLimit, StopTrail, StopTrailLimit)

### Phase 3: Backtest Engine

7. **Backtest Orchestrator**
   - Cerebro configuration
   - Strategy class resolution/creation
   - Sizer setup (PercentSizerInt, AllInSizerInt, FixedSize)
   - Data feed management
   - Analyzer attachment

8. **Strategy Factory**
   - Dynamic strategy class generation from YAML
   - Indicator factory functions
   - Trigger system setup from config

9. **Optimization Support**
   - `optstrategy()` vs `addstrategy()` branching
   - Parameter grid generation
   - Results aggregation

### Phase 4: Output & Analysis

10. **Output Formatters**
    - Console logging
    - JSON export
    - Plot generation

11. **Analyzers**
    - Sharpe Ratio
    - Max Drawdown
    - SQN
    - Trade statistics

---

## Open Questions

1. **Strategy resolution priority**: Should factory-created strategies override Python classes, or vice versa? Current: Python classes in `strategy_v2/` take precedence.

2. **Expression language expansion**: Should we support functions like `max()`, `min()`, `abs()` in conditions, or keep it simple with operators only?

3. **Multi-ticker support**: How to enhance data access patterns for multi-ticker correlation strategies beyond `tickers[0]` syntax?

4. **Error handling**: How should the system handle missing indicators, invalid conditions, or failed orders?

5. **Indicator parameters**: Should indicator parameters be validated against their schemas before strategy instantiation?

6. **Configuration validation**: Should we implement strict schema validation or allow flexible YAML structures?
