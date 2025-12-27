"""Evaluator for mathematical expressions."""

import logging
from typing import Any, Callable, Dict, Union

from .base_evaluator import BaseEvaluator
from .expression_parser import ExpressionParser
from .expression_tokenizer import EvaluationError, ExpressionNode, ParseError


logger = logging.getLogger(__name__)


class ExpressionEvaluator(BaseEvaluator[ExpressionNode]):
    """Evaluator for mathematical expressions (non-boolean)."""
    
    def parse_expression(self, expression_str: str) -> ExpressionNode:
        """
        Parse a mathematical expression string into an AST, with caching.
        
        Args:
            expression_str: The expression string to parse
            
        Returns:
            Parsed expression AST
            
        Raises:
            ParseError: If parsing fails
        """
        self._validate_expression_string(expression_str)
        
        cached_ast = self._get_from_cache(expression_str)
        if cached_ast:
            return cached_ast
        
        try:
            tokens = self._tokenizer.tokenize(expression_str)
            parser = ExpressionParser(tokens)
            ast = parser.parse()
            
            self._manage_cache(expression_str, ast)
            return ast
        except Exception as e:
            raise ParseError(f"Failed to parse expression '{expression_str}': {e}") from e
    
    def evaluate(
        self,
        expression: Union[Callable[[Dict[str, Any]], float], str],
        context: Dict[str, Any]
    ) -> float:
        """
        Evaluate a mathematical expression string or callable against context.
        
        Args:
            expression: The expression string to evaluate or a callable function
            context: Variable context for evaluation
            
        Returns:
            Float evaluation result
            
        Raises:
            EvaluationError: If evaluation fails
        """
        self._validate_context(context)
        
        if callable(expression):
            try:
                return expression(context)
            except Exception as e:
                raise EvaluationError(f"Error executing expression function: {e}") from e
        
        try:
            ast = self.parse_expression(expression)
            result = ast.evaluate(context)
            return float(result)
        except Exception as e:
            self._logger.error(f"Failed to evaluate expression '{expression}': {e}")
            raise EvaluationError(f"Expression evaluation failed: {e}") from e
