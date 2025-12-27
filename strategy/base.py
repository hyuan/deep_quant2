"""Base strategy class with trigger system integration."""

import logging
from typing import Any, Callable, Dict, List, Optional

import backtrader as bt

from .expression import ConditionEvaluator, ExpressionEvaluator, EvaluationError
from .trigger_system import Trigger, TriggerAction, TriggerSystem


logger = logging.getLogger(__name__)


# ===== Exceptions =====

class StrategyError(Exception):
    """Base exception for strategy errors."""
    pass


class OrderExecutionError(StrategyError):
    """Exception raised when order execution fails."""
    pass


# ===== Base Strategy =====

class BaseStrategy(bt.Strategy):
    """Base strategy class implementing trigger-based trading logic."""
    
    params = (
        ('optimizing', False),
        ('optimizing_param', ''),
    )
    
    def __init__(self):
        super().__init__()
        
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        
        # Core components
        self.indicators: Dict[str, Any] = {}
        self.condition_evaluator = ConditionEvaluator()
        self.expression_evaluator = ExpressionEvaluator()
        self.trigger_system = TriggerSystem()
        
        # Order and trigger tracking
        self.trigger_orders: Dict[str, Dict[str, Optional[bt.Order]]] = {}
        self.pending_actions: Dict[str, List[str]] = {}
        self.active_triggers: set[str] = set()
        
        # Testing and debugging
        self.executed_actions: List[Dict[str, Any]] = []
        self.executed_triggers: List[Dict[str, Any]] = []
        
        # Setup indicators and triggers
        try:
            self.setup_indicators()
        except Exception as e:
            raise StrategyError(f"Indicator setup failed: {e}") from e
        
        try:
            self.setup_trigger_system()
        except Exception as e:
            raise StrategyError(f"Trigger system setup failed: {e}") from e
        
        self.logger.info(f"Initialized {self.__class__.__name__}")
    
    # ===== Abstract Methods (Override in subclasses) =====
    
    def setup_indicators(self) -> None:
        """Set up technical indicators. Override in subclasses."""
        pass
    
    def setup_trigger_system(self) -> None:
        """Set up triggers. Override in subclasses."""
        pass
    
    # ===== Core Strategy Methods =====
    
    def next(self) -> None:
        """Strategy execution logic called for each bar."""
        try:
            for trigger_name, trigger in self.trigger_system.triggers.items():
                if not trigger.enabled:
                    continue
                
                # Skip if trigger is already active
                if trigger.name in self.active_triggers:
                    continue
                
                try:
                    if self.test_condition(trigger.condition):
                        self.execute_trigger_actions(trigger)
                except Exception as e:
                    self.logger.error(f"Error processing trigger '{trigger_name}': {e}")
        except Exception as e:
            self.logger.error(f"Error in strategy next(): {e}")
    
    def stop(self) -> None:
        """Called when the strategy stops."""
        try:
            if self.p.optimizing:
                self.logger.info(
                    f"({self.p.optimizing_param} "
                    f"{getattr(self.params, self.p.optimizing_param, 'N/A')}) "
                    f"Ending Value: {self.broker.getvalue():.2f}"
                )
            else:
                self.logger.info(f"Strategy stopped. Final value: {self.broker.getvalue():.2f}")
        except Exception as e:
            self.logger.error(f"Error in strategy stop: {e}")
    
    # ===== Order Notifications =====
    
    def notify_order(self, order: bt.Order) -> None:
        """Called when an order status changes."""
        if order.status in [bt.Order.Submitted, bt.Order.Accepted]:
            return
        
        if order.status == bt.Order.Completed:
            self._handle_completed_order(order)
        elif order.status in [bt.Order.Canceled, bt.Order.Margin, bt.Order.Rejected, bt.Order.Expired]:
            self._handle_failed_order(order)
    
    def notify_trade(self, trade: bt.Trade) -> None:
        """Called when a trade is completed."""
        if not trade.isclosed:
            return
        
        self.logger.info(f"TRADE PROFIT - Gross: {trade.pnl:.2f}, Net: {trade.pnlcomm:.2f}")
    
    # ===== Condition and Expression Evaluation =====
    
    def test_condition(self, condition: Callable | str) -> bool:
        """
        Test a condition against current market data.
        
        Args:
            condition: Condition string or callable to evaluate
            
        Returns:
            True if condition is met, False otherwise
        """
        try:
            context = self._build_context()
            return self.condition_evaluator.evaluate(condition, context)
        except Exception as e:
            self.logger.error(f"Error evaluating condition: {e}")
            return False
    
    def evaluate_expression(self, expression: Callable | str) -> float:
        """
        Evaluate a mathematical expression.
        
        Args:
            expression: Expression string or callable to evaluate
            
        Returns:
            Evaluated result as float
        """
        try:
            context = self._build_context()
            return self.expression_evaluator.evaluate(expression, context)
        except Exception as e:
            self.logger.error(f"Error evaluating expression: {e}")
            raise EvaluationError(f"Expression evaluation failed: {e}") from e
    
    def _build_context(self) -> Dict[str, Any]:
        """Build the evaluation context with current market data and indicators."""
        data = self.datas[0]
        context = {
            'strategy': self,
            'open': float(data.open[0]),
            'high': float(data.high[0]),
            'low': float(data.low[0]),
            'close': float(data.close[0]),
            'volume': float(data.volume[0]),
            'datas': self.datas,
            'tickers': self.datas,
        }
        
        # Add indicators with their current values (not the objects)
        for name, indicator in self.indicators.items():
            try:
                value = self._get_indicator_value(indicator)
                if value is not None:
                    context[f'indicators.{name}'] = value
            except Exception as e:
                self.logger.error(f"Failed to add indicator '{name}' to context: {e}")
        
        return context
    
    def _get_indicator_value(self, indicator: Any) -> Optional[float]:
        """Safely extract current value from an indicator.
        
        Args:
            indicator: The indicator to extract value from
            
        Returns:
            Float value or None if extraction fails
        """
        try:
            if hasattr(indicator, '__len__') and len(indicator) > 0:
                return float(indicator[0])
            elif hasattr(indicator, '__getitem__'):
                return float(indicator[0])
            else:
                return float(indicator)
        except (IndexError, TypeError, AttributeError, ValueError):
            return None
    
    # ===== Trigger Execution =====
    
    def execute_trigger_actions(self, trigger: Trigger) -> None:
        """
        Execute all actions for a triggered condition.
        
        Args:
            trigger: The trigger to execute
        """
        self.logger.info(f"Trigger activated: {trigger.name}")
        self.active_triggers.add(trigger.name)
        
        # Record trigger execution
        self.executed_triggers.append({
            'name': trigger.name,
            'date': self.datas[0].datetime.date(0).isoformat(),
        })
        
        # Execute first action immediately
        if trigger.actions:
            first_action = trigger.actions[0]
            self.execute_action(first_action, trigger_name=trigger.name)
            
            # Queue remaining actions
            if len(trigger.actions) > 1:
                self.pending_actions[trigger.name] = [a.name for a in trigger.actions[1:]]
    
    def execute_action(
        self,
        action: TriggerAction,
        data: Optional[bt.AbstractDataBase] = None,
        trigger_name: Optional[str] = None
    ) -> Optional[bt.Order]:
        """
        Execute a trading action.
        
        Args:
            action: The action to execute
            data: Data feed to use (defaults to primary)
            trigger_name: Name of the trigger (for tracking)
            
        Returns:
            Created order or None if failed
        """
        if not isinstance(action, TriggerAction):
            raise OrderExecutionError("Invalid action type")
        
        data = data or self.datas[0]
        
        try:
            params = self._validate_action_parameters(action.parameters)
            ticker_data = self._get_ticker_data(params.get('ticker', 'default'))
            position = self.broker.getposition(ticker_data)
            
            order = self._create_order(action, ticker_data, position, params)
            
            if order and trigger_name:
                self._track_order(trigger_name, action.name, order)
            
            return order
        except Exception as e:
            self.logger.error(f"Failed to execute action '{action.name}': {e}")
            raise OrderExecutionError(f"Action execution failed: {e}") from e
    
    # ===== Order Creation =====
    
    def _create_order(
        self,
        action: TriggerAction,
        ticker_data: bt.AbstractDataBase,
        position: bt.Position,
        params: Dict[str, Any]
    ) -> Optional[bt.Order]:
        """Create and submit an order."""
        signal = params['signal']
        order_type = params['orderType']
        
        # Check conditions
        if signal == 'Long':
            if self.broker.get_cash() <= ticker_data.close[0] or position.size > 0:
                self.logger.info("Cannot execute Long: insufficient cash or already long")
                return None
        elif signal == 'Short':
            if position.size <= 0:
                self.logger.info("Cannot execute Short: no position to close")
                return None
        
        # Build order parameters
        order_params = self._build_order_parameters(params, ticker_data)
        
        # Create order
        if signal == 'Long':
            order = self._create_buy_order(action, ticker_data, order_type, order_params)
        else:
            order = self._create_sell_order(action, ticker_data, order_type, order_params)
        
        # Record execution
        if order:
            self.executed_actions.append({
                'name': action.name,
                'signal': signal,
                'orderType': order_type,
                'date': self.datas[0].datetime.date(0).isoformat(),
            })
        
        return order
    
    def _create_buy_order(
        self,
        action: TriggerAction,
        ticker_data: bt.AbstractDataBase,
        order_type: str,
        order_params: Dict[str, Any]
    ) -> Optional[bt.Order]:
        """Create a buy order."""
        if order_type == 'Market':
            return self.buy(data=ticker_data, **order_params)
        elif order_type == 'Limit':
            return self.buy(data=ticker_data, exectype=bt.Order.Limit, **order_params)
        elif order_type == 'StopLimit':
            return self.buy(data=ticker_data, exectype=bt.Order.StopLimit, **order_params)
        elif order_type == 'StopTrail':
            return self.buy(data=ticker_data, exectype=bt.Order.StopTrail, **order_params)
        elif order_type == 'StopTrailLimit':
            return self.buy(data=ticker_data, exectype=bt.Order.StopTrailLimit, **order_params)
        else:
            raise OrderExecutionError(f"Unknown order type: {order_type}")
    
    def _create_sell_order(
        self,
        action: TriggerAction,
        ticker_data: bt.AbstractDataBase,
        order_type: str,
        order_params: Dict[str, Any]
    ) -> Optional[bt.Order]:
        """Create a sell order."""
        if order_type == 'Market':
            return self.sell(data=ticker_data, **order_params)
        elif order_type == 'Limit':
            return self.sell(data=ticker_data, exectype=bt.Order.Limit, **order_params)
        elif order_type == 'StopLimit':
            return self.sell(data=ticker_data, exectype=bt.Order.StopLimit, **order_params)
        elif order_type == 'StopTrail':
            return self.sell(data=ticker_data, exectype=bt.Order.StopTrail, **order_params)
        elif order_type == 'StopTrailLimit':
            return self.sell(data=ticker_data, exectype=bt.Order.StopTrailLimit, **order_params)
        else:
            raise OrderExecutionError(f"Unknown order type: {order_type}")
    
    def _build_order_parameters(
        self,
        params: Dict[str, Any],
        ticker_data: bt.AbstractDataBase
    ) -> Dict[str, Any]:
        """Build order parameters from action parameters."""
        order_params = {}
        
        # Price
        if 'price' in params:
            order_params['price'] = self.evaluate_expression(params['price'])
        
        # Size (use sizer by default)
        if 'size' in params:
            order_params['size'] = int(params['size'])
        
        # Valid (days)
        if 'valid' in params:
            valid_days = int(params['valid'])
            order_params['valid'] = self.datas[0].datetime.date(0) + bt.TimeFrame.Days * valid_days
        
        # Stop/Trail parameters
        if 'trailpercent' in params:
            order_params['trailpercent'] = float(params['trailpercent'])
        if 'trailamount' in params:
            order_params['trailamount'] = float(params['trailamount'])
        if 'plimit' in params:
            order_params['plimit'] = self.evaluate_expression(params['plimit'])
        
        return order_params
    
    # ===== Helper Methods =====
    
    def _validate_action_parameters(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and set default action parameters."""
        if not isinstance(parameters, dict):
            raise OrderExecutionError("Action parameters must be a dictionary")
        
        params = parameters.copy()
        params.setdefault('ticker', 'default')
        params.setdefault('signal', 'Long')
        params.setdefault('orderType', 'Market')
        
        if params['signal'] not in ['Long', 'Short']:
            raise OrderExecutionError(f"Invalid signal: {params['signal']}")
        
        return params
    
    def _get_ticker_data(self, ticker: str) -> bt.AbstractDataBase:
        """Get data feed for the specified ticker."""
        if ticker in ('default', 'tickers[0]'):
            return self.datas[0]
        
        for data_feed in self.datas:
            if getattr(data_feed, '_name', None) == ticker:
                return data_feed
        
        raise OrderExecutionError(f"Ticker '{ticker}' not found in data feeds")
    
    def _track_order(self, trigger_name: str, action_name: str, order: bt.Order) -> None:
        """Track an order for a specific trigger and action."""
        if trigger_name not in self.trigger_orders:
            self.trigger_orders[trigger_name] = {}
        
        self.trigger_orders[trigger_name][action_name] = order
        self.logger.debug(f"Tracking order for trigger '{trigger_name}', action '{action_name}'")
    
    def _find_order_trigger(self, order: bt.Order) -> Optional[tuple[str, str]]:
        """Find which trigger and action an order belongs to."""
        for trigger_name, trigger_orders in self.trigger_orders.items():
            for action_name, tracked_order in trigger_orders.items():
                if tracked_order == order:
                    return trigger_name, action_name
        return None
    
    def _handle_completed_order(self, order: bt.Order) -> None:
        """Handle a completed order."""
        order_type = "BUY" if order.isbuy() else "SELL"
        self.logger.info(
            f"{order_type} EXECUTED - Price: {order.executed.price:.2f}, "
            f"Cost: {order.executed.value:.2f}, Commission: {order.executed.comm:.2f}"
        )
        
        trigger_info = self._find_order_trigger(order)
        if trigger_info:
            trigger_name, action_name = trigger_info
            self._process_next_action(trigger_name, action_name)
    
    def _handle_failed_order(self, order: bt.Order) -> None:
        """Handle a failed order."""
        self.logger.warning(f"Order FAILED - Status: {order.getstatusname()}")
        
        trigger_info = self._find_order_trigger(order)
        if trigger_info:
            trigger_name, _ = trigger_info
            self._cleanup_failed_trigger(trigger_name)
    
    def _process_next_action(self, trigger_name: str, completed_action: str) -> None:
        """Process the next action in a trigger sequence."""
        # Clear completed order
        if trigger_name in self.trigger_orders and completed_action in self.trigger_orders[trigger_name]:
            self.trigger_orders[trigger_name][completed_action] = None
        
        # Execute next pending action
        if trigger_name in self.pending_actions and self.pending_actions[trigger_name]:
            next_action_name = self.pending_actions[trigger_name].pop(0)
            trigger = self.trigger_system.triggers.get(trigger_name)
            if trigger:
                next_action = next((a for a in trigger.actions if a.name == next_action_name), None)
                if next_action:
                    self.execute_action(next_action, trigger_name=trigger_name)
        else:
            # All actions completed
            self.active_triggers.discard(trigger_name)
    
    def _cleanup_failed_trigger(self, trigger_name: str) -> None:
        """Clean up after a trigger fails."""
        self.pending_actions.pop(trigger_name, None)
        self.active_triggers.discard(trigger_name)
        
        if trigger_name in self.trigger_orders:
            for action_name in self.trigger_orders[trigger_name]:
                self.trigger_orders[trigger_name][action_name] = None
