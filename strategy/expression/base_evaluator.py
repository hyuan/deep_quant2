"""Base evaluator class with caching and common logic."""

import logging
from typing import Any, Dict, Generic, Optional, TypeVar

from .expression_tokenizer import ExpressionTokenizer, EvaluationError, ParseError


T = TypeVar('T')


class BaseEvaluator(Generic[T]):
    """Base evaluator class with common caching and parsing logic."""
    
    def __init__(self, cache_size: int = 1000):
        """
        Initialize the base evaluator.
        
        Args:
            cache_size: Maximum number of cached expressions
        """
        self._expression_cache: Dict[str, T] = {}
        self._cache_size = cache_size
        self._tokenizer = ExpressionTokenizer()
        self._logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    def _manage_cache(self, expression_str: str, ast: T) -> None:
        """Manage cache size and store the AST."""
        if len(self._expression_cache) >= self._cache_size:
            # Remove oldest entry (simple FIFO)
            oldest_key = next(iter(self._expression_cache))
            del self._expression_cache[oldest_key]
        
        self._expression_cache[expression_str] = ast
    
    def _get_from_cache(self, expression_str: str) -> Optional[T]:
        """Get AST from cache if it exists."""
        return self._expression_cache.get(expression_str)
    
    def _validate_expression_string(self, expression_str: str) -> None:
        """Validate the expression string."""
        if not isinstance(expression_str, str) or not expression_str.strip():
            raise ParseError("Expression string cannot be empty")
    
    def _validate_context(self, context: Dict[str, Any]) -> None:
        """Validate the evaluation context."""
        if not isinstance(context, dict):
            raise EvaluationError("Context must be a dictionary")
    
    def clear_cache(self) -> None:
        """Clear the expression cache."""
        self._expression_cache.clear()
        self._logger.debug("Expression cache cleared")
