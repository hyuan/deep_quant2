"""Trigger system for defining strategy conditions and actions."""

import logging
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

from .expression import ConditionEvaluator, ParseError


logger = logging.getLogger(__name__)


# ===== Exceptions =====

class TriggerSystemError(Exception):
    """Base exception for trigger system errors."""
    pass


class TriggerValidationError(TriggerSystemError):
    """Exception raised when trigger validation fails."""
    pass


# ===== Dataclasses =====

@dataclass
class TriggerAction:
    """Represents an action to be executed when a trigger condition is met."""
    name: str
    type: str  # Must be "TradeAction" for now
    parameters: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate action parameters after initialization."""
        if not self.name or not isinstance(self.name, str):
            raise TriggerValidationError("Action name must be a non-empty string")
        if not isinstance(self.parameters, dict):
            raise TriggerValidationError("Action parameters must be a dictionary")


@dataclass
class Trigger:
    """Represents a trigger with condition and associated actions."""
    name: str
    condition: Callable[[Dict[str, Any]], bool] | str
    actions: List[TriggerAction]
    enabled: bool = True
    
    def __post_init__(self):
        """Validate trigger parameters after initialization."""
        if not self.name or not isinstance(self.name, str):
            raise TriggerValidationError("Trigger name must be a non-empty string")
        if not self.condition or (not isinstance(self.condition, str) and not callable(self.condition)):
            raise TriggerValidationError("Trigger condition must be a non-empty string or callable")
        if not isinstance(self.actions, list) or not self.actions:
            raise TriggerValidationError("Trigger must have at least one action")
        for action in self.actions:
            if not isinstance(action, TriggerAction):
                raise TriggerValidationError("All actions must be TriggerAction instances")


# ===== Trigger System =====

class TriggerSystem:
    """System for managing triggers with condition parsing and validation."""
    
    def __init__(self, max_triggers: int = 100):
        """
        Initialize the trigger system.
        
        Args:
            max_triggers: Maximum number of triggers allowed
        """
        self.triggers: Dict[str, Trigger] = {}
        self.condition_evaluator = ConditionEvaluator()
        self._max_triggers = max_triggers
    
    def add_trigger(self, trigger: Trigger) -> None:
        """
        Add a trigger to the system.
        
        Args:
            trigger: The trigger to add
            
        Raises:
            TriggerValidationError: If trigger validation fails
            TriggerSystemError: If system limits are exceeded
        """
        if not isinstance(trigger, Trigger):
            raise TriggerValidationError("Must provide a Trigger instance")
        
        if len(self.triggers) >= self._max_triggers:
            raise TriggerSystemError(f"Maximum number of triggers ({self._max_triggers}) exceeded")
        
        if trigger.name in self.triggers:
            raise TriggerValidationError(f"Trigger with name '{trigger.name}' already exists")
        
        # Validate condition syntax
        if isinstance(trigger.condition, str):
            try:
                self.condition_evaluator.parse_expression(trigger.condition)
            except ParseError as e:
                raise TriggerValidationError(
                    f"Invalid condition syntax in trigger '{trigger.name}': {e}"
                ) from e
        
        self.triggers[trigger.name] = trigger
        logger.debug(f"Added trigger: {trigger.name}")
    
    def remove_trigger(self, trigger_name: str) -> bool:
        """
        Remove a trigger from the system.
        
        Args:
            trigger_name: Name of the trigger to remove
            
        Returns:
            True if trigger was removed, False if not found
        """
        if not isinstance(trigger_name, str):
            return False
        
        if trigger_name in self.triggers:
            del self.triggers[trigger_name]
            logger.info(f"Removed trigger: {trigger_name}")
            return True
        return False
    
    def enable_trigger(self, trigger_name: str) -> bool:
        """
        Enable a trigger.
        
        Args:
            trigger_name: Name of the trigger to enable
            
        Returns:
            True if successful, False if trigger not found
        """
        if trigger_name in self.triggers:
            self.triggers[trigger_name].enabled = True
            logger.debug(f"Enabled trigger: {trigger_name}")
            return True
        return False
    
    def disable_trigger(self, trigger_name: str) -> bool:
        """
        Disable a trigger.
        
        Args:
            trigger_name: Name of the trigger to disable
            
        Returns:
            True if successful, False if trigger not found
        """
        if trigger_name in self.triggers:
            self.triggers[trigger_name].enabled = False
            logger.debug(f"Disabled trigger: {trigger_name}")
            return True
        return False
    
    def get_trigger(self, trigger_name: str) -> Optional[Trigger]:
        """
        Get a trigger by name.
        
        Args:
            trigger_name: Name of the trigger
            
        Returns:
            Trigger if found, None otherwise
        """
        return self.triggers.get(trigger_name)
    
    def validate_condition(self, condition: str) -> List[str]:
        """
        Validate a condition string for syntax errors.
        
        Args:
            condition: Condition string to validate
            
        Returns:
            List of validation errors (empty if valid)
        """
        errors = []
        try:
            self.condition_evaluator.parse_expression(condition)
        except ParseError as e:
            errors.append(str(e))
        return errors
