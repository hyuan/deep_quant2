"""Parser for boolean condition expressions."""

import logging

from .base_parser import BaseParser
from .expression_tokenizer import (
    ComparisonNode,
    ExpressionNode,
    LogicalNode,
    LogicalOperator,
    Operator
)


logger = logging.getLogger(__name__)


class ConditionParser(BaseParser):
    """Parses tokenized conditions into an AST."""
    
    def parse(self) -> ExpressionNode:
        """Parse the tokens into an AST."""
        result = self._parse_or_expression()
        if self.position < len(self.tokens):
            raise ValueError(f"Unexpected token: {self.tokens[self.position].value}")
        return result
    
    def _parse_or_expression(self) -> ExpressionNode:
        """Parse OR expressions (lowest precedence)."""
        left = self._parse_and_expression()
        
        while self._current_token() and self._current_token().value == 'or':
            self._consume_token()  # consume 'or'
            right = self._parse_and_expression()
            left = LogicalNode(left, LogicalOperator.OR, right)
        
        return left
    
    def _parse_and_expression(self) -> ExpressionNode:
        """Parse AND expressions (higher precedence than OR)."""
        left = self._parse_comparison_expression()
        
        while self._current_token() and self._current_token().value == 'and':
            self._consume_token()  # consume 'and'
            right = self._parse_comparison_expression()
            left = LogicalNode(left, LogicalOperator.AND, right)
        
        return left
    
    def _parse_comparison_expression(self) -> ExpressionNode:
        """Parse comparison expressions."""
        left = self._parse_additive_expression()
        
        current = self._current_token()
        if current and current.type == 'COMPARISON_OP':
            op_token = self._consume_token()
            right = self._parse_additive_expression()
            
            # Map operator string to enum
            operator_map = {
                '>': Operator.GREATER_THAN,
                '<': Operator.LESS_THAN,
                '>=': Operator.GREATER_EQUAL,
                '<=': Operator.LESS_EQUAL,
                '==': Operator.EQUAL,
                '!=': Operator.NOT_EQUAL,
            }
            
            operator = operator_map[op_token.value]
            return ComparisonNode(left, operator, right)
        
        # If no comparison operator found, check if it's a boolean expression
        if isinstance(left, (LogicalNode, ComparisonNode)):
            return left
        
        # Mathematical expression without comparison is an error
        raise ValueError("Mathematical expression must be part of a comparison")
    
    def _parse_primary_expression(self) -> ExpressionNode:
        """Parse primary expressions with parentheses support."""
        current = self._current_token()
        
        if current and current.type == 'LPAREN':
            self._consume_token()  # consume '('
            
            # Save position for potential backtracking
            saved_position = self.position
            
            try:
                # Try parsing as mathematical expression first
                result = self._parse_additive_expression()
                if not self._current_token() or self._current_token().type != 'RPAREN':
                    raise ValueError("Missing closing parenthesis")
                self._consume_token()  # consume ')'
                return result
            except Exception:
                # Backtrack and try boolean expression
                self.position = saved_position
                result = self._parse_or_expression()
                if not self._current_token() or self._current_token().type != 'RPAREN':
                    raise ValueError("Missing closing parenthesis")
                self._consume_token()  # consume ')'
                return result
        
        # Use parent's implementation for numbers and variables
        return super()._parse_primary_expression()
