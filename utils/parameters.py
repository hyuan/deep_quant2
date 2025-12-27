"""Parameter mapping and configuration utilities."""

import copy
from typing import Dict, Any


def set_nested_dict_value(d: Dict[str, Any], path: str, value: Any) -> None:
    """
    Set a value in a nested dictionary using a dot-notation path.
    
    Args:
        d: The dictionary to modify
        path: Dot-notation path (e.g., "indicators.sma.period")
        value: The value to set
        
    Example:
        >>> config = {"indicators": {"sma": {"period": 5}}}
        >>> set_nested_dict_value(config, "indicators.sma.period", 10)
        >>> config["indicators"]["sma"]["period"]
        10
    """
    keys = path.split('.')
    current = d
    
    # Navigate to the nested location
    for key in keys[:-1]:
        if key not in current:
            current[key] = {}
        current = current[key]
    
    # Set the value with type inference
    current[keys[-1]] = _infer_type(value, current.get(keys[-1]))


def _infer_type(value: Any, existing_value: Any = None) -> Any:
    """
    Infer the appropriate type for a value based on existing value or content.
    
    Args:
        value: The value to convert
        existing_value: Existing value to match type against
        
    Returns:
        Converted value with appropriate type
    """
    # If value is already not a string, return as-is
    if not isinstance(value, str):
        return value
    
    # Try to match existing value's type
    if existing_value is not None:
        try:
            if isinstance(existing_value, bool):
                return value.lower() in ('true', 'yes', '1', 't', 'y', 'on')
            elif isinstance(existing_value, int):
                return int(value)
            elif isinstance(existing_value, float):
                return float(value)
        except (ValueError, AttributeError):
            pass
    
    # Infer type from the value itself
    try:
        # Try boolean
        if value.lower() in ('true', 'false', 'yes', 'no', '1', '0', 'y', 'n', 'on', 'off'):
            return value.lower() in ('true', 'yes', '1', 't', 'y', 'on')
        
        # Try integer
        if value.lstrip('-').isdigit():
            return int(value)
        
        # Try float
        if value.replace('.', '', 1).replace('-', '', 1).isdigit() and value.count('.') == 1:
            return float(value)
    except (ValueError, AttributeError):
        pass
    
    # Keep as string
    return value


def map_cli_parameters_to_config(config: Dict[str, Any], dynamic_params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Map CLI parameters to configuration, applying parameter mappings if defined.
    
    Args:
        config: Original strategy configuration
        dynamic_params: CLI parameters to apply
        
    Returns:
        Updated strategy configuration (deep copy)
        
    Example:
        >>> config = {"parameters": {"sma_period": "indicators.sma.period"}}
        >>> params = {"sma_period": "10"}
        >>> updated = map_cli_parameters_to_config(config, params)
        >>> updated["indicators"]["sma"]["period"]
        10
    """
    config = copy.deepcopy(config)
    
    # Get parameter mappings from the strategy config
    parameter_mappings = config.get('parameters', {})
    
    # Process each CLI parameter
    for param_name, param_value in dynamic_params.items():
        # Use parameter mapping if available, otherwise use direct path
        param_path = parameter_mappings.get(param_name, param_name)
        set_nested_dict_value(config, param_path, param_value)
    
    return config


def merge_configs(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    """
    Recursively merge two configuration dictionaries.
    
    Args:
        base: Base configuration
        override: Configuration values to override
        
    Returns:
        Merged configuration (deep copy)
    """
    result = copy.deepcopy(base)
    
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = merge_configs(result[key], value)
        else:
            result[key] = copy.deepcopy(value)
    
    return result
