# strategy-framework Specification

## Purpose
Defines the strategy framework for YAML-driven trading strategies, including the BaseStrategy contract, trigger system, trade execution, and dynamic strategy generation.

## ADDED Requirements

### Requirement: BaseStrategy Lifecycle
The system SHALL manage strategy lifecycle through initialization, execution, and termination phases.

#### Scenario: Strategy initialization
- **WHEN** strategy class is instantiated
- **THEN** system initializes indicators dictionary, trigger system, and evaluation components
- **AND** calls `setup_indicators()` and `setup_trigger_system()` hooks

#### Scenario: Strategy execution per bar
- **WHEN** Backtrader calls `next()` on each bar
- **THEN** system evaluates all enabled triggers against current market data
- **AND** executes actions for triggers whose conditions are met

#### Scenario: Strategy termination
- **WHEN** Backtrader calls `stop()` at end of backtest
- **THEN** system logs final portfolio value
- **AND** cleans up resources

#### Scenario: Indicator setup hook
- **WHEN** strategy defines `setup_indicators()` method
- **THEN** system calls method during initialization to populate `indicators` dictionary

#### Scenario: Trigger setup hook
- **WHEN** strategy defines `setup_trigger_system()` method
- **THEN** system calls method during initialization to configure triggers

### Requirement: Trigger System Management
The system SHALL manage triggers with conditions and associated actions.

#### Scenario: Add trigger to system
- **WHEN** `TriggerSystem.add_trigger()` is called with valid trigger
- **THEN** system stores trigger by name for evaluation
- **AND** validates condition syntax for string conditions

#### Scenario: Remove trigger from system
- **WHEN** `TriggerSystem.remove_trigger()` is called with existing trigger name
- **THEN** system removes trigger from storage

#### Scenario: Enable and disable triggers
- **WHEN** `enable_trigger()` or `disable_trigger()` is called
- **THEN** system updates trigger's enabled state
- **AND** disabled triggers are skipped during evaluation

#### Scenario: Prevent duplicate trigger names
- **WHEN** trigger with existing name is added
- **THEN** system raises `TriggerValidationError`

#### Scenario: Validate trigger maximum
- **WHEN** trigger count exceeds configured maximum
- **THEN** system raises `TriggerSystemError`

### Requirement: Trigger Condition Evaluation
The system SHALL evaluate trigger conditions against current market context.

#### Scenario: Evaluate string condition
- **WHEN** trigger has string condition like `close > 100`
- **THEN** system parses and evaluates using `ConditionEvaluator`
- **AND** returns boolean result

#### Scenario: Evaluate callable condition
- **WHEN** trigger has callable condition function
- **THEN** system calls function with context dictionary
- **AND** returns boolean result

#### Scenario: Skip active triggers
- **WHEN** trigger is already active (has pending actions)
- **THEN** system skips evaluation to prevent duplicate executions

#### Scenario: Build evaluation context
- **WHEN** condition is evaluated
- **THEN** context includes OHLCV data, indicator values, and strategy reference

### Requirement: Trade Action Execution
The system SHALL execute trading actions when trigger conditions are met.

#### Scenario: Execute first action immediately
- **WHEN** trigger condition is met
- **THEN** system executes first action immediately
- **AND** queues remaining actions as pending

#### Scenario: Execute pending actions sequentially
- **WHEN** previous action order completes
- **THEN** system executes next pending action for that trigger

#### Scenario: Validate action parameters
- **WHEN** action is executed
- **THEN** system validates required parameters (signal, orderType)
- **AND** applies default values for optional parameters

#### Scenario: Track orders by trigger
- **WHEN** order is created from action
- **THEN** system tracks order under trigger name and action name
- **AND** can locate trigger from completed/failed orders

### Requirement: Order Type Support
The system SHALL support multiple order types for trade execution.

#### Scenario: Execute Market order
- **WHEN** action has `orderType: Market`
- **THEN** system creates market order at current price

#### Scenario: Execute Limit order
- **WHEN** action has `orderType: Limit` and `price` expression
- **THEN** system creates limit order at evaluated price

#### Scenario: Execute StopLimit order
- **WHEN** action has `orderType: StopLimit` with `price` and `plimit`
- **THEN** system creates stop-limit order with stop and limit prices

#### Scenario: Execute StopTrail order
- **WHEN** action has `orderType: StopTrail` with `trailpercent` or `trailamount`
- **THEN** system creates trailing stop order

#### Scenario: Execute StopTrailLimit order
- **WHEN** action has `orderType: StopTrailLimit` with trail and limit parameters
- **THEN** system creates trailing stop-limit order

#### Scenario: Set order validity
- **WHEN** action has `valid: N` parameter
- **THEN** system sets order expiration to N days from current date

### Requirement: Order Signal Handling
The system SHALL handle Long and Short signals with position checks.

#### Scenario: Long signal execution
- **WHEN** action has `signal: Long`
- **THEN** system creates buy order if cash available and no existing long position

#### Scenario: Short signal execution
- **WHEN** action has `signal: Short`
- **THEN** system creates sell order if position exists to close

#### Scenario: Reject Long without cash
- **WHEN** Long signal executed with insufficient cash
- **THEN** system logs rejection and returns None

#### Scenario: Reject Short without position
- **WHEN** Short signal executed with no position
- **THEN** system logs rejection and returns None

### Requirement: Order Notification Handling
The system SHALL handle order status changes through notifications.

#### Scenario: Handle completed order
- **WHEN** order status is `Completed`
- **THEN** system logs execution details (price, cost, commission)
- **AND** processes next pending action for the trigger

#### Scenario: Handle failed order
- **WHEN** order status is `Canceled`, `Margin`, `Rejected`, or `Expired`
- **THEN** system logs failure with status
- **AND** cleans up trigger state and pending actions

#### Scenario: Handle trade completion
- **WHEN** trade is closed
- **THEN** system logs gross and net profit/loss

### Requirement: Strategy Factory Generation
The system SHALL dynamically generate strategy classes from YAML definitions.

#### Scenario: Create strategy from YAML
- **WHEN** `create_strategy()` is called with strategy name and definition
- **THEN** system creates new class inheriting from `BaseStrategy`
- **AND** class name is set to provided strategy name

#### Scenario: Generate indicator factories
- **WHEN** strategy definition contains `indicators` section
- **THEN** system creates factory functions for each indicator
- **AND** factories resolve parameter references from strategy params

#### Scenario: Generate trigger system setup
- **WHEN** strategy definition contains `triggers` section
- **THEN** generated class configures trigger system in `setup_trigger_system()`

#### Scenario: Map strategy parameters
- **WHEN** strategy definition contains `parameters` section
- **THEN** system adds parameters to strategy class `params` tuple
- **AND** optimization lists use first value as default

### Requirement: Indicator Factory Creation
The system SHALL create indicators from configuration dictionaries.

#### Scenario: Create Backtrader indicator
- **WHEN** indicator type is a standard Backtrader indicator (e.g., SMA, EMA)
- **THEN** system resolves from `bt.indicators` module

#### Scenario: Create custom indicator
- **WHEN** indicator type is a custom indicator (e.g., VolumeSpike)
- **THEN** system resolves from `indicator` module

#### Scenario: Resolve parameter references
- **WHEN** indicator config has parameter like `period: ind_sma_period`
- **THEN** system resolves from strategy `params` at instantiation time

#### Scenario: Invalid indicator type
- **WHEN** indicator type is not found in any module
- **THEN** system raises `IndicatorCreationError`

### Requirement: Trigger Configuration Parsing
The system SHALL parse trigger configurations into Trigger objects.

#### Scenario: Parse trigger with name
- **WHEN** trigger config has `name` field
- **THEN** system uses provided name

#### Scenario: Generate name for unnamed trigger
- **WHEN** trigger config lacks `name` field
- **THEN** system generates name like `UnnamedTrigger_0`

#### Scenario: Parse multiple actions
- **WHEN** trigger config has multiple actions
- **THEN** system creates `TriggerAction` for each valid action
- **AND** filters out None or empty actions

#### Scenario: Validate action type
- **WHEN** action has type other than `TradeAction`
- **THEN** system raises `TriggerValidationError`

### Requirement: Strategy Configuration Validation
The system SHALL validate strategy configurations before use.

#### Scenario: Validate required name
- **WHEN** strategy config lacks name or has empty name
- **THEN** validation returns error for missing name

#### Scenario: Validate indicators structure
- **WHEN** indicators section is not a dictionary
- **THEN** validation returns error

#### Scenario: Validate indicator type required
- **WHEN** indicator config lacks `type` field
- **THEN** validation returns error for that indicator

#### Scenario: Validate triggers structure
- **WHEN** triggers section is not a list
- **THEN** validation returns error

#### Scenario: Validate trigger has condition
- **WHEN** trigger config lacks non-empty condition
- **THEN** validation returns error for that trigger

#### Scenario: Validate trigger has actions
- **WHEN** trigger config has no valid actions
- **THEN** validation returns error for that trigger
