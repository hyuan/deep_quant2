# My Quant V2

A YAML-driven quantitative trading backtest framework built on Backtrader.

## Features

- Define trading strategies via YAML configuration files
- Run backtests with customizable parameters
- Optimization support for strategy parameters
- Comprehensive analysis with Sharpe Ratio, Max Drawdown, SQN
- Multiple order types: Market, Limit, StopLimit, StopTrail, StopTrailLimit
- Custom technical indicators
- Expression-based condition evaluation

## Installation

```bash
pip install -e .
```

## Quick Start

```bash
python -m cli.main --config conf/example.yaml --strategy ExampleStrategy
```

## Documentation

See [PRD.md](docs/PRD.md) for detailed architecture and usage documentation.

## Project Structure

```
my_quant_v2/
├── cli/              # Command-line interface
├── core/             # Backtest engine
├── strategy/         # Strategy framework
├── indicator/        # Technical indicators
├── utils/            # Utility functions
├── strategies/       # Strategy YAML definitions
├── conf/             # Runtime configurations
├── templates/        # Jinja2 templates
├── datas/            # Data files
└── output/           # Output files
```
