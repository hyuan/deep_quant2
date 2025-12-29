"""
MCP Server for My Quant V2 - YAML-driven quantitative trading backtest framework.

This server exposes tools for:
- Strategy management (list, get, save, validate)
- Backtest execution (async with job tracking)
- Market data fetching (rate-limited)
- Indicator discovery

Usage:
    my-quant-v2-mcp  # Run as MCP server (stdio transport)
"""

import inspect
import logging
import os
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml
from mcp.server.fastmcp import FastMCP

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastMCP server
mcp = FastMCP(
    "my-quant-v2",
    instructions="YAML-driven quantitative trading backtest framework. "
                 "Create trading strategies from ideas and validate them through backtesting."
)

# Rate limiter for Yahoo Finance
_last_yf_call = 0.0
_YF_RATE_LIMIT_SECONDS = 1.0  # Minimum seconds between Yahoo Finance calls


def _get_project_root() -> Path:
    """Get the project root directory."""
    return Path(__file__).parent.parent


def _rate_limit_yahoo():
    """Apply rate limiting for Yahoo Finance API calls."""
    global _last_yf_call
    now = time.time()
    elapsed = now - _last_yf_call
    if elapsed < _YF_RATE_LIMIT_SECONDS:
        time.sleep(_YF_RATE_LIMIT_SECONDS - elapsed)
    _last_yf_call = time.time()


# ============================================================================
# Strategy Management Tools
# ============================================================================

@mcp.tool()
def list_strategies() -> List[Dict[str, Any]]:
    """
    List all available strategy definitions.
    
    Returns a list of strategies found in the strategies/ folder,
    including basic info about each strategy.
    """
    strategies_dir = _get_project_root() / "strategies"
    strategies = []
    
    if not strategies_dir.exists():
        return strategies
    
    for file in strategies_dir.glob("*.yaml"):
        try:
            with open(file, 'r') as f:
                strategy_def = yaml.safe_load(f) or {}
            
            strategies.append({
                "name": strategy_def.get("name", file.stem),
                "file_path": str(file),
                "has_indicators": bool(strategy_def.get("indicators")),
                "indicator_count": len(strategy_def.get("indicators", {})),
                "trigger_count": len(strategy_def.get("triggers", [])),
                "parameter_count": len(strategy_def.get("parameters", {}))
            })
        except Exception as e:
            logger.warning(f"Failed to parse strategy {file}: {e}")
    
    return strategies


@mcp.tool()
def get_strategy(strategy_name: str) -> Dict[str, Any]:
    """
    Get a strategy definition by name.
    
    Args:
        strategy_name: Name of the strategy (without .yaml extension)
        
    Returns:
        Strategy definition including YAML content and parsed structure
    """
    from utils.config import load_strategy_def
    
    strategies_dir = _get_project_root() / "strategies"
    
    # Find the strategy file
    for ext in ['.yaml', '.yml']:
        strategy_file = strategies_dir / f"{strategy_name}{ext}"
        if strategy_file.exists():
            with open(strategy_file, 'r') as f:
                yaml_content = f.read()
            
            parsed = load_strategy_def(strategy_name)
            return {
                "name": strategy_name,
                "yaml_content": yaml_content,
                "parsed": parsed,
                "file_path": str(strategy_file)
            }
    
    return {"error": f"Strategy '{strategy_name}' not found"}


@mcp.tool()
def save_strategy(strategy_name: str, yaml_content: str) -> Dict[str, Any]:
    """
    Save a strategy definition to a YAML file.
    
    Args:
        strategy_name: Name for the strategy (will be saved as {name}.yaml)
        yaml_content: YAML content defining the strategy
        
    Returns:
        Result indicating success or validation errors
    """
    from strategy.factory import validate_strategy_config
    
    # Parse YAML first
    try:
        strategy_def = yaml.safe_load(yaml_content)
    except yaml.YAMLError as e:
        return {"success": False, "error": f"Invalid YAML: {e}"}
    
    if not isinstance(strategy_def, dict):
        return {"success": False, "error": "Strategy must be a YAML dictionary"}
    
    # Validate the strategy
    errors = validate_strategy_config(strategy_def)
    if errors:
        return {"success": False, "errors": errors}
    
    # Ensure name is set
    if "name" not in strategy_def:
        strategy_def["name"] = strategy_name
    
    # Save to file
    strategies_dir = _get_project_root() / "strategies"
    strategies_dir.mkdir(parents=True, exist_ok=True)
    
    strategy_file = strategies_dir / f"{strategy_name}.yaml"
    with open(strategy_file, 'w') as f:
        yaml.dump(strategy_def, f, default_flow_style=False, sort_keys=False)
    
    return {
        "success": True,
        "file_path": str(strategy_file),
        "message": f"Strategy '{strategy_name}' saved successfully"
    }


@mcp.tool()
def validate_strategy(yaml_content: str) -> Dict[str, Any]:
    """
    Validate a strategy definition without saving it.
    
    Args:
        yaml_content: YAML content defining the strategy
        
    Returns:
        Validation result with any errors found
    """
    from strategy.factory import validate_strategy_config
    
    # Parse YAML first
    try:
        strategy_def = yaml.safe_load(yaml_content)
    except yaml.YAMLError as e:
        return {"is_valid": False, "errors": [f"Invalid YAML: {e}"]}
    
    if not isinstance(strategy_def, dict):
        return {"is_valid": False, "errors": ["Strategy must be a YAML dictionary"]}
    
    # Validate
    errors = validate_strategy_config(strategy_def)
    
    return {
        "is_valid": len(errors) == 0,
        "errors": errors
    }


# ============================================================================
# Backtest Execution Tools
# ============================================================================

@mcp.tool()
def run_backtest(
    strategy: str,
    tickers: str,
    start_date: str,
    end_date: str,
    initial_cash: float = 100000.0,
    sizer_percent: int = 95,
    analysis: bool = True
) -> Dict[str, Any]:
    """
    Start a backtest job asynchronously.
    
    The backtest runs in the background. Use get_job_status to check progress.
    
    Args:
        strategy: Name of the strategy to backtest
        tickers: Comma-separated ticker symbols (e.g., "AAPL" or "AAPL,MSFT")
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format
        initial_cash: Initial portfolio value (default: 100000)
        sizer_percent: Percent of cash to use per trade (default: 95)
        analysis: Whether to run analyzers for detailed metrics (default: True)
        
    Returns:
        Job information including job_id for tracking
    """
    from utils.config import load_strategy_def
    from utils.yf_utils import fetch_and_save_data
    from core.backtest import run_backtest as _run_backtest
    from .jobs import job_manager
    from .schemas import JobStatus
    
    # Load strategy definition
    strategy_def = load_strategy_def(strategy)
    if not strategy_def:
        return {"error": f"Strategy '{strategy}' not found"}
    
    # Create job
    job = job_manager.create_job(strategy, tickers, start_date, end_date)
    
    # Define the backtest task
    def backtest_task():
        # Fetch market data (with rate limiting)
        ticker_list = [t.strip() for t in tickers.split(',')]
        data_files = []
        
        for ticker in ticker_list:
            _rate_limit_yahoo()
            data_file = fetch_and_save_data(
                ticker=ticker,
                start=start_date,
                end=end_date,
                datas_folder=str(_get_project_root() / "datas")
            )
            data_files.append(data_file)
        
        # Build config
        config = {
            "strategy": strategy,
            "start_date": start_date,
            "end_date": end_date,
            "tickers": tickers,
            "sizer": {"PercentSizerInt": {"percents": sizer_percent}},
            "strategy_parameters": strategy_def.get("parameters", {}),
            "analysis": analysis,
            "plot": {"enabled": False},  # Disable plots for MCP
            "json_output": True
        }
        
        # Run backtest
        result = _run_backtest(
            strategy_name=strategy,
            strategy_def=strategy_def,
            data_files=data_files,
            config=config,
            initial_cash=initial_cash,
            plot=False,
            analysis=analysis,
            json_output=True
        )
        
        # Extract key metrics for response
        metrics = {
            "initial_value": result.get("initial_value"),
            "final_value": result.get("final_value"),
            "profit": result.get("profit"),
            "profit_percent": result.get("profit_percent")
        }
        
        # Add analyzer results if available
        if "analyzers" in result:
            analyzers = result["analyzers"]
            metrics["sharpe_ratio"] = analyzers.get("sharpe", {}).get("sharperatio")
            metrics["max_drawdown"] = analyzers.get("drawdown", {}).get("max", {}).get("drawdown")
            metrics["sqn"] = analyzers.get("sqn", {}).get("sqn")
            trades = analyzers.get("trades", {})
            metrics["total_trades"] = trades.get("total", {}).get("closed", 0)
        
        return metrics
    
    # Run in background
    job_manager.run_job_async(job.job_id, backtest_task)
    
    return {
        "job_id": job.job_id,
        "status": job.status.value,
        "message": f"Backtest started for strategy '{strategy}' on {tickers}",
        "strategy": strategy,
        "tickers": tickers,
        "start_date": start_date,
        "end_date": end_date
    }


@mcp.tool()
def get_job_status(job_id: str) -> Dict[str, Any]:
    """
    Get the status of a backtest job.
    
    Args:
        job_id: The job ID returned by run_backtest
        
    Returns:
        Job status and results (if completed)
    """
    from .jobs import job_manager
    
    job = job_manager.get_job(job_id)
    if not job:
        return {"error": f"Job '{job_id}' not found"}
    
    response = {
        "job_id": job.job_id,
        "status": job.status.value,
        "strategy": job.strategy,
        "tickers": job.tickers,
        "start_date": job.start_date,
        "end_date": job.end_date,
        "created_at": job.created_at.isoformat()
    }
    
    if job.started_at:
        response["started_at"] = job.started_at.isoformat()
    if job.completed_at:
        response["completed_at"] = job.completed_at.isoformat()
    if job.error:
        response["error"] = job.error
    if job.result:
        response["result"] = job.result
    
    return response


@mcp.tool()
def list_jobs(limit: int = 10) -> List[Dict[str, Any]]:
    """
    List recent backtest jobs.
    
    Args:
        limit: Maximum number of jobs to return (default: 10)
        
    Returns:
        List of recent jobs with their status
    """
    from .jobs import job_manager
    
    jobs = job_manager.list_jobs(limit=limit)
    return [
        {
            "job_id": job.job_id,
            "status": job.status.value,
            "strategy": job.strategy,
            "tickers": job.tickers,
            "created_at": job.created_at.isoformat(),
            "completed_at": job.completed_at.isoformat() if job.completed_at else None
        }
        for job in jobs
    ]


# ============================================================================
# Market Data Tools
# ============================================================================

@mcp.tool()
def fetch_market_data(
    ticker: str,
    start_date: str,
    end_date: str,
    force_download: bool = False
) -> Dict[str, Any]:
    """
    Fetch historical market data from Yahoo Finance.
    
    Data is cached locally to avoid repeated downloads.
    Rate-limited to avoid Yahoo Finance API throttling.
    
    Args:
        ticker: Stock ticker symbol (e.g., "AAPL")
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format
        force_download: If True, re-download even if cached
        
    Returns:
        Information about the fetched data
    """
    from utils.yf_utils import fetch_and_save_data
    
    # Apply rate limiting
    _rate_limit_yahoo()
    
    datas_folder = str(_get_project_root() / "datas")
    
    # Check if cached
    data_path = Path(datas_folder)
    expected_file = data_path / f"{ticker}-{start_date}-to-{end_date}.csv"
    was_cached = expected_file.exists() and not force_download
    
    try:
        file_path = fetch_and_save_data(
            ticker=ticker,
            start=start_date,
            end=end_date,
            datas_folder=datas_folder,
            force_download=force_download
        )
        
        # Count rows
        with open(file_path, 'r') as f:
            rows = sum(1 for _ in f) - 1  # Subtract header
        
        return {
            "ticker": ticker,
            "start_date": start_date,
            "end_date": end_date,
            "file_path": file_path,
            "rows": rows,
            "cached": was_cached
        }
    except Exception as e:
        return {"error": str(e)}


# ============================================================================
# Discovery Tools
# ============================================================================

@mcp.tool()
def list_indicators() -> List[Dict[str, Any]]:
    """
    List all available indicators for use in strategies.
    
    Returns both custom indicators (from the indicator/ module) and
    common Backtrader indicators.
    """
    import indicator
    import backtrader as bt
    
    indicators = []
    
    # Custom indicators
    indicator_dir = _get_project_root() / "indicator"
    for file in indicator_dir.glob("*.py"):
        if file.name.startswith("_"):
            continue
        
        module_name = file.stem
        try:
            module = getattr(indicator, module_name, None)
            if module:
                # Find indicator classes
                for name in dir(module):
                    obj = getattr(module, name)
                    if isinstance(obj, type) and issubclass(obj, bt.Indicator) and obj is not bt.Indicator:
                        # Get parameters
                        params = []
                        if hasattr(obj, 'params'):
                            if isinstance(obj.params, tuple):
                                params = [p[0] if isinstance(p, tuple) else str(p) for p in obj.params]
                        
                        indicators.append({
                            "name": name,
                            "source": "custom",
                            "module": module_name,
                            "description": obj.__doc__.split('\n')[0] if obj.__doc__ else None,
                            "parameters": params
                        })
        except Exception:
            pass
    
    # Add custom indicators directly from the indicator module
    for name in ['VolumeSpike', 'ZigZag', 'LocalPeakTrough', 'Fractals']:
        if hasattr(indicator, name):
            obj = getattr(indicator, name)
            params = []
            if hasattr(obj, 'params'):
                if isinstance(obj.params, tuple):
                    params = [p[0] if isinstance(p, tuple) else str(p) for p in obj.params]
            
            # Avoid duplicates
            if not any(i["name"] == name for i in indicators):
                indicators.append({
                    "name": name,
                    "source": "custom",
                    "description": obj.__doc__.split('\n')[0] if obj.__doc__ else None,
                    "parameters": params
                })
    
    # Common Backtrader indicators
    common_bt_indicators = [
        ("SMA", "Simple Moving Average", ["period"]),
        ("EMA", "Exponential Moving Average", ["period"]),
        ("RSI", "Relative Strength Index", ["period"]),
        ("MACD", "Moving Average Convergence Divergence", ["period_me1", "period_me2", "period_signal"]),
        ("BollingerBands", "Bollinger Bands", ["period", "devfactor"]),
        ("ATR", "Average True Range", ["period"]),
        ("Stochastic", "Stochastic Oscillator", ["period", "period_dfast", "period_dslow"]),
        ("ADX", "Average Directional Index", ["period"]),
        ("CCI", "Commodity Channel Index", ["period"]),
        ("WilliamsR", "Williams %R", ["period"]),
        ("OBV", "On Balance Volume", []),
        ("VWAP", "Volume Weighted Average Price", []),
    ]
    
    for name, desc, params in common_bt_indicators:
        indicators.append({
            "name": name,
            "source": "backtrader",
            "description": desc,
            "parameters": params
        })
    
    return indicators


@mcp.tool()
def list_runtime_configs(strategy_name: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    List available runtime configuration examples.
    
    These are example configurations that show how to set up
    backtest runs with different strategies and parameters.
    
    Args:
        strategy_name: Optional filter by strategy name (case-insensitive partial match)
        
    Returns:
        List of runtime configurations, optionally filtered by strategy
    """
    conf_dir = _get_project_root() / "conf"
    configs = []
    
    if not conf_dir.exists():
        return configs
    
    for file in conf_dir.glob("*.yaml"):
        try:
            with open(file, 'r') as f:
                config = yaml.safe_load(f) or {}
            
            config_strategy = config.get("strategy", "")
            
            # Filter by strategy name if provided
            if strategy_name:
                if strategy_name.lower() not in config_strategy.lower():
                    continue
            
            configs.append({
                "name": file.stem,
                "file_path": str(file),
                "strategy": config_strategy,
                "tickers": config.get("tickers"),
                "start_date": config.get("start_date"),
                "end_date": config.get("end_date")
            })
        except Exception as e:
            logger.warning(f"Failed to parse config {file}: {e}")
    
    return configs


@mcp.tool()
def get_runtime_config(config_name: str) -> Dict[str, Any]:
    """
    Get a runtime configuration by name.
    
    Args:
        config_name: Name of the config file (without .yaml extension)
        
    Returns:
        The configuration content
    """
    conf_dir = _get_project_root() / "conf"
    
    for ext in ['.yaml', '.yml']:
        config_file = conf_dir / f"{config_name}{ext}"
        if config_file.exists():
            with open(config_file, 'r') as f:
                yaml_content = f.read()
            
            config = yaml.safe_load(yaml_content)
            return {
                "name": config_name,
                "yaml_content": yaml_content,
                "parsed": config,
                "file_path": str(config_file)
            }
    
    return {"error": f"Config '{config_name}' not found"}


# ============================================================================
# MCP Resources
# ============================================================================

STRATEGY_SCHEMA = """# Strategy Definition YAML Schema

A strategy definition file defines trading logic using YAML. 
Save it in the `strategies/` folder with a `.yaml` extension.

## Structure

```yaml
name: StrategyName           # Required: Unique strategy name

indicators:                  # Dictionary of technical indicators
  indicator_name:            # Your name for the indicator
    type: IndicatorType      # SMA, RSI, VolumeSpike, MACD, etc.
    period: param_name       # Parameters can reference `parameters` section
    # ... other indicator-specific params

triggers:                    # List of trigger conditions
  - name: TriggerName        # Descriptive name for the trigger
    condition: "expression"  # Boolean expression (see below)
    actions:                 # Actions to execute when condition is true
      - name: action_name
        type: TradeAction    # Currently only TradeAction is supported
        ticker: tickers[0]   # Data feed reference
        signal: Long         # Long or Short
        orderType: Market    # Market, Limit, StopLimit, StopTrail, StopTrailLimit
        price: close * 1.02  # Price expression (for Limit orders)
        valid: 7             # Order validity in days
        trailpercent: 0.05   # For trailing stops (0.05 = 5%)
        plimit: close * 0.98 # Limit price for stop-limit orders

sizer:                       # Position sizing configuration
  PercentSizerInt:           # Sizer type
    percents: 95             # Use 95% of available cash

parameters:                  # Tunable parameters
  param_name: default_value  # Referenced in indicators/triggers

plot:                        # Optional plotting config
  enabled: false
```

## Expression Language

### Available Variables
- `open`, `high`, `low`, `close`, `volume` - Current bar OHLCV data
- `indicators.name` - Indicator values (e.g., `indicators.sma`)
- `tickers[0]` - First data feed reference

### Operators
- Comparison: `>`, `<`, `>=`, `<=`, `==`, `!=`
- Logical: `and`, `or`
- Math: `+`, `-`, `*`, `/`

### Example Conditions
```
indicators.sma > close                    # SMA above price
indicators.rsi < 30 and volume > 1000000  # RSI oversold with high volume
(high - low) / close > 0.05               # Daily range > 5%
indicators.vs == 1                        # Volume spike detected
```

## Order Types

| Type | Description | Required Fields |
|------|-------------|-----------------|
| Market | Execute at market price | signal, ticker |
| Limit | Execute at specified price | signal, ticker, price, valid |
| StopTrail | Trailing stop loss | signal, ticker, price, trailpercent |
| StopLimit | Stop with limit price | signal, ticker, price, plimit |
| StopTrailLimit | Trailing stop with limit | signal, ticker, price, trailpercent, plimit |

## Sizer Types

| Type | Description | Parameters |
|------|-------------|------------|
| PercentSizerInt | Use % of cash | percents (int) |
| AllInSizerInt | Use all available cash | - |
| FixedSize | Fixed number of shares | stake (int) |
"""

EXAMPLE_STRATEGY = """# Example: Simple Moving Average Crossover Strategy

name: SMACrossover

indicators:
  sma_fast:
    type: SMA
    period: sma_fast_period
  sma_slow:
    type: SMA
    period: sma_slow_period

triggers:
  - name: goldenCross
    condition: indicators.sma_fast > indicators.sma_slow
    actions:
      - name: buy_signal
        type: TradeAction
        ticker: tickers[0]
        signal: Long
        orderType: Market
        
  - name: deathCross
    condition: indicators.sma_fast < indicators.sma_slow
    actions:
      - name: sell_signal
        type: TradeAction
        ticker: tickers[0]
        signal: Short
        orderType: Market

sizer:
  PercentSizerInt:
    percents: 95

parameters:
  sma_fast_period: 10
  sma_slow_period: 30
"""


@mcp.resource("strategy://schema")
def get_strategy_schema() -> str:
    """Get the YAML schema documentation for strategy definitions."""
    return STRATEGY_SCHEMA


@mcp.resource("strategy://example")
def get_strategy_example() -> str:
    """Get an example strategy definition."""
    return EXAMPLE_STRATEGY


@mcp.resource("indicator://list")
def get_indicator_docs() -> str:
    """Get documentation for available indicators."""
    docs = """# Available Indicators

## Custom Indicators (from indicator/ module)

### VolumeSpike
Detects volume spikes using MACD histogram analysis.
- Parameters: macd_fast, macd_slow, macd_signal, macd_hist_mean_period, macd_hist_mean_threshold
- Returns: 1 when spike detected, 0 otherwise

### ZigZag
Identifies trend reversals and significant price movements.
- Parameters: deviation (minimum % move to register)
- Returns: 1 for up-swing, -1 for down-swing, 0 otherwise

### LocalPeakTrough
Detects local price peaks and troughs.
- Parameters: period (lookback period)
- Returns: 1 for peak, -1 for trough, 0 otherwise

### Fractals
Bill Williams fractal indicator for reversal points.
- Parameters: period
- Returns: 1 for up fractal, -1 for down fractal, 0 otherwise

## Common Backtrader Indicators

### SMA (Simple Moving Average)
- Parameters: period
- Usage: `indicators.sma > close` (price below SMA)

### EMA (Exponential Moving Average)
- Parameters: period
- More responsive to recent prices than SMA

### RSI (Relative Strength Index)
- Parameters: period (default: 14)
- Usage: `indicators.rsi < 30` (oversold), `indicators.rsi > 70` (overbought)

### MACD
- Parameters: period_me1 (fast), period_me2 (slow), period_signal
- Returns: macd line, signal line, histogram

### BollingerBands
- Parameters: period, devfactor (standard deviations)
- Returns: top, mid, bot bands

### ATR (Average True Range)
- Parameters: period
- Measures volatility

### Stochastic
- Parameters: period, period_dfast, period_dslow
- Momentum indicator (0-100 scale)

### ADX (Average Directional Index)
- Parameters: period
- Measures trend strength (>25 = trending)

For full Backtrader indicator list, see: https://www.backtrader.com/docu/indautoref/
"""
    return docs


# ============================================================================
# Main Entry Point
# ============================================================================

def main():
    """Run the MCP server."""
    mcp.run()


if __name__ == "__main__":
    main()
