"""Strategy factory for creating strategies dynamically from YAML definitions."""

import logging
from typing import Any, Callable, Dict, List, Type

import backtrader as bt

import indicator
from .base import BaseStrategy
from .trigger_system import Trigger, TriggerAction, TriggerSystem, TriggerValidationError


logger = logging.getLogger(__name__)


# ===== Exceptions =====

class IndicatorCreationError(Exception):
    """Exception raised when indicator creation fails."""
    pass


class StrategyCreationError(Exception):
    """Exception raised when strategy creation fails."""
    pass


# ===== Indicator Factory =====

def create_indicator(
    indicator_config: Dict[str, Any],
    config_parameters: Dict[str, Any]
) -> Callable[[bt.AbstractDataBase], Any]:
    """
    Create an indicator factory function from configuration.
    
    Args:
        indicator_config: Indicator configuration including type and parameters
        config_parameters: Strategy parameters for variable substitution
        
    Returns:
        Function that creates the indicator instance
        
    Raises:
        IndicatorCreationError: If indicator creation fails
    """
    if not isinstance(indicator_config, dict):
        raise IndicatorCreationError("Indicator config must be a dictionary")
    
    indicator_type = indicator_config.get('type', '')
    if not indicator_type:
        raise IndicatorCreationError("Indicator type is required")
    
    try:
        # Try to get indicator class from bt.indicators or custom indicators
        if hasattr(bt.indicators, indicator_type):
            indicator_class = getattr(bt.indicators, indicator_type)
        elif hasattr(indicator, indicator_type):
            indicator_class = getattr(indicator, indicator_type)
        else:
            raise IndicatorCreationError(f"Unsupported indicator type: {indicator_type}")
        
        # Extract parameters (exclude 'type' key)
        params = {k: v for k, v in indicator_config.items() if k != 'type'}
        
        # Replace parameter references with actual values
        for key in list(params.keys()):
            value = params[key]
            if isinstance(value, str) and value in config_parameters:
                params[key] = config_parameters[value]
        
        # Return factory function
        def create_indicator_instance(data: bt.AbstractDataBase) -> Any:
            try:
                return indicator_class(data, **params)
            except Exception as e:
                raise IndicatorCreationError(
                    f"Failed to create {indicator_type} indicator: {e}"
                ) from e
        
        return create_indicator_instance
        
    except IndicatorCreationError:
        raise
    except Exception as e:
        raise IndicatorCreationError(
            f"Failed to setup indicator {indicator_type}: {e}"
        ) from e


# ===== Trigger System Factory =====

def setup_trigger_system(
    trigger_system: TriggerSystem,
    triggers_config: List[Dict[str, Any]]
) -> None:
    """
    Create triggers from configuration and add to trigger system.
    
    Args:
        trigger_system: Existing TriggerSystem instance
        triggers_config: List of trigger configurations
        
    Raises:
        TriggerValidationError: If trigger validation fails
    """
    if not isinstance(triggers_config, list):
        raise TriggerValidationError("Triggers config must be a list")
    
    unnamed_trigger_index = 0
    
    for i, trigger_config in enumerate(triggers_config):
        if not isinstance(trigger_config, dict):
            raise TriggerValidationError(
                f"Trigger config at index {i} must be a dictionary"
            )
        
        try:
            # Ensure trigger has a name
            if 'name' not in trigger_config or not trigger_config['name']:
                trigger_config['name'] = f'UnnamedTrigger_{unnamed_trigger_index}'
                unnamed_trigger_index += 1
            
            # Validate condition
            condition = trigger_config.get('condition', '').strip()
            if not condition:
                raise TriggerValidationError(
                    f"Trigger '{trigger_config['name']}' is missing a condition"
                )
            
            # Create actions
            actions = []
            actions_config = trigger_config.get('actions', [])
            if not isinstance(actions_config, list):
                raise TriggerValidationError(
                    f"Actions for trigger '{trigger_config['name']}' must be a list"
                )
            
            for j, action_config in enumerate(actions_config):
                if not action_config or action_config == 'None':
                    continue
                
                if not isinstance(action_config, dict):
                    raise TriggerValidationError(
                        f"Action {j} in trigger '{trigger_config['name']}' must be a dictionary"
                    )
                
                action_name = action_config.get('name', f'unnamed_action_{j}')
                action_type = action_config.get('type', 'TradeAction')
                
                if action_type != 'TradeAction':
                    raise TriggerValidationError(
                        f"Unsupported action type '{action_type}' in trigger "
                        f"'{trigger_config['name']}'. Only 'TradeAction' is supported."
                    )
                
                # Create action
                action = TriggerAction(
                    name=action_name,
                    type=action_type,
                    parameters={
                        k: v for k, v in action_config.items()
                        if k not in ('name', 'type')
                    }
                )
                actions.append(action)
            
            # Validate at least one action exists
            if not actions:
                raise TriggerValidationError(
                    f"Trigger '{trigger_config['name']}' has no valid actions"
                )
            
            # Create and add trigger
            trigger = Trigger(
                name=trigger_config['name'],
                condition=condition,
                actions=actions
            )
            
            trigger_system.add_trigger(trigger)
            logger.debug(f"Added trigger: {trigger.name}")
            
        except TriggerValidationError:
            raise
        except Exception as e:
            raise TriggerValidationError(
                f"Failed to create trigger at index {i}: {e}"
            ) from e


# ===== Strategy Factory =====

def create_strategy(
    strategy_name: str,
    strategy_def: Dict[str, Any]
) -> Type[BaseStrategy]:
    """
    Create a strategy class dynamically from YAML definition.
    
    Args:
        strategy_name: Name of the strategy (used for class name)
        strategy_def: Strategy definition dictionary
        
    Returns:
        A strategy class ready for instantiation
        
    Raises:
        StrategyCreationError: If strategy creation fails
    """
    if not isinstance(strategy_def, dict):
        raise StrategyCreationError("Strategy config must be a dictionary")
    
    if not isinstance(strategy_name, str) or not strategy_name.strip():
        raise StrategyCreationError("Strategy name must be a non-empty string")
    
    try:
        # Create indicator factories
        indicators_config = strategy_def.get('indicators', {})
        if not isinstance(indicators_config, dict):
            raise StrategyCreationError("Indicators config must be a dictionary")
        
        indicator_funs = {}
        parameters = strategy_def.get('parameters', {})
        
        for name, ind_config in indicators_config.items():
            if not isinstance(name, str) or not name.strip():
                raise StrategyCreationError(
                    f"Indicator name must be a non-empty string, got: {name}"
                )
            try:
                indicator_funs[name] = create_indicator(ind_config, parameters)
            except IndicatorCreationError as e:
                raise StrategyCreationError(
                    f"Failed to create indicator '{name}': {e}"
                ) from e
        
        # Validate triggers config
        triggers_config = strategy_def.get('triggers', [])
        if not isinstance(triggers_config, list):
            raise StrategyCreationError("Triggers config must be a list")
        
        # Create the strategy class
        class CustomStrategy(BaseStrategy):
            """Dynamically created strategy class."""
            
            def __init__(self):
                super().__init__()
                self.strategy_name = strategy_name
                self.logger.debug(f"Initialized strategy: {strategy_name}")
            
            def setup_indicators(self) -> None:
                """Set up indicators based on configuration."""
                for ind_name, indicator_fn in indicator_funs.items():
                    try:
                        self.indicators[ind_name] = indicator_fn(self.data)
                        self.logger.debug(f"Created indicator: {ind_name}")
                    except Exception as e:
                        self.logger.error(f"Failed to create indicator '{ind_name}': {e}")
            
            def setup_trigger_system(self) -> None:
                """Set up trigger system based on configuration."""
                try:
                    setup_trigger_system(self.trigger_system, triggers_config)
                except TriggerValidationError as e:
                    raise StrategyCreationError(
                        f"Failed to create trigger system: {e}"
                    ) from e
        
        # Set class name for better debugging
        CustomStrategy.__name__ = strategy_name
        CustomStrategy.__qualname__ = strategy_name
        
        logger.info(f"Created strategy class: {strategy_name}")
        return CustomStrategy
        
    except StrategyCreationError:
        raise
    except Exception as e:
        raise StrategyCreationError(
            f"Unexpected error creating strategy: {e}"
        ) from e


# ===== Validation =====

def validate_strategy_config(config: Dict[str, Any]) -> List[str]:
    """
    Validate a strategy configuration and return issues found.
    
    Args:
        config: Strategy configuration to validate
        
    Returns:
        List of validation error messages (empty if valid)
    """
    issues = []
    
    if not isinstance(config, dict):
        return ["Configuration must be a dictionary"]
    
    # Validate name
    name = config.get('name', '')
    if not isinstance(name, str) or not name.strip():
        issues.append("Strategy name must be a non-empty string")
    
    # Validate indicators
    indicators = config.get('indicators', {})
    if not isinstance(indicators, dict):
        issues.append("Indicators must be a dictionary")
    else:
        for ind_name, ind_config in indicators.items():
            if not isinstance(ind_name, str) or not ind_name.strip():
                issues.append(f"Indicator name '{ind_name}' must be a non-empty string")
            if not isinstance(ind_config, dict):
                issues.append(f"Indicator config for '{ind_name}' must be a dictionary")
            elif 'type' not in ind_config:
                issues.append(f"Indicator '{ind_name}' is missing required 'type' field")
    
    # Validate triggers
    triggers = config.get('triggers', [])
    if not isinstance(triggers, list):
        issues.append("Triggers must be a list")
    else:
        for i, trigger_config in enumerate(triggers):
            if not isinstance(trigger_config, dict):
                issues.append(f"Trigger at index {i} must be a dictionary")
                continue
            
            # Check condition
            condition = trigger_config.get('condition', '')
            if not isinstance(condition, str) or not condition.strip():
                issues.append(f"Trigger at index {i} must have a non-empty condition")
            
            # Check actions
            actions = trigger_config.get('actions', [])
            if not isinstance(actions, list):
                issues.append(f"Actions for trigger at index {i} must be a list")
            elif not any(action for action in actions if action and action != 'None'):
                issues.append(f"Trigger at index {i} must have at least one valid action")
    
    return issues
