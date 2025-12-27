"""Tests for expression evaluator."""

import unittest
from strategy.expression import ExpressionEvaluator, EvaluationError


class TestExpressionEvaluator(unittest.TestCase):
    """Test cases for the ExpressionEvaluator class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.evaluator = ExpressionEvaluator()
        self.context = {
            'close': 100.0,
            'open': 98.0,
            'high': 105.0,
            'low': 97.0,
            'volume': 1000.0,
            'indicators.sma': 99.0,
            'indicators.rsi': 65.0,
        }
    
    def test_simple_number(self):
        """Test evaluation of simple numbers."""
        self.assertEqual(self.evaluator.evaluate("42", self.context), 42.0)
        self.assertEqual(self.evaluator.evaluate("3.14", self.context), 3.14)
        self.assertEqual(self.evaluator.evaluate("0", self.context), 0.0)
    
    def test_simple_variables(self):
        """Test evaluation of simple variable references."""
        self.assertEqual(self.evaluator.evaluate("close", self.context), 100.0)
        self.assertEqual(self.evaluator.evaluate("open", self.context), 98.0)
        self.assertEqual(self.evaluator.evaluate("high", self.context), 105.0)
        self.assertEqual(self.evaluator.evaluate("low", self.context), 97.0)
        self.assertEqual(self.evaluator.evaluate("volume", self.context), 1000.0)
    
    def test_indicator_variables(self):
        """Test evaluation of indicator variable references."""
        self.assertEqual(self.evaluator.evaluate("indicators.sma", self.context), 99.0)
        self.assertEqual(self.evaluator.evaluate("indicators.rsi", self.context), 65.0)
    
    def test_arithmetic_operations(self):
        """Test basic arithmetic operations."""
        self.assertEqual(self.evaluator.evaluate("10 + 5", self.context), 15.0)
        self.assertEqual(self.evaluator.evaluate("10 - 5", self.context), 5.0)
        self.assertEqual(self.evaluator.evaluate("10 * 5", self.context), 50.0)
        self.assertEqual(self.evaluator.evaluate("10 / 5", self.context), 2.0)
    
    def test_complex_expressions(self):
        """Test complex mathematical expressions."""
        result = self.evaluator.evaluate("(close + open) / 2", self.context)
        self.assertEqual(result, 99.0)  # (100 + 98) / 2
        
        result = self.evaluator.evaluate("high - low", self.context)
        self.assertEqual(result, 8.0)  # 105 - 97
        
        result = self.evaluator.evaluate("close * 1.02", self.context)
        self.assertEqual(result, 102.0)  # 100 * 1.02
    
    def test_order_of_operations(self):
        """Test that order of operations is respected."""
        result = self.evaluator.evaluate("2 + 3 * 4", self.context)
        self.assertEqual(result, 14.0)  # 2 + (3 * 4) = 14
        
        result = self.evaluator.evaluate("(2 + 3) * 4", self.context)
        self.assertEqual(result, 20.0)  # (2 + 3) * 4 = 20
    
    def test_missing_variable(self):
        """Test handling of missing variables."""
        with self.assertRaises(EvaluationError):
            self.evaluator.evaluate("nonexistent", self.context)
    
    def test_invalid_expression(self):
        """Test handling of invalid expressions."""
        with self.assertRaises(EvaluationError):
            self.evaluator.evaluate("close +", self.context)
    
    def test_division_by_zero(self):
        """Test handling of division by zero."""
        with self.assertRaises(EvaluationError):
            self.evaluator.evaluate("close / 0", self.context)


if __name__ == '__main__':
    unittest.main()
