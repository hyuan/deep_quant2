# Change: Add Backtest Engine Specification

## Why
The backtest engine (`core/backtest.py`) orchestrates the entire backtesting process—Cerebro setup, strategy resolution, data feeds, analyzers, and result processing—but lacks a formal specification. This makes it difficult to ensure consistent behavior, document capabilities, and guide future enhancements.

## What Changes
- **NEW** capability specification: `backtest-engine`
- Documents Cerebro orchestration, strategy resolution, data feed management, analyzer setup, optimization support, and result processing
- No code changes required—this is a documentation/specification change only

## Impact
- Affected specs: Creates new `openspec/specs/backtest-engine/spec.md`
- Affected code: Documents existing `core/backtest.py` behavior
- No breaking changes—purely additive specification
