# Change: Add Strategy Framework Specification

## Why
The strategy framework is a core capability that handles trading logic, triggers, actions, and dynamic strategy generation from YAML. While the implementation exists in `strategy/`, there's no formal specification documenting the expected behavior and contracts. This makes it difficult to validate behavior, track changes, and onboard contributors.

## What Changes
- **NEW** `strategy-framework` spec defining:
  - BaseStrategy contract and lifecycle
  - Trigger system with conditions and actions
  - Trade execution and order types
  - Strategy factory for YAML-to-class generation
  - Strategy validation

## Impact
- Affected specs: None existing (new capability)
- Affected code: `strategy/base.py`, `strategy/factory.py`, `strategy/trigger_system.py`
- Dependencies: Uses `expression-system` spec for condition/expression evaluation
