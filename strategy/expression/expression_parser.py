"""Parser for mathematical expressions (non-boolean)."""

from .base_parser import BaseParser
from .expression_tokenizer import ExpressionNode


class ExpressionParser(BaseParser):
    """Parser specifically for mathematical expressions."""
    
    def parse(self) -> ExpressionNode:
        """Parse the tokens into a mathematical expression AST."""
        result = self._parse_additive_expression()
        if self.position < len(self.tokens):
            raise ValueError(f"Unexpected token: {self.tokens[self.position].value}")
        return result
