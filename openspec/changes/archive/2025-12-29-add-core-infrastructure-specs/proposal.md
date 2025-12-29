# Change: Add Core Infrastructure Specifications

## Why

The core infrastructure for My Quant V2 (CLI, configuration, data layer, and expression system) has been implemented but lacks formal specifications. Adding specs will:

1. Document the current working behavior as the source of truth
2. Enable spec-driven validation of future changes
3. Provide clear contracts for AI assistants and developers
4. Support the OpenSpec workflow established in this project

## What Changes

- **ADDED**: `cli-interface` spec - Documents CLI argument parsing, config file merging, and execution flow
- **ADDED**: `configuration-system` spec - Documents runtime config and strategy definition schemas
- **ADDED**: `data-layer` spec - Documents Yahoo Finance data fetching and caching
- **ADDED**: `expression-system` spec - Documents condition and expression evaluation

This is a **documentation-only change** that codifies existing implemented behavior as specifications. No code changes are required.

## Impact

- Affected specs: New specs in `openspec/specs/`
- Affected code: None (specs document existing behavior)
- Breaking changes: None

## Success Criteria

1. All new specs pass `openspec validate --strict`
2. Specs accurately reflect implemented behavior in:
   - `cli/main.py`
   - `utils/config.py`
   - `utils/yf_utils.py`
   - `strategy/expression/`
3. Existing tests (43 tests) continue to pass
