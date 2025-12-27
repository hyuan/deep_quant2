"""Backtrader utility functions."""

import logging
from typing import Optional

import backtrader as bt


logger = logging.getLogger(__name__)

# Cache for strategy classes
_strategy_class_cache = {}


def find_strategy_class(strategy_name: str) -> Optional[type]:
    """
    Find and return the strategy class by name.
    
    Searches in the strategy_v2 module for pre-implemented strategies.
    Supports both simple names and fully qualified names (e.g., "module.ClassName").
    
    Args:
        strategy_name: The name of the strategy class to find
        
    Returns:
        The strategy class if found, None otherwise
        
    Raises:
        ValueError: If strategy_name is a qualified name but import fails
    """
    # Check cache first
    if strategy_name in _strategy_class_cache:
        return _strategy_class_cache[strategy_name]
    
    # Handle fully qualified names (e.g., "strategy_v2.ExampleStrategy")
    if '.' in strategy_name:
        module_name, class_name = strategy_name.rsplit('.', 1)
        try:
            module = __import__(module_name, fromlist=[class_name])
            strategy_class = getattr(module, class_name)
            
            if not issubclass(strategy_class, bt.Strategy):
                raise ValueError(f"{strategy_name} is not a valid Backtrader Strategy class")
            
            _strategy_class_cache[strategy_name] = strategy_class
            logger.info(f"Found strategy class: {strategy_name}")
            return strategy_class
        except (ImportError, AttributeError) as e:
            raise ValueError(f"Failed to import strategy class '{strategy_name}': {e}") from e
    
    # Try to find in strategy_v2 module
    try:
        import strategy_v2
        if hasattr(strategy_v2, strategy_name):
            strategy_class = getattr(strategy_v2, strategy_name)
            if issubclass(strategy_class, bt.Strategy):
                _strategy_class_cache[strategy_name] = strategy_class
                logger.info(f"Found strategy class in strategy_v2: {strategy_name}")
                return strategy_class
    except ImportError:
        logger.debug("strategy_v2 module not found")
    
    logger.debug(f"Strategy class '{strategy_name}' not found")
    return None


def explain_order_status(order: bt.Order) -> str:
    """
    Explain the order status in human-readable form.
    
    Args:
        order: The Backtrader order object
        
    Returns:
        Human-readable order status description
    """
    status_name = order.getstatusname()
    
    if order.status in [order.Completed]:
        return f"Order Status: {status_name} - Order completed successfully"
    elif order.status in [order.Margin]:
        return f"Order Status: {status_name} - Order cancelled due to insufficient margin"
    elif order.status in [order.Rejected]:
        return f"Order Status: {status_name} - Order rejected by broker"
    elif order.status in [order.Canceled, order.Cancelled]:
        return f"Order Status: {status_name} - Order cancelled"
    elif order.status in [order.Expired]:
        return f"Order Status: {status_name} - Order expired"
    elif status_name:
        return f"Order Status: {status_name}"
    else:
        return f"Unknown order status: {order.status}"


def describe_order(order: bt.Order) -> str:
    """
    Describe the order with full details.
    
    Args:
        order: The Backtrader order object
        
    Returns:
        Detailed order description
    """
    return (
        f"Order Status: {order.getstatusname()}, "
        f"Type: {order.getordername()}, "
        f"Price: {order.price:.2f}, "
        f"Size: {order.size}, "
        f"Created: {bt.num2date(order.created.dt).strftime('%Y-%m-%d')}"
    )


def format_price(price: float) -> str:
    """Format price for display."""
    return f"${price:,.2f}"


def format_percentage(value: float) -> str:
    """Format percentage for display."""
    return f"{value:.2f}%"
