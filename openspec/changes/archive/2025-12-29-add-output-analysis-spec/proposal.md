# Change: Add Output & Analysis Specification

## Why

The project has implemented Output & Analysis functionality (console logging, JSON export, trade analysis, analyzer formatting) scattered across `utils/analysis_utils.py`, `core/backtest.py`, and `strategy/base.py`. However, there is no dedicated spec documenting the analysis formatting, metrics calculation, and output format requirements. This makes it difficult to understand the complete output contract and extend analysis capabilities consistently.

## What Changes

- Add new `output-analysis` capability spec documenting:
  - Console logging format for backtest events
  - Trade analysis formatting and metrics
  - Analyzer result formatting (Sharpe, DrawDown, SQN)
  - JSON output schema
  - Logging levels and conventions

## Impact

- Affected specs: None (new capability)
- Related specs: `backtest-engine` (orchestrates analysis), `cli-interface` (exposes options)
- Affected code: `utils/analysis_utils.py`, `strategy/base.py` (logging), `core/backtest.py` (JSON output)
