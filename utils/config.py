"""Configuration utilities for loading and saving strategy definitions."""

import logging
from pathlib import Path
from typing import Dict, Any, Optional, Tuple

import yaml
import backtrader as bt


logger = logging.getLogger(__name__)


def load_strategy_def(strategy_name: str) -> Dict[str, Any]:
    """
    Load a strategy definition from a YAML file.
    
    Args:
        strategy_name: Name of the strategy
        
    Returns:
        Strategy definition dictionary. Returns empty dict if not found.
    """
    strategies_dir = Path(__file__).parent.parent / 'strategies'
    
    # Try both .yaml and .yml extensions
    for ext in ['.yaml', '.yml']:
        strategy_file = strategies_dir / f"{strategy_name}{ext}"
        if strategy_file.exists():
            with open(strategy_file, 'r') as f:
                strategy_def = yaml.safe_load(f)
            logger.info(f"Loaded strategy definition from {strategy_file}")
            return strategy_def or {}
    
    logger.debug(f"Strategy file for {strategy_name} not found in {strategies_dir}")
    return {}


def save_strategy_def(strategy_name: str, strategy_def: Dict[str, Any]) -> Path:
    """
    Save a strategy definition to a YAML file.
    
    Args:
        strategy_name: Name of the strategy
        strategy_def: Strategy definition dictionary
        
    Returns:
        Path to the saved strategy file
    """
    strategies_dir = Path(__file__).parent.parent / 'strategies'
    strategies_dir.mkdir(parents=True, exist_ok=True)
    
    strategy_file = strategies_dir / f"{strategy_name}.yaml"
    with open(strategy_file, 'w') as f:
        yaml.dump(strategy_def, f, default_flow_style=False, sort_keys=False)
    
    logger.info(f"Saved strategy definition to {strategy_file}")
    return strategy_file


def load_runtime_config(config_path: str) -> Dict[str, Any]:
    """
    Load runtime configuration from a YAML file.
    
    Args:
        config_path: Path to the configuration file
        
    Returns:
        Configuration dictionary
    """
    config_file = Path(config_path)
    if not config_file.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
    
    with open(config_file, 'r') as f:
        config = yaml.safe_load(f)
    
    logger.info(f"Loaded runtime configuration from {config_file}")
    return config or {}


def setup_sizer(sizer_config: Optional[Dict[str, Any]]) -> Tuple[type, Dict[str, Any]]:
    """
    Set up position sizing based on configuration.
    
    Args:
        sizer_config: Sizer configuration dictionary with format:
            {"SizerName": {"param1": value1, ...}}
            
    Returns:
        Tuple of (sizer_class, sizer_params)
    """
    if not sizer_config:
        logger.warning('No sizer configuration found, using AllInSizerInt')
        return bt.sizers.AllInSizerInt, {}
    
    # Extract sizer name and parameters
    sizer_name = next(iter(sizer_config))
    sizer_params = sizer_config[sizer_name] or {}
    
    # Map sizer name to Backtrader class
    sizer_map = {
        'PercentSizerInt': bt.sizers.PercentSizerInt,
        'AllInSizerInt': bt.sizers.AllInSizerInt,
        'FixedSize': bt.sizers.FixedSize,
    }
    
    sizer_type = sizer_map.get(sizer_name)
    if sizer_type is None:
        logger.warning(f'Unknown sizer type: {sizer_name}, using AllInSizerInt')
        return bt.sizers.AllInSizerInt, {}
    
    logger.info(f"Using sizer: {sizer_name} with params: {sizer_params}")
    return sizer_type, sizer_params


def setup_logging(level: int = logging.INFO, log_file: Optional[str] = 'backtest.log') -> None:
    """
    Setup logging configuration.
    
    Args:
        level: Logging level (default: INFO)
        log_file: Path to log file (default: 'backtest.log'). Set to None to disable file logging.
    """
    handlers = [logging.StreamHandler()]
    
    if log_file:
        handlers.append(logging.FileHandler(log_file))
    
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=handlers
    )
    
    logger.info("Logging initialized")
