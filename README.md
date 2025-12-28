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

### Prerequisites

#### Step 1: Install Python, pyenv and uv

- This application requires Python 3.10 or later.
- Install uv: <https://docs.astral.sh/uv/getting-started/installation/>
- Install pyenv: <https://github.com/pyenv/pyenv?tab=readme-ov-file#installation>

#### Step 2: Set up virtual environment

```bash
uv venv
```

#### Step 3: Activate the virtual environment

Windows:

```bash
.\venv\Scripts\activate
```

Linux/Mac:

```bash
source .venv/bin/activate
```

#### Step 4: Install dependencies

```bash
uv sync
```

## Quick Start

### Option 1: Run with pipx (Recommended for end users)

Install pipx if you haven't already:
```bash
# macOS
brew install pipx
pipx ensurepath

# Linux
python3 -m pip install --user pipx
python3 -m pipx ensurepath

# Windows
python -m pip install --user pipx
python -m pipx ensurepath
```

Install and run the application:
```bash
# Install from the project directory
pipx install .

# Run the application
my-quant-v2 --config conf/example_strategy.yaml

# Or use the CLI module directly
python -m cli.main --config conf/example_strategy.yaml
```

### Option 2: Run with uv (For development)

Run Example Strategy
```bash
python -m cli.main --config conf/example_strategy.yaml
```

Run Volume Spike Strategy
```bash
python -m cli.main --config conf/volume_spike_msft.yaml
```

Run Optimization
```bash
python -m cli.main --config conf/volume_spike_tsla_opt.yaml
```

## Running Tests

Run all tests:
```bash
pytest tests/
```

Run tests with coverage:
```bash
pytest tests/ --cov=. --cov-report=term-missing
```

Run tests verbosely:
```bash
pytest tests/ -v
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
