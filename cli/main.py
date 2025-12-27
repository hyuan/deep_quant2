#!/usr/bin/env python
"""Main CLI entry point for My Quant V2 backtest system."""

import argparse
import logging
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple

import yaml

from core.backtest import run_backtest
from utils.config import load_runtime_config, load_strategy_def, setup_logging
from utils.parameters import map_cli_parameters_to_config
from utils.yf_utils import fetch_and_save_data


logger = logging.getLogger(__name__)


def parse_args() -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """
    Parse command line arguments and merge with config file.
    
    Returns:
        Tuple of (merged_config, dynamic_params)
    """
    parser = argparse.ArgumentParser(
        description='Run a Backtrader-based backtest',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    # Config file
    parser.add_argument(
        '--config',
        help='Path to YAML configuration file'
    )
    
    # Strategy selection
    parser.add_argument(
        '--strategy',
        help='Strategy name to run'
    )
    
    # Date range
    parser.add_argument(
        '--start-date',
        dest='start_date',
        help='Start date in YYYY-MM-DD format'
    )
    parser.add_argument(
        '--end-date',
        dest='end_date',
        help='End date in YYYY-MM-DD format'
    )
    
    # Tickers
    parser.add_argument(
        '--tickers',
        help='Comma-separated list of tickers to analyze'
    )
    
    # Sizer
    parser.add_argument(
        '--sizer-percent',
        type=int,
        dest='sizer_percent',
        help='Percentage of cash to use for each trade (default: 95)'
    )
    
    # Optimization
    parser.add_argument(
        '--optimize',
        help='Comma-separated list of parameters to optimize'
    )
    
    # Analysis and output
    parser.add_argument(
        '--analysis',
        action='store_true',
        help='Enable analysis of backtest results'
    )
    
    parser.add_argument(
        '--plot',
        action='store_true',
        help='Generate plots'
    )
    
    parser.add_argument(
        '--json-output',
        action='store_true',
        dest='json_output',
        help='Save results to JSON file'
    )
    
    parser.add_argument(
        '--initial-cash',
        type=float,
        dest='initial_cash',
        help='Initial cash amount (default: 100000.0)'
    )
    
    # Parse known args and collect unknowns for dynamic parameters
    args, unknown = parser.parse_known_args()
    
    # Load config file
    config = {}
    if args.config:
        try:
            config = load_runtime_config(args.config)
            logger.info(f"Loaded config from: {args.config}")
        except FileNotFoundError:
            logger.error(f"Config file not found: {args.config}")
            sys.exit(1)
        except Exception as e:
            logger.error(f"Error loading config: {e}")
            sys.exit(1)
    
    # Override with CLI arguments (CLI takes precedence)
    if args.strategy:
        config['strategy'] = args.strategy
    if args.start_date:
        config['start_date'] = args.start_date
    if args.end_date:
        config['end_date'] = args.end_date
    if args.tickers:
        config['tickers'] = args.tickers
    if args.sizer_percent is not None:
        config['sizer'] = {'PercentSizerInt': {'percents': args.sizer_percent}}
    if args.optimize:
        config['optimizing_params'] = args.optimize.split(',')
    if args.analysis:
        config['analysis'] = True
    if args.plot:
        config['plot'] = {'enabled': True}
    if args.json_output:
        config['json_output'] = True
    if args.initial_cash is not None:
        config['initial_cash'] = args.initial_cash
    
    # Validate required fields
    required_fields = ['strategy', 'start_date', 'end_date', 'tickers']
    missing = [f for f in required_fields if f not in config]
    if missing:
        logger.error(f"Required fields missing: {', '.join(missing)}")
        print(f"Error: Required fields missing: {', '.join(missing)}")
        print("Provide via config file or command line arguments")
        sys.exit(1)
    
    # Parse dynamic parameters (--indicator.param=value format)
    dynamic_params = {}
    for arg in unknown:
        if arg.startswith('--'):
            parts = arg[2:].split('=', 1)
            if len(parts) == 2:
                key, value = parts
                dynamic_params[key] = value
                logger.debug(f"Dynamic parameter: {key}={value}")
    
    return config, dynamic_params


def main() -> None:
    """Main entry point for the backtest application."""
    setup_logging()
    logger.info("=== My Quant V2 Backtest System ===")
    
    try:
        # Parse arguments
        config, dynamic_params = parse_args()
        
        # Load strategy definition
        strategy_name = config['strategy']
        logger.info(f"Loading strategy: {strategy_name}")
        strategy_def = load_strategy_def(strategy_name)
        
        # Apply dynamic parameters to strategy definition
        if dynamic_params:
            logger.info(f"Applying {len(dynamic_params)} dynamic parameters")
            strategy_def = map_cli_parameters_to_config(strategy_def, dynamic_params)
        
        # Prepare tickers
        tickers_str = config['tickers']
        tickers = [t.strip() for t in tickers_str.split(',')] if isinstance(tickers_str, str) else tickers_str
        logger.info(f"Tickers: {', '.join(tickers)}")
        
        # Fetch data
        logger.info("Fetching market data...")
        data_files = []
        for ticker in tickers:
            try:
                data_file = fetch_and_save_data(
                    ticker,
                    config['start_date'],
                    config['end_date'],
                    'datas/temp'
                )
                data_files.append(data_file)
                logger.info(f"  {ticker}: {data_file}")
            except Exception as e:
                logger.error(f"Failed to fetch data for {ticker}: {e}")
                sys.exit(1)
        
        # Prepare backtest parameters
        initial_cash = config.get('initial_cash', 100000.0)
        plot_enabled = config.get('plot', {}).get('enabled', False)
        analysis_enabled = config.get('analysis', False)
        json_output = config.get('json_output', False)
        
        logger.info(f"Initial cash: ${initial_cash:,.2f}")
        logger.info(f"Date range: {config['start_date']} to {config['end_date']}")
        
        # Run backtest
        logger.info("Running backtest...")
        result = run_backtest(
            strategy_name=strategy_name,
            strategy_def=strategy_def,
            data_files=data_files,
            config=config,
            initial_cash=initial_cash,
            plot=plot_enabled,
            analysis=analysis_enabled,
            json_output=json_output
        )
        
        # Display results
        logger.info("=" * 60)
        logger.info("BACKTEST RESULTS")
        logger.info("=" * 60)
        logger.info(f"Initial Value: ${result['initial_value']:,.2f}")
        logger.info(f"Final Value:   ${result['final_value']:,.2f}")
        logger.info(f"Profit:        ${result['profit']:,.2f}")
        logger.info(f"Return:        {result['profit_percent']:.2f}%")
        logger.info("=" * 60)
        
        # Display optimization results if applicable
        if 'best_optimization' in result:
            best = result['best_optimization']
            logger.info("\nBest Optimization Result:")
            logger.info(f"  Parameter: {best['param']}")
            logger.info(f"  Value: {best['value']}")
            logger.info(f"  Portfolio Value: ${best['portfolio']:,.2f}")
        
        logger.info("\nBacktest completed successfully!")
        
    except KeyboardInterrupt:
        logger.info("\nBacktest interrupted by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Backtest failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
