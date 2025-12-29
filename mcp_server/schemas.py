"""Pydantic schemas for MCP server responses."""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class JobStatus(str, Enum):
    """Status of an async job."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class StrategyInfo(BaseModel):
    """Summary information about a strategy."""
    name: str
    file_path: str
    has_indicators: bool
    indicator_count: int
    trigger_count: int
    parameter_count: int


class StrategyDefinition(BaseModel):
    """Full strategy definition."""
    name: str
    yaml_content: str
    parsed: Dict[str, Any]


class ValidationResult(BaseModel):
    """Result of strategy validation."""
    is_valid: bool
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)


class BacktestJob(BaseModel):
    """Information about a backtest job."""
    job_id: str
    status: JobStatus
    strategy: str
    tickers: str
    start_date: str
    end_date: str
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error: Optional[str] = None
    result: Optional[Dict[str, Any]] = None


class BacktestResult(BaseModel):
    """Result of a completed backtest."""
    strategy: str
    tickers: str
    start_date: str
    end_date: str
    initial_value: float
    final_value: float
    profit: float
    profit_percent: float
    sharpe_ratio: Optional[float] = None
    max_drawdown: Optional[float] = None
    sqn: Optional[float] = None
    total_trades: Optional[int] = None


class IndicatorInfo(BaseModel):
    """Information about an available indicator."""
    name: str
    source: str  # 'custom' or 'backtrader'
    description: Optional[str] = None
    parameters: List[str] = Field(default_factory=list)


class MarketDataResult(BaseModel):
    """Result of market data fetch."""
    ticker: str
    start_date: str
    end_date: str
    file_path: str
    rows: int
    cached: bool


class RuntimeConfig(BaseModel):
    """Runtime configuration for backtest."""
    name: str
    file_path: str
    strategy: str
    tickers: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
