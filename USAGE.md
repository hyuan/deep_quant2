# My Quant V2 - Usage Guide

## Quick Start

### Installation

```bash
cd /Users/anthonyyuan/Projects/investment/my_quant_v2
pip install -e .
```

### Running a Backtest

#### Using a configuration file:

```bash
python -m cli.main --config conf/example_strategy.yaml
```

#### Using command-line arguments:

```bash
python -m cli.main \
  --strategy ExampleStrategy \
  --start-date 2023-01-01 \
  --end-date 2024-12-01 \
  --tickers AAPL \
  --analysis
```

#### With dynamic parameter overrides:

```bash
python -m cli.main \
  --config conf/example_strategy.yaml \
  --ind_sma_period=20 \
  --analysis
```

### Running an Optimization

```bash
python -m cli.main --config conf/volume_spike_tsla_apt.yaml
```

## Examples

### 1. Simple SMA Crossover Strategy

```bash
python -m cli.main \
  --strategy ExampleStrategy \
  --start-date 2023-01-01 \
  --end-date 2024-01-01 \
  --tickers AAPL \
  --sizer-percent 90 \
  --analysis \
  --json-output
```

### 2. Volume Spike Strategy on MSFT

```bash
python -m cli.main --config conf/volume_spike_msft.yaml
```

### 3. Optimize Volume Spike Threshold

```bash
python -m cli.main --config conf/volume_spike_tsla_apt.yaml
```

### 4. Multiple Tickers

```bash
python -m cli.main \
  --strategy ExampleStrategy \
  --start-date 2023-01-01 \
  --end-date 2024-01-01 \
  --tickers AAPL,MSFT,GOOGL \
  --analysis
```

## CLI Options

```
--config PATH              Path to YAML configuration file
--strategy NAME            Strategy name to run
--start-date YYYY-MM-DD    Start date for backtest
--end-date YYYY-MM-DD      End date for backtest
--tickers SYMBOLS          Comma-separated ticker symbols
--sizer-percent INT        Percentage of cash per trade (default: 95)
--optimize PARAMS          Comma-separated parameters to optimize
--analysis                 Enable analysis with Sharpe, Drawdown, SQN
--plot                     Generate charts
--json-output              Save results to JSON
--initial-cash FLOAT       Initial capital (default: 100000.0)
--PARAM=VALUE              Override any strategy parameter
```

## Configuration Structure

### Strategy Definition (strategies/*.yaml)

```yaml
name: MyStrategy

indicators:
  sma:
    type: SMA
    period: sma_period

triggers:
  - name: BuySignal
    condition: indicators.sma > close
    actions:
      - name: buy
        type: TradeAction
        ticker: tickers[0]
        signal: Long
        orderType: Market

parameters:
  sma_period: 20
```

### Runtime Config (conf/*.yaml)

```yaml
strategy: MyStrategy
start_date: "2023-01-01"
end_date: "2024-01-01"
tickers: AAPL

strategy_parameters:
  sma_period: 30

sizer:
  PercentSizerInt:
    percents: 95

analysis: true
initial_cash: 100000.0
```

## Output

### Console Output

```
=== My Quant V2 Backtest System ===
INFO - Loading strategy: VolumeSpikeBasedStrategy
INFO - Tickers: MSFT
INFO - Fetching market data...
INFO - Running backtest...
INFO - Starting Portfolio Value: 100000.00
INFO - BUY EXECUTED - Price: 234.50, Cost: 95000.00
INFO - TRADE PROFIT - Gross: 5432.10, Net: 5337.10
INFO - Ending Portfolio Value: 146547.16

============================================================
BACKTEST RESULTS
============================================================
Initial Value: $100,000.00
Final Value:   $146,547.16
Profit:        $46,547.16
Return:        46.55%
============================================================

===== TRADE ANALYSIS =====
Total Trades: 2 (Open: 0, Closed: 2)
Won Trades: 2 (100.00%)
Sharpe Ratio: 0.68
Max Drawdown: 29.18%
```

### JSON Output (output/json/)

```json
{
  "strategy": "VolumeSpikeBasedStrategy",
  "ticker": "MSFT",
  "start_date": "2019-12-01",
  "end_date": "2024-12-01",
  "initial_cash": 100000,
  "final_value": 146547.16,
  "return_pct": 46.55,
  "sharpe_ratio": 0.68,
  "max_drawdown": 29.18,
  "sqn": 0.67,
  "trades": 2
}
```

## Creating Custom Strategies

### 1. Define Strategy YAML (strategies/MyCustomStrategy.yaml)

```yaml
name: MyCustomStrategy

indicators:
  rsi:
    type: RSI
    period: 14
  
  sma_fast:
    type: SMA
    period: 10
  
  sma_slow:
    type: SMA
    period: 30

triggers:
  - name: BuySignal
    condition: indicators.rsi < 30 and indicators.sma_fast > indicators.sma_slow
    actions:
      - name: enter_long
        type: TradeAction
        ticker: tickers[0]
        signal: Long
        orderType: Market
      
      - name: set_stop_loss
        type: TradeAction
        ticker: tickers[0]
        signal: Short
        orderType: StopTrail
        price: close
        trailpercent: 0.05

parameters:
  # Parameters can be overridden via CLI or config
```

### 2. Create Runtime Config (conf/my_custom.yaml)

```yaml
strategy: MyCustomStrategy
start_date: "2023-01-01"
end_date: "2024-01-01"
tickers: AAPL
analysis: true
```

### 3. Run It

```bash
python -m cli.main --config conf/my_custom.yaml
```

## Order Types

- **Market**: Execute at next available price
- **Limit**: Execute at specified price or better
  - Parameters: `price`
- **StopLimit**: Stop order with limit price
  - Parameters: `price`, `plimit`
- **StopTrail**: Trailing stop order
  - Parameters: `price`, `trailpercent` or `trailamount`
- **StopTrailLimit**: Trailing stop with limit
  - Parameters: `price`, `trailpercent`, `plimit`

## Expression Language

### Variables
- `open`, `high`, `low`, `close`, `volume` - Current bar OHLCV
- `indicators.NAME` - Indicator values
- `tickers[0]` - Data feed reference

### Operators
- Comparison: `>`, `<`, `>=`, `<=`, `==`, `!=`
- Logical: `and`, `or`
- Math: `+`, `-`, `*`, `/`

### Examples
```
indicators.sma > close
close > indicators.sma * 1.05
(high - low) / close > 0.02
indicators.rsi < 30 and volume > 1000000
```

## Troubleshooting

### No data fetched
- Check ticker symbol is correct
- Verify date range is valid
- Ensure internet connection for Yahoo Finance

### Strategy not found
- Check strategy name matches YAML filename
- Verify strategies/ folder contains the definition

### Import errors
- Ensure dependencies installed: `pip install -e .`
- Check Python version >= 3.10

### Order not executing
- Check cash available
- Verify position status (not already in position)
- Review order type parameters

## Development

### Project Structure
```
my_quant_v2/
├── cli/              # Command-line interface
├── core/             # Backtest engine
├── strategy/         # Strategy framework
│   ├── expression/   # Expression evaluator
│   ├── base.py       # Base strategy class
│   ├── factory.py    # YAML-to-class factory
│   └── trigger_system.py
├── indicator/        # Technical indicators
├── utils/            # Utilities
├── strategies/       # Strategy definitions
└── conf/             # Runtime configurations
```

### Running Tests
```bash
pytest tests/
```

### Adding Custom Indicators

Create in `indicator/my_indicator.py`:
```python
import backtrader as bt

class MyIndicator(bt.Indicator):
    lines = ('signal',)
    params = (('period', 14),)
    
    def __init__(self):
        self.addminperiod(self.p.period)
    
    def next(self):
        # Implement indicator logic
        self.l.signal[0] = ...
```

Register in `indicator/__init__.py`:
```python
from .my_indicator import MyIndicator

__all__ = [..., 'MyIndicator']
```

Use in strategy YAML:
```yaml
indicators:
  my_ind:
    type: MyIndicator
    period: 20
```
