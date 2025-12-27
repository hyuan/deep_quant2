"""Expression parsing, tokenization and AST nodes."""

import logging
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Union


logger = logging.getLogger(__name__)


# ===== Exceptions =====

class ParserError(Exception):
    """Base exception for parser errors."""
    pass


class TokenizeError(ParserError):
    """Exception raised when tokenization fails."""
    pass


class ParseError(ParserError):
    """Exception raised when parsing fails."""
    pass


class EvaluationError(ParserError):
    """Exception raised when evaluation fails."""
    pass


# ===== Operators =====

class Operator(Enum):
    """Comparison operators."""
    GREATER_THAN = ">"
    LESS_THAN = "<"
    GREATER_EQUAL = ">="
    LESS_EQUAL = "<="
    EQUAL = "=="
    NOT_EQUAL = "!="


class LogicalOperator(Enum):
    """Logical operators."""
    AND = "and"
    OR = "or"


class MathOperator(Enum):
    """Mathematical operators."""
    ADD = "+"
    SUBTRACT = "-"
    MULTIPLY = "*"
    DIVIDE = "/"


# ===== Token =====

@dataclass
class Token:
    """Represents a token in an expression string."""
    type: str           # Token type (e.g., 'NUMBER', 'IDENTIFIER')
    value: str          # Actual string value
    position: int       # Position in original string


# ===== AST Nodes =====

class ExpressionNode(ABC):
    """Abstract base class for all AST nodes."""
    
    @abstractmethod
    def evaluate(self, context: Dict[str, Any]) -> Union[bool, float]:
        """
        Evaluate the node given a context.
        
        Args:
            context: Dictionary containing variable values
            
        Returns:
            The evaluation result
            
        Raises:
            EvaluationError: If evaluation fails
        """
        pass


class ComparisonNode(ExpressionNode):
    """Node for comparison operations like 'price > 100'."""
    
    def __init__(self, left: ExpressionNode, operator: Operator, right: ExpressionNode):
        self.left = left
        self.operator = operator
        self.right = right
    
    def evaluate(self, context: Dict[str, Any]) -> bool:
        """Evaluate the comparison."""
        try:
            left_value = self.left.evaluate(context)
            right_value = self.right.evaluate(context)
            
            if self.operator == Operator.GREATER_THAN:
                return left_value > right_value
            elif self.operator == Operator.LESS_THAN:
                return left_value < right_value
            elif self.operator == Operator.GREATER_EQUAL:
                return left_value >= right_value
            elif self.operator == Operator.LESS_EQUAL:
                return left_value <= right_value
            elif self.operator == Operator.EQUAL:
                return left_value == right_value
            elif self.operator == Operator.NOT_EQUAL:
                return left_value != right_value
            
            raise EvaluationError(f"Unknown operator: {self.operator}")
        except EvaluationError:
            raise
        except Exception as e:
            raise EvaluationError(f"Comparison evaluation failed: {e}") from e


class LogicalNode(ExpressionNode):
    """Node for logical operations like 'AND' and 'OR'."""
    
    def __init__(self, left: ExpressionNode, operator: LogicalOperator, right: ExpressionNode):
        self.left = left
        self.operator = operator
        self.right = right
    
    def evaluate(self, context: Dict[str, Any]) -> bool:
        """Evaluate the logical operation."""
        try:
            if self.operator == LogicalOperator.AND:
                return bool(self.left.evaluate(context)) and bool(self.right.evaluate(context))
            elif self.operator == LogicalOperator.OR:
                return bool(self.left.evaluate(context)) or bool(self.right.evaluate(context))
            
            raise EvaluationError(f"Unknown logical operator: {self.operator}")
        except EvaluationError:
            raise
        except Exception as e:
            raise EvaluationError(f"Logical evaluation failed: {e}") from e


class VariableNode(ExpressionNode):
    """Node for variable references with support for dot and bracket notation."""
    
    def __init__(self, name: str):
        if not name:
            raise ValueError("Variable name cannot be empty")
        self.name = name
    
    def evaluate(self, context: Dict[str, Any]) -> float:
        """Evaluate the variable reference."""
        # Simple variable lookup
        if self.name in context:
            try:
                return float(context[self.name])
            except (ValueError, TypeError) as e:
                raise EvaluationError(
                    f"Cannot convert variable '{self.name}' to float: {e}"
                ) from e
        
        # Complex path (dot/bracket notation)
        parts = self._build_parts(self.name)
        if len(parts) > 1:
            strategy = context.get("strategy", {})
            current = self._evaluate_path(strategy, parts)
            return float(current)
        
        raise EvaluationError(f"Variable '{self.name}' not found in context")
    
    def _build_parts(self, name: str) -> List[Union[str, List]]:
        """
        Split variable name into parts for evaluation.
        
        Examples:
            'indicators.test_sma.lines.sma' → ['indicators', 'test_sma', 'lines', 'sma']
            'indicators.test_sma[0]' → ['indicators', 'test_sma', [0]]
            'datas[0].close' → ['datas', [0], 'close']
        """
        if not name:
            return []
        
        parts = []
        i = 0
        current_part = ""
        
        while i < len(name):
            char = name[i]
            
            if char == '.':
                if current_part:
                    parts.append(current_part)
                    current_part = ""
            elif char == '[':
                if current_part:
                    parts.append(current_part)
                    current_part = ""
                
                # Extract bracket content
                bracket_content = ""
                bracket_count = 1
                i += 1
                
                while i < len(name) and bracket_count > 0:
                    if name[i] == '[':
                        bracket_count += 1
                    elif name[i] == ']':
                        bracket_count -= 1
                    
                    if bracket_count > 0:
                        bracket_content += name[i]
                    i += 1
                
                # Process bracket content
                if bracket_content.isdigit():
                    parts.append([int(bracket_content)])
                else:
                    # Recursive parsing for complex expressions
                    nested_parts = self._build_parts(bracket_content)
                    parts.append(nested_parts)
                
                i -= 1
            else:
                current_part += char
            
            i += 1
        
        if current_part:
            parts.append(current_part)
        
        return parts
    
    def _evaluate_path(self, context: Any, parts: List[Union[str, List]]) -> Any:
        """Evaluate a path through nested structures."""
        if not parts:
            raise EvaluationError("Variable name cannot be empty")
        
        current = context
        for part in parts:
            if isinstance(part, list):
                current = self._evaluate_path(current, part)
            else:
                current = self._evaluate_name(current, part)
        
        return current
    
    def _evaluate_name(self, context: Any, name: str) -> Any:
        """Evaluate a single name in the context."""
        if name is None or name == "":
            raise EvaluationError("Variable name cannot be empty")
        
        if isinstance(name, int):
            if isinstance(context, (list, tuple)) and 0 <= name < len(context):
                return context[name]
            raise EvaluationError(f"Index '{name}' out of range")
        
        if hasattr(context, name):
            return getattr(context, name)
        elif isinstance(context, dict) and name in context:
            return context[name]
        else:
            raise EvaluationError(f"Variable '{self.name}' not found in context")


class NumberNode(ExpressionNode):
    """Node for numeric literals."""
    
    def __init__(self, value: float):
        self.value = value
    
    def evaluate(self, context: Dict[str, Any]) -> float:
        """Return the numeric value."""
        return self.value


class MathNode(ExpressionNode):
    """Node for mathematical operations."""
    
    def __init__(self, left: ExpressionNode, operator: MathOperator, right: ExpressionNode):
        self.left = left
        self.operator = operator
        self.right = right
    
    def evaluate(self, context: Dict[str, Any]) -> float:
        """Evaluate the mathematical operation."""
        try:
            left_value = self.left.evaluate(context)
            right_value = self.right.evaluate(context)
            
            if self.operator == MathOperator.ADD:
                return left_value + right_value
            elif self.operator == MathOperator.SUBTRACT:
                return left_value - right_value
            elif self.operator == MathOperator.MULTIPLY:
                return left_value * right_value
            elif self.operator == MathOperator.DIVIDE:
                if right_value == 0:
                    raise EvaluationError("Division by zero")
                return left_value / right_value
            
            raise EvaluationError(f"Unknown math operator: {self.operator}")
        except EvaluationError:
            raise
        except Exception as e:
            raise EvaluationError(f"Mathematical evaluation failed: {e}") from e


# ===== Tokenizer =====

class ExpressionTokenizer:
    """Tokenizes expression strings into manageable tokens."""
    
    TOKEN_PATTERNS = [
        ('LPAREN', r'\('),
        ('RPAREN', r'\)'),
        ('COMPARISON_OP', r'>=|<=|==|!=|>|<'),
        ('LOGICAL_OP', r'\b(and|or)\b'),
        ('MATH_OP', r'[+\-*/]'),
        ('NUMBER', r'\d+\.?\d*'),
        ('BRACKET_VAR', r'[a-zA-Z_][a-zA-Z0-9_]*\[[a-zA-Z_][a-zA-Z0-9_]*\]'),
        ('DOT_VAR', r'[a-zA-Z_][a-zA-Z0-9_]*(\.[a-zA-Z_][a-zA-Z0-9_]*|\[\d+\])+'),
        ('IDENTIFIER', r'[a-zA-Z_][a-zA-Z0-9_]*'),
        ('WHITESPACE', r'\s+'),
    ]
    
    def tokenize(self, expression: str) -> List[Token]:
        """
        Tokenize an expression string.
        
        Args:
            expression: The expression string to tokenize
            
        Returns:
            List of tokens
            
        Raises:
            TokenizeError: If tokenization fails
        """
        if not isinstance(expression, str):
            raise TokenizeError("Expression must be a string")
        
        tokens = []
        position = 0
        
        while position < len(expression):
            match_found = False
            
            for token_type, pattern in self.TOKEN_PATTERNS:
                regex = re.compile(pattern)
                match = regex.match(expression, position)
                
                if match:
                    value = match.group(0)
                    if token_type != 'WHITESPACE':
                        tokens.append(Token(token_type, value, position))
                    position = match.end()
                    match_found = True
                    break
            
            if not match_found:
                raise TokenizeError(
                    f"Invalid character at position {position}: '{expression[position]}'"
                )
        
        return tokens
