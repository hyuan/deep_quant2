"""Evaluator for boolean condition expressions."""

import logging
from typing import Any, Callable, Dict, Union

from .base_evaluator import BaseEvaluator
from .condition_parser import ConditionParser
from .expression_tokenizer import EvaluationError, ExpressionNode, ParseError


logger = logging.getLogger(__name__)


class ConditionEvaluator(BaseEvaluator[ExpressionNode]):
    """Main class for parsing and evaluating conditions with caching."""
    
    def parse_expression(self, condition_str: str) -> ExpressionNode:
        """
        Parse a condition string into an AST, with caching.
        
        Args:
            condition_str: The condition string to parse
            
        Returns:
            Parsed condition AST
            
        Raises:
            ParseError: If parsing fails
        """
        self._validate_expression_string(condition_str)
        
        cached_ast = self._get_from_cache(condition_str)
        if cached_ast:
            return cached_ast
        
        try:
            tokens = self._tokenizer.tokenize(condition_str)
            parser = ConditionParser(tokens)
            ast = parser.parse()
            
            self._manage_cache(condition_str, ast)
            return ast
        except Exception as e:
            raise ParseError(f"Failed to parse condition '{condition_str}': {e}") from e
    
    def evaluate(
        self,
        condition: Union[Callable[[Dict[str, Any]], bool], str],
        context: Dict[str, Any]
    ) -> bool:
        """
        Evaluate a condition string or callable against the given context.
        
        Args:
            condition: The condition string to evaluate or a callable function
            context: Variable context for evaluation
            
        Returns:
            Boolean evaluation result
            
        Raises:
            EvaluationError: If evaluation fails
        """
        self._validate_context(context)
        
        if callable(condition):
            try:
                return condition(context)
            except Exception as e:
                raise EvaluationError(f"Error executing condition function: {e}") from e
        
        try:
            ast = self.parse_expression(condition)
            result = ast.evaluate(context)
            return bool(result)
        except Exception as e:
            self._logger.error(f"Failed to evaluate condition '{condition}': {e}")
            raise EvaluationError(f"Condition evaluation failed: {e}") from e
