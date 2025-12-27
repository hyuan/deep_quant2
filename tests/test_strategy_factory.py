"""Tests for strategy factory."""

import unittest
import backtrader as bt
from strategy.factory import create_indicator, create_strategy, StrategyCreationError


class TestStrategyFactory(unittest.TestCase):
    """Test cases for strategy factory functions."""
    
    def test_create_sma_indicator(self):
        """Test creating an SMA indicator."""
        config = {
            'type': 'SMA',
            'period': 20
        }
        parameters = {}
        
        indicator_fn = create_indicator(config, parameters)
        self.assertIsNotNone(indicator_fn)
        self.assertTrue(callable(indicator_fn))
    
    def test_create_indicator_with_parameter_reference(self):
        """Test creating indicator with parameter reference."""
        config = {
            'type': 'SMA',
            'period': 'sma_period'
        }
        parameters = {
            'sma_period': 15
        }
        
        indicator_fn = create_indicator(config, parameters)
        self.assertIsNotNone(indicator_fn)
    
    def test_create_indicator_missing_type(self):
        """Test creating indicator without type."""
        config = {
            'period': 20
        }
        parameters = {}
        
        with self.assertRaises(Exception):  # Should raise IndicatorCreationError
            create_indicator(config, parameters)
    
    def test_create_indicator_invalid_type(self):
        """Test creating indicator with invalid type."""
        config = {
            'type': 'NonexistentIndicator',
            'period': 20
        }
        parameters = {}
        
        with self.assertRaises(Exception):
            create_indicator(config, parameters)
    
    def test_create_simple_strategy(self):
        """Test creating a simple strategy."""
        strategy_def = {
            'name': 'TestStrategy',
            'indicators': {
                'sma': {
                    'type': 'SMA',
                    'period': 20
                }
            },
            'triggers': [
                {
                    'name': 'test_trigger',
                    'condition': 'close > indicators.sma',
                    'actions': [
                        {
                            'name': 'buy',
                            'type': 'TradeAction',
                            'ticker': 'tickers[0]',
                            'signal': 'Long',
                            'orderType': 'Market'
                        }
                    ]
                }
            ],
            'parameters': {}
        }
        
        strategy_class = create_strategy('TestStrategy', strategy_def)
        self.assertIsNotNone(strategy_class)
        self.assertEqual(strategy_class.__name__, 'TestStrategy')
    
    def test_create_strategy_invalid_config(self):
        """Test creating strategy with invalid config."""
        with self.assertRaises(StrategyCreationError):
            create_strategy('TestStrategy', None)
        
        with self.assertRaises(StrategyCreationError):
            create_strategy('', {})
    
    def test_create_strategy_invalid_indicators(self):
        """Test creating strategy with invalid indicators."""
        strategy_def = {
            'name': 'TestStrategy',
            'indicators': "not a dict",  # Should be dict
            'triggers': [],
            'parameters': {}
        }
        
        with self.assertRaises(StrategyCreationError):
            create_strategy('TestStrategy', strategy_def)
    
    def test_create_strategy_invalid_triggers(self):
        """Test creating strategy with invalid triggers."""
        strategy_def = {
            'name': 'TestStrategy',
            'indicators': {},
            'triggers': "not a list",  # Should be list
            'parameters': {}
        }
        
        with self.assertRaises(StrategyCreationError):
            create_strategy('TestStrategy', strategy_def)


if __name__ == '__main__':
    unittest.main()
