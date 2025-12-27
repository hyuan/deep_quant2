"""Base parser with common parsing logic for expressions."""

from typing import List, Optional

from .expression_tokenizer import (
    ExpressionNode,
    MathNode,
    MathOperator,
    NumberNode,
    Token,
    VariableNode
)


class BaseParser:
    """Base parser class with common parsing logic."""
    
    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.position = 0
    
    def _parse_additive_expression(self) -> ExpressionNode:
        """Parse addition and subtraction (lower precedence)."""
        left = self._parse_multiplicative_expression()
        
        while self._current_token() and self._current_token().value in ['+', '-']:
            op_token = self._consume_token()
            right = self._parse_multiplicative_expression()
            
            operator = MathOperator.ADD if op_token.value == '+' else MathOperator.SUBTRACT
            left = MathNode(left, operator, right)
        
        return left
    
    def _parse_multiplicative_expression(self) -> ExpressionNode:
        """Parse multiplication and division (higher precedence)."""
        left = self._parse_primary_expression()
        
        while self._current_token() and self._current_token().value in ['*', '/']:
            op_token = self._consume_token()
            right = self._parse_primary_expression()
            
            operator = MathOperator.MULTIPLY if op_token.value == '*' else MathOperator.DIVIDE
            left = MathNode(left, operator, right)
        
        return left
    
    def _parse_primary_expression(self) -> ExpressionNode:
        """Parse primary expressions (variables, numbers, parenthesized expressions)."""
        current = self._current_token()
        
        if current and current.type == 'LPAREN':
            self._consume_token()  # consume '('
            result = self._parse_additive_expression()
            if not self._current_token() or self._current_token().type != 'RPAREN':
                raise ValueError("Missing closing parenthesis")
            self._consume_token()  # consume ')'
            return result
        
        if current and current.type == 'NUMBER':
            token = self._consume_token()
            return NumberNode(float(token.value))
        
        if current and current.type in ['IDENTIFIER', 'BRACKET_VAR', 'DOT_VAR']:
            token = self._consume_token()
            return VariableNode(token.value)
        
        raise ValueError(f"Unexpected token: {current.value if current else 'EOF'}")
    
    def _current_token(self) -> Optional[Token]:
        """Get the current token without consuming it."""
        if self.position < len(self.tokens):
            return self.tokens[self.position]
        return None
    
    def _consume_token(self) -> Optional[Token]:
        """Consume and return the current token."""
        if self.position < len(self.tokens):
            token = self.tokens[self.position]
            self.position += 1
            return token
        return None
