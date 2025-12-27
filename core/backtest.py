"""Core backtest engine with Cerebro orchestration and analysis."""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

import backtrader as bt

from utils.bt_utils import find_strategy_class
from utils.config import setup_sizer
from utils.analysis_utils import format_analyzer_results


logger = logging.getLogger(__name__)


# ===== Custom Analyzer =====

class ResultCollector(bt.Analyzer):
    """Collects optimization results for each parameter combination."""
    
    def __init__(self):
        super(ResultCollector, self).__init__()
        self.results = {}
    
    def start(self) -> None:
        pass
    
    def next(self):
        pass
    
    def stop(self) -> None:
        self.results = {
            'param': getattr(self.strategy.p, 'optimizing_param', None),
            'value': getattr(
                self.strategy.p,
                self.strategy.p.optimizing_param,
                None
            ) if self.strategy.p.optimizing_param else None,
            'portfolio': self.strategy.broker.getvalue()
        }
    
    def get_analysis(self):
        """Return collected results."""
        return dict(optresult=self.results)


# ===== Main Backtest Function =====

def run_backtest(
    strategy_name: str,
    strategy_def: Dict[str, Any],
    data_files: List[str],
    config: Dict[str, Any],
    initial_cash: float = 100000.0,
    plot: bool = False,
    analysis: bool = False,
    json_output: bool = False,
) -> Dict[str, Any]:
    """
    Run a backtest with the given parameters.
    
    Args:
        strategy_name: Name of the strategy to run
        strategy_def: Strategy definition (for YAML-based strategies)
        data_files: List of CSV data file paths
        config: Backtest configuration including strategy_parameters, sizer, etc.
        initial_cash: Initial cash value
        plot: Whether to generate plots
        analysis: Whether to run analyzers
        json_output: Whether to save results to JSON
        
    Returns:
        Dictionary containing backtest results
    """
    # Create Cerebro engine
    # For optimization with dynamically created strategies, disable multiprocessing
    cerebro = bt.Cerebro(maxcpus=1)
    
    # Resolve strategy class
    strategy_class = _resolve_strategy_class(strategy_name, strategy_def)
    
    # Get strategy parameters
    strategy_parameters = config.get('strategy_parameters', {})
    
    # Check for optimization
    optimizing_params = config.get('optimizing_params', [])
    is_optimizing = bool(optimizing_params)
    
    # Add strategy (normal or optimization mode)
    if is_optimizing:
        logger.info("Starting optimization mode")
        optimizing_param = optimizing_params[0]  # Take first param for now
        
        # Extract the parameter value from strategy_parameters
        # In optimization mode, this should be a list of values to try
        param_values = strategy_parameters.get(optimizing_param)
        if not isinstance(param_values, list):
            raise ValueError(f"Optimization parameter '{optimizing_param}' must be a list of values")
        
        # Pass the parameter values to optstrategy
        # The parameter name as keyword argument with list of values
        strategy_idx = cerebro.optstrategy(
            strategy_class,
            optimizing=True,
            optimizing_param=optimizing_param,
            **{optimizing_param: param_values}
        )
    else:
        logger.info("Starting backtest mode")
        # Don't pass strategy_parameters - they're already baked into the strategy class
        strategy_idx = cerebro.addstrategy(strategy_class)
    
    # Setup sizer
    _setup_sizer(cerebro, config, strategy_idx)
    
    # Add data feeds
    for data_file in data_files:
        data = bt.feeds.YahooFinanceCSVData(dataname=data_file)
        cerebro.adddata(data)
    
    # Set initial cash
    cerebro.broker.setcash(initial_cash)
    
    # Add analyzers
    if analysis:
        _add_analyzers(cerebro)
    
    # Log initial value
    initial_value = cerebro.broker.getvalue()
    logger.info(f'Starting Portfolio Value: {initial_value:.2f}')
    
    # Run backtest
    results = cerebro.run()
    
    # Log final value
    final_value = cerebro.broker.getvalue()
    logger.info(f'Ending Portfolio Value: {final_value:.2f}')
    
    # Process results
    result_dict = _process_results(
        results,
        initial_value,
        final_value,
        analysis,
        is_optimizing
    )
    
    # Save JSON output if requested
    if json_output and not is_optimizing:
        _save_json_output(strategy_name, config, result_dict)
    
    # Plot if requested
    if plot and not is_optimizing:
        cerebro.plot()
    
    return result_dict


# ===== Helper Functions =====

def _resolve_strategy_class(strategy_name: str, strategy_def: Dict[str, Any]) -> type:
    """
    Resolve the strategy class by name or create from definition.
    
    Args:
        strategy_name: Name of the strategy
        strategy_def: Strategy definition for factory creation
        
    Returns:
        Strategy class
        
    Raises:
        ValueError: If strategy cannot be resolved
    """
    # Try to find pre-implemented strategy
    strategy_class = find_strategy_class(strategy_name)
    
    # If not found and we have a definition, create from YAML
    if not strategy_class and strategy_def:
        logger.info(f"Creating strategy '{strategy_name}' from YAML definition")
        from strategy.factory import create_strategy
        strategy_class = create_strategy(strategy_name, strategy_def)
    
    if not strategy_class:
        raise ValueError(f"Strategy '{strategy_name}' not found and no definition provided")
    
    logger.info(f"Using strategy class: {strategy_class.__name__}")
    return strategy_class


def _setup_sizer(cerebro: bt.Cerebro, config: Dict[str, Any], strategy_idx: int) -> None:
    """Setup position sizer based on configuration."""
    sizer_config = config.get('sizer', {})
    sizer_type, sizer_params = setup_sizer(sizer_config)
    
    if sizer_type:
        cerebro.addsizer_byidx(strategy_idx, sizer_type, **sizer_params)
    else:
        # Fallback to default
        cerebro.addsizer_byidx(strategy_idx, bt.sizers.PercentSizerInt, percents=95)


def _add_analyzers(cerebro: bt.Cerebro) -> None:
    """Add standard analyzers to Cerebro."""
    cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name='sharpe')
    cerebro.addanalyzer(bt.analyzers.DrawDown, _name='drawdown')
    cerebro.addanalyzer(bt.analyzers.SQN, _name='sqn')
    cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name='trades')
    cerebro.addanalyzer(bt.analyzers.Transactions, _name='transactions')
    cerebro.addanalyzer(ResultCollector, _name='collector')


def _process_results(
    results: List,
    initial_value: float,
    final_value: float,
    analysis: bool,
    is_optimizing: bool
) -> Dict[str, Any]:
    """Process backtest results and extract analysis."""
    result_dict = {
        'results': results,
        'initial_value': initial_value,
        'final_value': final_value,
        'profit': final_value - initial_value,
        'profit_percent': ((final_value - initial_value) / initial_value) * 100
    }
    
    # Add analysis results if enabled
    if analysis and results and not is_optimizing:
        strat = results[0]
        
        # Collect analyzer results
        analyzers = {}
        if hasattr(strat, 'analyzers'):
            if hasattr(strat.analyzers, 'sharpe'):
                analyzers['sharpe'] = strat.analyzers.sharpe.get_analysis()
            if hasattr(strat.analyzers, 'drawdown'):
                analyzers['drawdown'] = strat.analyzers.drawdown.get_analysis()
            if hasattr(strat.analyzers, 'sqn'):
                analyzers['sqn'] = strat.analyzers.sqn.get_analysis()
            if hasattr(strat.analyzers, 'trades'):
                analyzers['trades'] = strat.analyzers.trades.get_analysis()
        
        result_dict['analyzers'] = analyzers
        
        # Log formatted analysis
        logger.info(format_analyzer_results(analyzers))
    
    # Process optimization results
    if is_optimizing and results:
        opt_results = []
        for strat in results:
            if hasattr(strat, 'analyzers') and hasattr(strat.analyzers, 'collector'):
                opt_results.append(strat.analyzers.collector.get_analysis()['optresult'])
        
        if opt_results:
            result_dict['optimization_results'] = opt_results
            # Find best result
            best_result = max(opt_results, key=lambda x: x['portfolio'])
            logger.info(
                f"Best result: {best_result['param']}={best_result['value']}, "
                f"Portfolio={best_result['portfolio']:.2f}"
            )
            result_dict['best_optimization'] = best_result
    
    return result_dict


def _save_json_output(
    strategy_name: str,
    config: Dict[str, Any],
    result_dict: Dict[str, Any]
) -> None:
    """Save backtest results to JSON file."""
    try:
        output_dir = Path('output/json')
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Build output data
        output_data = {
            'strategy': strategy_name,
            'ticker': config.get('tickers', 'unknown'),
            'start_date': config.get('start_date'),
            'end_date': config.get('end_date'),
            'initial_cash': result_dict['initial_value'],
            'final_value': result_dict['final_value'],
            'return_pct': result_dict['profit_percent'],
        }
        
        # Add analyzer results if available
        if 'analyzers' in result_dict:
            analyzers = result_dict['analyzers']
            output_data.update({
                'sharpe_ratio': analyzers.get('sharpe', {}).get('sharperatio'),
                'max_drawdown': analyzers.get('drawdown', {}).get('max', {}).get('drawdown'),
                'sqn': analyzers.get('sqn', {}).get('sqn'),
                'trades': analyzers.get('trades', {}).get('total', {}).get('closed', 0),
            })
        
        # Generate filename
        ticker = config.get('tickers', 'unknown')
        filename = output_dir / f'{strategy_name}_{ticker}_results.json'
        
        # Save to file
        with open(filename, 'w') as f:
            json.dump(output_data, f, indent=2)
        
        logger.info(f'Results saved to {filename}')
    except Exception as e:
        logger.error(f'Failed to save JSON output: {e}')
