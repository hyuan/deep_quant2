"""Tests for condition evaluator."""

import unittest
from strategy.expression import ConditionEvaluator, EvaluationError


class TestConditionEvaluator(unittest.TestCase):
    """Test cases for the ConditionEvaluator class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.evaluator = ConditionEvaluator()
        self.context = {
            'price': 150.0,
            'close': 100.0,
            'open': 98.0,
            'high': 105.0,
            'low': 97.0,
            'volume': 1000.0,
            'indicators.sma': 99.0,
            'indicators.rsi': 65.0,
            'ma_50': 100.0,
            'ma_200': 95.0,
        }
    
    def test_simple_comparisons(self):
        """Test simple comparison operations."""
        self.assertTrue(self.evaluator.evaluate("price > 100", self.context))
        self.assertTrue(self.evaluator.evaluate("price < 200", self.context))
        self.assertTrue(self.evaluator.evaluate("price >= 150", self.context))
        self.assertTrue(self.evaluator.evaluate("price <= 150", self.context))
        self.assertTrue(self.evaluator.evaluate("price == 150", self.context))
        self.assertTrue(self.evaluator.evaluate("price != 100", self.context))
    
    def test_variable_comparison(self):
        """Test comparison between variables."""
        self.assertTrue(self.evaluator.evaluate("ma_50 > ma_200", self.context))
        self.assertTrue(self.evaluator.evaluate("close > open", self.context))
        self.assertTrue(self.evaluator.evaluate("high > low", self.context))
    
    def test_indicator_comparisons(self):
        """Test comparisons with indicators."""
        self.assertTrue(self.evaluator.evaluate("indicators.sma < close", self.context))
        self.assertTrue(self.evaluator.evaluate("indicators.rsi > 50", self.context))
    
    def test_logical_and(self):
        """Test logical AND operations."""
        self.assertTrue(
            self.evaluator.evaluate("price > 100 and price < 200", self.context)
        )
        self.assertFalse(
            self.evaluator.evaluate("price > 100 and price > 200", self.context)
        )
    
    def test_logical_or(self):
        """Test logical OR operations."""
        # price is 150, so price < 100 is False, but price > 100 is True
        # Therefore the second condition should succeed
        self.assertTrue(
            self.evaluator.evaluate("price < 100 or price > 100", self.context)
        )
        self.assertTrue(
            self.evaluator.evaluate("price > 100 or price > 200", self.context)
        )
        self.assertFalse(
            self.evaluator.evaluate("price > 200 or price < 50", self.context)
        )
    
    def test_complex_conditions(self):
        """Test complex logical conditions."""
        # Test: (price > 100 and volume > 500) or indicators.rsi < 30
        condition = "(price > 100 and volume > 500) or indicators.rsi < 30"
        self.assertTrue(self.evaluator.evaluate(condition, self.context))
        
        # Test: close > open and high > close and low < open
        condition = "close > open and high > close and low < open"
        self.assertTrue(self.evaluator.evaluate(condition, self.context))
    
    def test_expression_in_condition(self):
        """Test conditions with mathematical expressions."""
        self.assertTrue(
            self.evaluator.evaluate("close * 1.02 > 100", self.context)
        )
        self.assertTrue(
            self.evaluator.evaluate("(high + low) / 2 > 100", self.context)
        )
    
    def test_missing_variable(self):
        """Test handling of missing variables."""
        with self.assertRaises(EvaluationError):
            self.evaluator.evaluate("nonexistent > 100", self.context)
    
    def test_invalid_condition(self):
        """Test handling of invalid conditions."""
        with self.assertRaises(EvaluationError):
            self.evaluator.evaluate("price >", self.context)


if __name__ == '__main__':
    unittest.main()
