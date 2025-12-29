## ADDED Requirements

### Requirement: Condition Expression Parsing
The system SHALL parse condition expressions into evaluable AST nodes.

#### Scenario: Parse comparison operators
- **WHEN** condition contains `close > 100`
- **THEN** system parses as comparison node with greater-than operator

#### Scenario: Parse equality operators
- **WHEN** condition contains `indicators.vs == 1`
- **THEN** system parses as comparison node with equality operator

#### Scenario: Parse logical AND
- **WHEN** condition contains `close > 100 and volume > 1000000`
- **THEN** system parses as logical AND combining two comparisons

#### Scenario: Parse logical OR
- **WHEN** condition contains `close > 100 or close < 50`
- **THEN** system parses as logical OR combining two comparisons


### Requirement: Condition Evaluation
The system SHALL evaluate condition expressions against market context.

#### Scenario: Evaluate simple comparison
- **WHEN** condition is `close > 100` AND context has `close: 150`
- **THEN** system evaluates to True

#### Scenario: Evaluate indicator comparison
- **WHEN** condition is `indicators.sma > close` AND context has both values
- **THEN** system compares indicator value against close price

#### Scenario: Evaluate compound condition
- **WHEN** condition is `close > 100 and volume > 1000000`
- **THEN** system evaluates both comparisons and returns logical AND result

#### Scenario: Handle missing variable
- **WHEN** condition references undefined variable
- **THEN** system raises EvaluationError with descriptive message


### Requirement: Math Expression Parsing
The system SHALL parse mathematical expressions for price calculations.

#### Scenario: Parse arithmetic operators
- **WHEN** expression contains `close * 1.02`
- **THEN** system parses as multiplication operation

#### Scenario: Parse operator precedence
- **WHEN** expression contains `close + high * 0.5`
- **THEN** system respects multiplication before addition

#### Scenario: Parse parentheses
- **WHEN** expression contains `(high - low) / close`
- **THEN** system evaluates parenthesized expression first


### Requirement: Math Expression Evaluation
The system SHALL evaluate mathematical expressions to numeric results.

#### Scenario: Evaluate multiplication
- **WHEN** expression is `close * 1.02` AND context has `close: 100`
- **THEN** system returns 102.0

#### Scenario: Evaluate division
- **WHEN** expression is `volume / 1000000` AND context has `volume: 5000000`
- **THEN** system returns 5.0

#### Scenario: Handle division by zero
- **WHEN** expression involves division by zero
- **THEN** system raises EvaluationError

#### Scenario: Evaluate complex expression
- **WHEN** expression is `(high - low) / close * 100`
- **THEN** system correctly evaluates all operations in order


### Requirement: Variable Resolution
The system SHALL resolve variables from the evaluation context.

#### Scenario: Resolve OHLCV variables
- **WHEN** expression references `open`, `high`, `low`, `close`, `volume`
- **THEN** system resolves from current bar data in context

#### Scenario: Resolve indicator variables
- **WHEN** expression references `indicators.sma`
- **THEN** system resolves indicator value from context

#### Scenario: Resolve numeric literals
- **WHEN** expression contains `100` or `1.02`
- **THEN** system parses as numeric constant


### Requirement: Expression Tokenization
The system SHALL tokenize expression strings into tokens.

#### Scenario: Tokenize operators
- **WHEN** expression contains `>`, `<`, `>=`, `<=`, `==`, `!=`
- **THEN** system produces comparison operator tokens

#### Scenario: Tokenize arithmetic
- **WHEN** expression contains `+`, `-`, `*`, `/`
- **THEN** system produces arithmetic operator tokens

#### Scenario: Tokenize identifiers
- **WHEN** expression contains `close` or `indicators.sma`
- **THEN** system produces identifier tokens with full dotted name

#### Scenario: Tokenize numbers
- **WHEN** expression contains `100` or `1.02`
- **THEN** system produces number tokens with parsed value


### Requirement: Callable Condition Support
The system SHALL support callable functions as conditions.

#### Scenario: Evaluate callable condition
- **WHEN** condition is a Python callable that returns boolean
- **THEN** system calls the function with context and returns result

#### Scenario: Callable with strategy access
- **WHEN** callable condition needs strategy instance
- **THEN** context includes `strategy` key with instance reference
