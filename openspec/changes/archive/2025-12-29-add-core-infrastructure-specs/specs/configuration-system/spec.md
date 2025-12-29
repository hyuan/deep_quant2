## ADDED Requirements

### Requirement: Runtime Configuration Loading
The system SHALL load runtime configuration from YAML files.

#### Scenario: Load valid config file
- **WHEN** user specifies a valid YAML config file path
- **THEN** system parses and returns configuration dictionary

#### Scenario: Config file not found
- **WHEN** user specifies a non-existent config file path
- **THEN** system raises FileNotFoundError with descriptive message

#### Scenario: Empty config file
- **WHEN** config file exists but is empty
- **THEN** system returns empty dictionary


### Requirement: Strategy Definition Loading
The system SHALL load strategy definitions from YAML files in the strategies directory.

#### Scenario: Load existing strategy
- **WHEN** strategy file exists at `strategies/{name}.yaml` or `strategies/{name}.yml`
- **THEN** system loads and returns strategy definition dictionary

#### Scenario: Strategy not found
- **WHEN** strategy file does not exist in strategies directory
- **THEN** system returns empty dictionary (allows factory creation fallback)


### Requirement: Strategy Definition Saving
The system SHALL save strategy definitions to YAML files.

#### Scenario: Save new strategy
- **WHEN** system saves strategy definition with name "MyStrategy"
- **THEN** file is created at `strategies/MyStrategy.yaml` with YAML content

#### Scenario: Create strategies directory
- **WHEN** strategies directory does not exist during save
- **THEN** system creates the directory before saving


### Requirement: Sizer Configuration
The system SHALL configure position sizers from configuration.

#### Scenario: Configure PercentSizerInt
- **WHEN** config contains `sizer: {PercentSizerInt: {percents: 95}}`
- **THEN** system returns PercentSizerInt class with percents=95

#### Scenario: Configure AllInSizerInt
- **WHEN** config contains `sizer: {AllInSizerInt: {}}`
- **THEN** system returns AllInSizerInt class with default params

#### Scenario: Configure FixedSize
- **WHEN** config contains `sizer: {FixedSize: {stake: 100}}`
- **THEN** system returns FixedSize class with stake=100

#### Scenario: Unknown sizer type
- **WHEN** config contains unknown sizer type
- **THEN** system logs warning and returns AllInSizerInt as fallback

#### Scenario: Missing sizer config
- **WHEN** sizer configuration is not provided
- **THEN** system logs warning and returns AllInSizerInt as default


### Requirement: Configuration Merging
The system SHALL merge configurations with proper precedence.

#### Scenario: Merge strategy parameters
- **WHEN** config contains `strategy_parameters` section
- **THEN** system merges values into strategy definition's `parameters`

#### Scenario: Deep merge nested values
- **WHEN** both configs have nested dictionaries with same keys
- **THEN** system recursively merges nested values

#### Scenario: Override scalar values
- **WHEN** both configs have same scalar key
- **THEN** later config value overrides earlier value


### Requirement: Logging Setup
The system SHALL configure logging with console and optional file output.

#### Scenario: Default logging setup
- **WHEN** setup_logging is called with defaults
- **THEN** system configures INFO level with console handler and backtest.log file

#### Scenario: Disable file logging
- **WHEN** setup_logging is called with log_file=None
- **THEN** system configures console-only logging
